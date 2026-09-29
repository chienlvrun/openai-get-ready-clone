import cv2,numpy as np,json,sys
sys.path.insert(0,'tools')
from eyes import *
COL={'white':(223,223,223),'purple':(140,58,239),'orange':(242,106,32),'green':(17,208,78),'dark':(38,38,38),'blue':(9,107,247)}
DISC=json.load(open('meas/discs.json'))
def clean(fr):
    L=[]
    for n,l in fr.items():
        for c in l:
            if c[4]>60 and c[5]/c[6]>0.4: L.append([n]+c[:3])
    out=[]
    for c in L:
        inside=any(o is not c and o[3]>c[3]*1.5 and np.hypot(o[1]-c[1],o[2]-c[2])<o[3] for o in L)
        if not inside: out.append(c)
    if not out: out=[['white',959.0,538.0,4000.0]]
    return out
CANDS=['ast','chev','plus','o','caret','bar']
def run(f,prevs={}):
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
    H,W=im.shape[:2]; res=[]; newprev=[]
    for n,cx,cy,r in DISC.get(str(f),[]):
        x0,y0=int(max(0,cx-r-2)),int(max(0,cy-r-2)); x1,y1=int(min(W,cx+r+3)),int(min(H,cy+r+3))
        if x1-x0<8 or y1-y0<8: continue
        p=im[y0:y1,x0:x1]
        if n=='dark': cov=np.clip((p.mean(2)-38)/(255-38),0,1)
        else:
            c=np.array(COL[n],np.float32); cov=1-np.clip((p@c)/(c@c),0,1)
        ys,xs=np.mgrid[y0:y1,x0:x1]; dd=np.hypot(xs+0.5-cx-0.5,ys+0.5-cy-0.5)
        dd=np.hypot(xs-cx,ys-cy)
        mask=(dd<r-1.5).astype(np.uint8)
        cov=cov*mask
        m=(cov>0.5).astype(np.uint8); nl,l,st,ce=cv2.connectedComponentsWithStats(m)
        eyes=[]
        for i in range(1,nl):
            if st[i,4]<15: continue
            bx,by,bw,bh,_=st[i]; pad=int(max(bw,bh)*0.6)+4
            ex0,ey0=max(0,bx-pad),max(0,by-pad); ex1,ey1=min(x1-x0,bx+bw+pad),min(y1-y0,by+bh+pad)
            sub=cov[ey0:ey1,ex0:ex1]*(cv2.dilate((l[ey0:ey1,ex0:ex1]==i).astype(np.uint8),np.ones((5,5)))>0)
            mk=mask[ey0:ey1,ex0:ex1]
            gx,gy=ce[i][0]+x0,ce[i][1]+y0
            pv=None; bd=1e9
            for (pn,pg,pW,px,py) in prevs.get('list',[]):
                d=np.hypot(px-gx,py-gy)
                if pn==n and d<bd and d<r*0.5: bd=d; pv=(pg,pW,px,py)
            prev=None
            if pv is not None:
                W0=pv[1].copy(); W0[:,2]+= [ -(x0+ex0), -(y0+ey0)]; W0[:,2]+= [gx-pv[2], gy-pv[3]]
                prev=(pv[0],W0)
            b=fit_eye(sub.astype(np.float32),mk,CANDS,prev)
            if b is None: continue
            name,Wm,cc=b
            # convert: template px -> template units: u*S+TS/2 ; to frame: + (x0+ex0, y0+ey0)
            A=Wm[:,:2]*S; t=Wm[:,:2]@np.array([TS/2,TS/2])+Wm[:,2]+[x0+ex0,y0+ey0]
            Wg=Wm.copy(); Wg[:,2]+=[x0+ex0,y0+ey0]; newprev.append((n,name,Wg,gx,gy))
            eyes.append({'g':name,'A':np.c_[A,t].round(4).tolist(),'cc':round(float(cc),4),'area':int(st[i,4])})
        res.append({'c':n,'x':cx,'y':cy,'r':r,'eyes':eyes})
    prevs['list']=newprev
    return res
if __name__=='__main__':
    a,b=int(sys.argv[1]),int(sys.argv[2]); R={}; P={}
    for f in range(a,b):
        R[f]=run(f,P)
        if f%10==0: json.dump(R,open(sys.argv[3],'w'))
    json.dump(R,open(sys.argv[3],'w'))
