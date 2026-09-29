# per-glyph per-frame translation+scale tracking of filled glyphs (ECC, dots masked)
import sys,json,cv2,numpy as np; sys.path.insert(0,'tools')
from glyphraster import *
COL={'white':(255,255,255),'green':(17,208,78),'purple':(140,58,239)}
def cover(im,col):
    c=np.array(col,np.float32); a=np.clip((im@c)/(c@c),0,1)
    resid=np.linalg.norm(im-a[...,None]*c,axis=2); a[resid>70]=0; return a
def run(key,F0,frames,out):
    T=json.load(open('meas/text_trace.json'))[key]
    tpls=[]
    for g in T:
        P=parse(g['d']); x,y,w,h=g['bbox']; pad=8; x0,y0=x-pad,y-pad
        tpls.append((raster([[p-[x0,y0] for p in P]],w+2*pad,h+2*pad,ss=8),x0,y0,g['color']))
    R={}; prev=[None]*len(T)
    for f in frames:
        YO=400
        im=cv2.imread('of/%05d.png'%(f+1))[YO:700,:,::-1].astype(np.float32)
        dots=((np.abs(im[:,:,0]-im[:,:,2])>60)).astype(np.uint8)
        dm=(1-cv2.dilate(dots,np.ones((7,7)))).astype(np.uint8)
        covs={cn:(np.clip(im.min(2)/255,0,1) if cn=='white' else cover(im,COL[cn])) for cn in set(t[3] for t in tpls)}
        res=[]
        for k,(tpl,x0,y0,cn) in enumerate(tpls):
            a=covs[cn]
            mask=dm if cn=='white' else np.ones(a.shape,np.uint8)
            W=prev[k].copy() if prev[k] is not None else np.array([[1,0,x0],[0,1,y0]],np.float32)
            W[1,2]-=YO
            best=None
            for dx in ([0] if prev[k] is not None else [0,-20,20,-40,40,-60,60,-90,90]):
                Wi=W.copy(); Wi[0,2]+=dx
                try:
                    cc,Wm=cv2.findTransformECC(tpl,a,Wi,cv2.MOTION_AFFINE,(3,200,1e-6),mask,1)
                except cv2.error: continue
                if best is None or cc>best[0]: best=(cc,Wm)
                if cc>0.97: break
            if best is None: res.append(None); prev[k]=None; continue
            cc,Wm=best; Wm=Wm.copy(); Wm[1,2]+=YO
            prev[k]=Wm if cc>0.9 else prev[k]
            res.append([round(float(cc),4)]+Wm.round(4).ravel().tolist())
        R[f]=res
    json.dump(R,open(out,'w'))
if __name__=='__main__':
    key=sys.argv[1]; a,b=int(sys.argv[2]),int(sys.argv[3]); step=-1 if a>b else 1
    run(key,None,range(a,b,step),sys.argv[4])
