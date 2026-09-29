# Math reference helpers (skill §8)
import numpy as np
from scipy.optimize import least_squares, brentq
def rts(z, dt, q=1.0, r=1.0):
    F=np.array([[1,dt,dt*dt/2],[0,1,dt],[0,0,1]]); H=np.array([[1.,0,0]])
    G=np.array([[dt**3/6],[dt*dt/2],[dt]]); Q=q*(G@G.T); R=np.array([[r]])
    x=np.array([z[~np.isnan(z)][0],0,0.]); Pm=np.eye(3)*100; xs=[];Ps=[];xp=[];Pp=[]
    for k in range(len(z)):
        if k>0: x=F@x; Pm=F@Pm@F.T+Q
        xp.append(x.copy()); Pp.append(Pm.copy())
        if not np.isnan(z[k]):
            S=H@Pm@H.T+R; K=Pm@H.T@np.linalg.inv(S); x=x+(K@(z[k]-H@x)).ravel(); Pm=(np.eye(3)-K@H)@Pm
        xs.append(x.copy()); Ps.append(Pm.copy())
    xs=np.array(xs); out=xs.copy()
    for k in range(len(z)-2,-1,-1):
        C=Ps[k]@F.T@np.linalg.inv(Pp[k+1]); out[k]=xs[k]+C@(out[k+1]-xp[k+1])
    return out[:,0], out[:,1]
def bez(u,p1,p2): return 3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3
def ease(x,x1,y1,x2,y2):
    x=np.clip(np.asarray(x,float),0,1); out=np.empty_like(x)
    for i,xv in np.ndenumerate(x):
        out[i]=0 if xv<=0 else 1 if xv>=1 else bez(brentq(lambda u: bez(u,x1,x2)-xv,0,1),y1,y2)
    return out
def fit_ease(t,v,p0=None):
    p0=p0 or [t[0],t[-1],v[0],v[-1],.42,0,.58,1]
    f=lambda p: p[2]+(p[3]-p[2])*ease((t-p[0])/(p[1]-p[0]),*p[4:])-v
    lo=[-np.inf]*8; hi=[np.inf]*8; lo[4]=lo[6]=0; hi[4]=hi[6]=1
    r=least_squares(f,p0,bounds=(lo,hi)); return r.x, np.sqrt(np.mean(r.fun**2))
def basis(gx,gy,W,H,xs,ys,sig=0.75):
    cx=(np.arange(gx)+.5)*W/gx; cy=(np.arange(gy)+.5)*H/gy; s=sig*W/gx
    P=np.exp(-((xs[:,None]-np.repeat(cx,gy)[None])**2+(ys[:,None]-np.tile(cy,gx)[None])**2)/(2*s*s))
    return P/P.sum(1,keepdims=True)
def fit_field(Phi,Y,W0,lam):
    A=Phi.T@Phi+lam*np.eye(Phi.shape[1]); return np.linalg.solve(A, Phi.T@Y+lam*W0)
