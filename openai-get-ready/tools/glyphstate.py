# Per-frame, per-glyph: ECC pose fit with fill template AND outline template -> state + pose
import sys,json,cv2,numpy as np; sys.path.insert(0,'tools')
from glyphraster import *
COL={'white':(255,255,255),'green':(17,208,78),'purple':(140,58,239)}
def cover(im,col):
    if col=='white': return np.clip(im.min(2)/255,0,1)
    c=np.array(COL[col],np.float32); a=np.clip((im@c)/(c@c),0,1)
    resid=np.linalg.norm(im-a[...,None]*c,axis=2); a[resid>70]=0; return a
def outline_raster(polys,W,H,w,ss=8):
    img=np.zeros((H*ss,W*ss),np.uint8)
    for p in polys:
        cv2.polylines(img,[(p*ss*16).round().astype(np.int32)],True,255,max(1,int(round(w*ss))),cv2.LINE_8,4)
    return cv2.resize(img,(W,H),interpolation=cv2.INTER_AREA).astype(np.float32)/255
def run(key,frames,out,sw,YO=330,YH=420):
    J=json.load(open('meas/text_trace.json'))
    G=J[key]
    tpl=[]
    for g in G:
        P=parse(g['d']); allp=np.concatenate(P); pad=10
        x0,y0=np.floor(allp.min(0)).astype(int)-pad; x1,y1=np.ceil(allp.max(0)).astype(int)+pad
        Pl=[p-[x0,y0] for p in P]
        tpl.append({'fill':raster([Pl],x1-x0,y1-y0,ss=8),'line':outline_raster(Pl,x1-x0,y1-y0,sw),'x0':x0,'y0':y0,'col':g['color']})
    R={}; prev={}
    for f in frames:
        im=cv2.imread('of/%05d.png'%(f+1))[YO:YO+YH,:,::-1].astype(np.float32)
        dots=(np.abs(im[:,:,0]-im[:,:,2])>60).astype(np.uint8)
        dm=(1-cv2.dilate(dots,np.ones((5,5)))).astype(np.uint8)
        covs={c:cover(im,c) for c in set(t['col'] for t in tpl)}
        res=[]
        for k,t in enumerate(tpl):
            a=covs[t['col']]; mask=dm if t['col']=='white' else np.ones_like(dm)
            row=[]
            for kind in ('fill','line'):
                W0=prev.get((k,kind))
                if W0 is None: W0=prev.get((k,'fill' if kind=='line' else 'line'))
                if W0 is None: W0=np.array([[1,0,t['x0']],[0,1,t['y0']]],np.float32)
                W0=W0.copy(); W0[1,2]-=YO
                try:
                    cc,Wm=cv2.findTransformECC(t[kind],a,W0,cv2.MOTION_AFFINE,(3,100,1e-6),mask,1)
                    Wm=Wm.copy(); Wm[1,2]+=YO
                except cv2.error: cc,Wm=-1,None
                if Wm is not None and cc>0.9: prev[(k,kind)]=Wm
                row.append([round(float(cc),4)]+(Wm.round(4).ravel().tolist() if Wm is not None else []))
            res.append(row)
        R[f]=res
    json.dump({'frames':R,'tpl':[[int(t['x0']),int(t['y0'])] for t in tpl]},open(out,'w'))
if __name__=='__main__':
    key=sys.argv[1]; a,b=int(sys.argv[2]),int(sys.argv[3]); sw=float(sys.argv[5])
    run(key,range(a,b,-1 if a>b else 1),sys.argv[4],sw)
