# glyph states + per-frame global similarity for a text shot
import json,numpy as np,sys; sys.path.insert(0,'tools')
from glyphraster import parse
def compile_shot(key,gsfile,a,b,sw,fill_thr=0.9,line_thr=0.85,smooth=True):
    G=json.load(open('meas/text_trace.json'))[key]; d=json.load(open(gsfile)); tpl=d['tpl']
    C=[]
    for g in G:
        allp=np.concatenate(parse(g['d'])); C.append((allp.min(0)+allp.max(0))/2)
    C=np.array(C)
    frames={}; raw={}
    for f in range(a,b+1):
        r=d['frames'].get(str(f))
        if r is None: continue
        st=[];X=[];Y=[];sc=[]
        for i,(fi,li) in enumerate(r):
            s=0; W=None
            if fi[0]>fill_thr: s=2; W=fi
            elif li[0]>line_thr: s=1; W=li
            st.append(s)
            if W is not None and len(W)==7:
                M=np.array(W[1:]).reshape(2,3); x0,y0=tpl[i]
                X.append(C[i]); Y.append(M[:,:2]@(C[i]-[x0,y0])+M[:,2]); sc.append(np.sqrt(abs(np.linalg.det(M[:,:2]))))
        if len(X)>=2:
            X=np.array(X);Y=np.array(Y); A=np.zeros((2*len(X),3)); A[0::2,0]=X[:,0];A[0::2,1]=1;A[1::2,0]=X[:,1];A[1::2,2]=1
            p=np.linalg.lstsq(A,Y.ravel(),rcond=None)[0]
        elif len(X)==1:
            s_=sc[0]; p=[s_,Y[0][0]-s_*X[0][0],Y[0][1]-s_*X[0][1]]
        else: p=None
        frames[f]={'st':st}; raw[f]=p
    fs=sorted(f for f in raw if raw[f] is not None)
    P=np.array([raw[f] for f in fs])
    allf=np.arange(a,b+1)
    T=np.stack([np.interp(allf,fs,P[:,j]) for j in range(3)],1)
    # linear extrapolation before first measured frame
    if len(fs)>2 and fs[0]>a:
        k0=fs[0]-a; v=P[1]-P[0]
        for k in range(k0): T[k]=P[0]-v*(k0-k)
    import os
    if os.path.exists('meas/pose_override.json'):
        for f_,v in json.load(open('meas/pose_override.json')).get(key,{}).items():
            if a<=int(f_)<=b: T[int(f_)-a]=v
    out={'a':a,'b':b,'sw':sw,'frames':[]}
    for k,f in enumerate(allf):
        fr=frames.get(int(f),{'st':[0]*len(G)})
        out['frames'].append({'T':np.round(T[k],5).tolist(),'st':fr['st']})
    return out,fs,P
if __name__=='__main__':
    o,fs,P=compile_shot('big','meas/gs_big.json',301,370,3.3)
    for f,p in zip(fs,P): print(f,np.round(p,4))
