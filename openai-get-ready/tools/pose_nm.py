# per-frame pose refinement by direct model fitting (Nelder-Mead on s,tx,ty) over all active glyphs
import sys,json,cv2,numpy as np; sys.path.insert(0,'tools')
from glyphraster import parse,raster
from glyphstate import cover,outline_raster
from compile_text import compile_shot
from scipy.optimize import minimize
key,gs,stf,a,b,sw,f0,f1,out=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]),float(sys.argv[6]),int(sys.argv[7]),int(sys.argv[8]),sys.argv[9]
o,_,_=compile_shot(key,gs,a,b,sw); S=json.load(open(stf))['st']
G=json.load(open('meas/text_trace.json'))[key]; P=[parse(g['d']) for g in G]
R={}
for f in range(f0,f1):
    st=S[str(f)]; act=[i for i,v in enumerate(st) if v]
    if not act: continue
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
    U=cv2.cvtColor(im.astype(np.uint8),cv2.COLOR_RGB2YCrCb).astype(np.float32)
    chroma=np.hypot(U[:,:,1]-128,U[:,:,2]-128)
    covs={c:cover(im,c) for c in ('white','green','purple')}
    s0,tx0,ty0=o['frames'][f-a]['T']
    boxes=[]
    for i in act:
        Q=[q*s0+[tx0,ty0] for q in P[i]]; allp=np.concatenate(Q)
        x0,y0=np.floor(allp.min(0)).astype(int)-8; x1,y1=np.ceil(allp.max(0)).astype(int)+8
        x0,y0=max(0,x0),max(0,y0); x1,y1=min(1920,x1),min(1080,y1)
        c=G[i]['color']; obs=covs[c][y0:y1,x0:x1]
        dm=(cv2.erode((chroma[y0:y1,x0:x1]<25).astype(np.uint8),np.ones((5,5)))>0) if c=='white' else np.ones(obs.shape,bool)
        boxes.append((i,x0,y0,x1,y1,obs,dm))
    def err(p):
        s,tx,ty=p; e=0;n=0
        for i,x0,y0,x1,y1,obs,dm in boxes:
            L=[q*s+[tx-x0,ty-y0] for q in P[i]]
            if st[i]==2: m=raster([L],x1-x0,y1-y0,ss=4)
            else:
                lw=sw if G[i]['color']=='white' else 1.0
                m=st[i]*outline_raster(L,x1-x0,y1-y0,lw,ss=4)
            d=(obs-m)[dm]; e+=np.sum(d*d); n+=d.size
        return e/max(n,1)
    x0=np.array([s0,tx0,ty0])
    r=minimize(err,x0,method='Nelder-Mead',options={'xatol':0.003,'fatol':1e-7,'maxiter':200,'initial_simplex':np.array([x0,x0+[0.004,0,0],x0+[0,1.5,0],x0+[0,0,1.5]])})
    R[f]=[float(v) for v in r.x]+[float(err(x0)),float(r.fun)]
    print(f,np.round(r.x,4),round(err(x0),5),round(r.fun,5),flush=True)
    json.dump(R,open(out,'w'))
