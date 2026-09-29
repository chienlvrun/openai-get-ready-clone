# Per-frame sub-pixel circle measurement for coloured discs (phase A).
import cv2,numpy as np,json,sys
from skimage.measure import find_contours
COL={'white':(223,223,223),'purple':(140,58,239),'orange':(242,106,32),'green':(17,208,78),'dark':(38,38,38),'blue':(9,107,247)}
H,W=1080,1920
def alpha_map(im,c):
    c=np.array(c,np.float32); im=im.astype(np.float32)
    # projection onto segment black->c
    a=(im@c)/(c@c); resid=np.linalg.norm(im-a[...,None]*c,axis=2)
    a=np.clip(a,0,1); a[resid>40]=0
    return a
def kasa(p):
    x,y=p[:,0],p[:,1]; A=np.c_[2*x,2*y,np.ones(len(x))]; b=x*x+y*y
    s=np.linalg.lstsq(A,b,rcond=None)[0]; r=np.sqrt(s[2]+s[0]**2+s[1]**2); return s[0],s[1],r
def fit(pts):
    rng=np.random.default_rng(0); best=(-1,None)
    n=len(pts)
    for _ in range(300):
        idx=rng.choice(n,3,replace=False)
        try: c=kasa(pts[idx])
        except Exception: continue
        if not np.isfinite(c[2]): continue
        d=np.abs(np.hypot(pts[:,0]-c[0],pts[:,1]-c[1])-c[2]); k=(d<1.0).sum()
        if k>best[0]: best=(k,c)
    c=best[1]
    for it in range(4):
        d=np.abs(np.hypot(pts[:,0]-c[0],pts[:,1]-c[1])-c[2]); keep=d<0.8
        c=kasa(pts[keep])
    d=np.abs(np.hypot(pts[:,0]-c[0],pts[:,1]-c[1])-c[2]); return c,float(np.median(d[keep])),int(keep.sum())
def measure(f):
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1]
    out={}
    for n,c in COL.items():
        a=alpha_map(im,c)
        if n=='dark':  # dark disc: alpha tiny; use direct distance
            a=np.clip(1-np.linalg.norm(im.astype(np.float32)-np.array(c,np.float32),axis=2)/38,0,1)
            a[im.max(2)>60]=0
        m=(a>0.5).astype(np.uint8)
        m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        nl,lab,st,cen=cv2.connectedComponentsWithStats(m)
        res=[]
        for i in range(1,nl):
            if st[i,4]<20: continue
            x0,y0,w,h=st[i,:4]
            pad=3; xa,ya=max(0,x0-pad),max(0,y0-pad); xb,yb=min(W,x0+w+pad),min(H,y0+h+pad)
            sub=a[ya:yb,xa:xb].copy(); sub[lab[ya:yb,xa:xb]!=i]*= (sub[lab[ya:yb,xa:xb]!=i]>0.02)  # keep AA
            # fill holes (eyes) so inner contours don't count
            comp=(lab[ya:yb,xa:xb]==i)
            from scipy.ndimage import binary_fill_holes
            holes=binary_fill_holes(comp)&~comp
            holes=cv2.dilate(holes.astype(np.uint8),np.ones((5,5),np.uint8))>0
            sub[holes]=1.0
            cs=find_contours(np.pad(sub,1),0.5)
            pts=[]
            for cc in cs:
                cc=cc-1
                pts.append(cc[:,::-1]+[xa,ya])
            if not pts: continue
            pts=np.concatenate(pts)
            # drop frame border points
            ok=(pts[:,0]>1)&(pts[:,0]<W-2)&(pts[:,1]>1)&(pts[:,1]<H-2)
            pts=pts[ok]
            if len(pts)<8: continue
            (cx,cy,r),err,nk=fit(pts)
            res.append([round(float(cx),3),round(float(cy),3),round(float(r),3),round(err,3),int(st[i,4]),nk,len(pts)])
        out[n]=res
    return out
if __name__=='__main__':
    a,b=int(sys.argv[1]),int(sys.argv[2])
    R={f:measure(f) for f in range(a,b)}
    json.dump(R,open(sys.argv[3],'w'))
