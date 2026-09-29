# Export measured tables -> project/data/*.js
import json,numpy as np,os
OUT='project/data'
def w(name,var,obj): open(f'{OUT}/{name}.js','w').write(f'window.{var}='+json.dumps(obj,separators=(',',':'))+';')
# eye templates (normalised by sqrt(area) exactly as in tools/eyes.py)
T=json.load(open('meas/eye_templates.json'))
w('eye_templates','EYE_TPL',{k:[(np.array(p)/np.sqrt(v['area'])).round(5).tolist() for p in v['polys']] for k,v in T.items()})
# discs
D=json.load(open('meas/discs.json')); w('circles','DISCS',{int(k):v for k,v in D.items()})
# eyes
E={}
for fn in ['meas/eyes2_a.json','meas/eyes2_b.json']:
    if os.path.exists(fn):
        for f,L in json.load(open(fn)).items():
            E[int(f)]={c['c']:[[e['g']]+np.array(e['A']).T.ravel().round(4).tolist() for e in c['eyes'] if e['cc']>0.9] for c in L}
w('eyes','EYES',E)
# ---- dots
import glob
from scipy.ndimage import gaussian_filter1d
CI={'orange':0,'blue':1,'green':2,'purple':3,'white':4}
DOTS={}
for fn in ['meas/dots_b.json','meas/dots_c.json','meas/dots_d1.json','meas/dots_d2.json','meas/dots_d3.json','meas/dots_e.json','meas/dots_w.json']:
    if not os.path.exists(fn): continue
    for f,res in json.load(open(fn)).items():
        f=int(f); L=DOTS.setdefault(f,[])
        for n,lst in res.items():
            for x,y,r,err,k in lst:
                if n=='purple' and str(f) in D and any(c[0]=='purple' and np.hypot(c[1]-x,c[2]-y)<c[3]+2 for c in D[str(f)]): continue
                if r<0.8: continue
                L.append([CI[n],round(x,2),round(y,2),round(r,2)])
for fn in sorted(glob.glob('meas/dots_*_fix_*.json')):
    for f,res in json.load(open(fn)).items():
        f=int(f); cols={CI[n] for n in res}; L=[d for d in DOTS.get(f,[]) if d[0] not in cols]
        for n,lst in res.items():
            for x,y,r,err,k in lst:
                if n=='purple' and str(f) in D and any(c[0]=='purple' and np.hypot(c[1]-x,c[2]-y)<c[3]+2 for c in D[str(f)]): continue
                if r<0.8: continue
                L.append([CI[n],round(x,2),round(y,2),round(r,2)])
        DOTS[f]=L
w('dots','DOTS',DOTS)
# ---- text shots
import sys; sys.path.insert(0,'tools')
from compile_text import compile_shot
TS={}
PO=json.load(open('meas/pose_override.json'))
def smooth_T(o,sig,upto=None,key=None,rawfirst=0):
    for f,v in PO.get(key,{}).items(): o['frames'][int(f)-o['a']]['T']=v
    T=np.array([fr['T'] for fr in o['frames']])
    Ts=np.stack([gaussian_filter1d(T[:,j],sig,mode='nearest') for j in range(3)],1)
    if upto is not None:
        k=upto-o['a']; Ts[k:]=T[k:]
    if rawfirst: Ts[:rawfirst]=T[:rawfirst]
    for fr,t in zip(o['frames'],Ts): fr['T']=np.round(t,5).tolist()
if os.path.exists('meas/gs_big.json'):
    o,_,_=compile_shot('big','meas/gs_big.json',301,370,3.3); smooth_T(o,4); TS['big']=o
if os.path.exists('meas/gs_t1.json'):
    o,_,_=compile_shot('t1','meas/gs_t1.json',371,490,2.1); TS['t1']=o
if os.path.exists('meas/gs_t2.json'):
    o,_,_=compile_shot('t2','meas/gs_t2.json',491,725,1.6); smooth_T(o,1.0,key='t2',rawfirst=12); o['lineW']={'white':1.6,'green':1.0,'purple':1.0}; o['lineA']={'green':0.62,'purple':0.62}; TS['t2']=o
for key in list(TS):
    fn='meas/st_%s.json'%key
    if os.path.exists(fn):
        S=json.load(open(fn))['st']; o=TS[key]
        for k,fr in enumerate(o['frames']):
            f=o['a']+k
            if str(f) in S: fr['st']=[(1.0 if (0<v<=1 and v>0.75) else v) for v in S[str(f)]]
if 't2' in TS:
    BS=json.load(open('meas/bracket_slide.json')); o=TS['t2']
    for f in range(491,519): o['frames'][f-491]['st'][17]=0
    for f in range(519,524):
        fr=o['frames'][f-491]; fr['st'][17]=1.0; fr['off']={'17':BS[str(f)][:2]}
w('textstate','TSTATE',TS)
