# Per-frame dot detection. Chroma (UV) unmixing -> alpha (area-preserving under 4:2:0 chroma blur),
# then k-disc least squares with a blurred union-of-discs model.
import cv2,numpy as np,json,sys
from scipy.optimize import least_squares
DOTC={'orange':(242,106,32),'blue':(9,107,247),'green':(17,208,78),'purple':(140,58,239)}
BGS={'orange':[(0,0,0),(255,255,255)],'blue':[(0,0,0),(17,208,78),(255,255,255)],'green':[(0,0,0),(140,58,239)],'purple':[(0,0,0)]}
M=np.array([[-0.168736,-0.331264,0.5],[0.5,-0.418688,-0.081312]],np.float32)
def uv(x): return np.asarray(x,np.float32)@M.T
def alpha(im,n):
    U=uv(im); c=uv(DOTC[n]); best=None; bres=None
    for b in BGS[n]:
        b=uv(b); d=c-b; a=((U-b)@d)/(d@d); r=np.linalg.norm(U-(b+a[...,None]*d),axis=2)
        if best is None: best,bres=a,r
        else: m=r<bres; best=np.where(m,a,best); bres=np.where(m,r,bres)
    best=np.clip(best,0,1.2); best[bres>25]=0
    return best
SIG=0.9
def model(p,xs,ys):
    k=len(p)//3; u=np.zeros(xs.shape,np.float32)
    for i in range(k):
        x,y,r=p[3*i:3*i+3]; u=np.maximum(u,np.clip(r-np.hypot(xs-x,ys-y)+0.5,0,1))
    return cv2.GaussianBlur(u,(0,0),SIG)
def fit_comp(a,x0,y0,rtyp=None):
    ys,xs=(np.mgrid[:a.shape[0],:a.shape[1]]+0.5).astype(np.float32)
    area=a.sum(); cx,cy=(a*xs).sum()/area,(a*ys).sum()/area; r1=np.sqrt(area/np.pi)
    res1=np.sqrt(np.mean((model([cx,cy,r1],xs,ys)-a)**2))
    if res1<0.09: return [[cx+x0,cy+y0,r1]],res1,1
    best=None
    n=a.size
    bin_=(a>0.5).astype(np.uint8); dt=cv2.distanceTransform(np.pad(bin_,1),cv2.DIST_L2,5)[1:-1,1:-1]
    mx=(dt==cv2.dilate(dt,np.ones((3,3))))&(dt>1.0)
    pk=np.c_[xs[mx],ys[mx],dt[mx]]; pk=pk[np.argsort(-pk[:,2])]
    pts=np.c_[xs[a>0.4],ys[a>0.4]].astype(np.float32)
    kmax=int(min(10,max(1,area/(np.pi*2.0**2))))
    for k in range(1,kmax+1):
        inits=[]
        if k==1: inits.append(np.array([[cx,cy]]))
        else:
            if len(pts)>=k:
                _,_,cen=cv2.kmeans(pts,k,None,(3,50,0.01),4,cv2.KMEANS_PP_CENTERS); inits.append(cen)
            if len(pk)>=k: inits.append(pk[:k,:2])
        for cen in inits:
            r0=np.sqrt(area/k/np.pi); p0=np.concatenate([[c[0],c[1],r0] for c in cen])
            lo=[];hi=[]
            for c in cen: lo+=[-3,-3,0.5]; hi+=[a.shape[1]+3,a.shape[0]+3,80]
            p0=np.clip(p0,np.array(lo)+1e-3,np.array(hi)-1e-3)
            r=least_squares(lambda p:(model(p,xs,ys)-a).ravel(),p0,bounds=(lo,hi),diff_step=1e-3,max_nfev=300)
            res=np.sqrt(np.mean(r.fun**2)); bic=n*np.log(max(res**2,1e-6))+3*k*np.log(n)*2
            if best is None or bic<best[0]: best=(bic,r.x,res,k)
        if best[2]<0.085: break
        if k>=best[3]+3: break
    if best is None: return [[cx+x0,cy+y0,r1]],res1,1
    p=best[1]
    return [[p[3*i]+x0,p[3*i+1]+y0,p[3*i+2]] for i in range(best[3])],best[2],best[3]
def measure(f,colors=None):
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
    res={}
    for n in (colors or DOTC):
        a=alpha(im,n); m=(a>0.3).astype(np.uint8)
        nl,l,st,ce=cv2.connectedComponentsWithStats(m); L=[]
        for i in range(1,nl):
            bx,by,bw,bh,ar=st[i]
            if ar<3 or ar>30000: continue
            pad=3; x0,y0=max(0,bx-pad),max(0,by-pad); x1,y1=min(1920,bx+bw+pad),min(1080,by+bh+pad)
            sub=np.clip(a[y0:y1,x0:x1],0,1)*(cv2.dilate((l[y0:y1,x0:x1]==i).astype(np.uint8),np.ones((5,5)))>0)
            d,err,k=fit_comp(sub,x0,y0)
            for q in d: L.append([round(float(q[0]),3),round(float(q[1]),3),round(float(q[2]),3),round(float(err),3),k])
        res[n]=L
    return res
if __name__=='__main__':
    a,b=int(sys.argv[1]),int(sys.argv[2]); R={}
    for f in range(a,b):
        R[f]=measure(f)
        if f%10==0: json.dump(R,open(sys.argv[3],'w'))
    json.dump(R,open(sys.argv[3],'w'))
