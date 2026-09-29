# white handle dots on the bracket outlines: 3x3 opening removes 1.6px strokes, keeps ~5.6px dots
import cv2,numpy as np,json
R={}
for f in range(491,580):
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
    x0,y0,x1,y1=1080,470,1460,620
    p=im[y0:y1,x0:x1]; U=cv2.cvtColor(p.astype(np.uint8),cv2.COLOR_RGB2YCrCb).astype(np.float32)
    a=np.clip(p.min(2)/255,0,1); a[np.hypot(U[:,:,1]-128,U[:,:,2]-128)>20]=0
    b=(a>0.5).astype(np.uint8); o=cv2.morphologyEx(b,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(o); L=[]
    for i in range(1,n):
        if st[i,4]<6 or st[i,4]>80 or max(st[i,2],st[i,3])>9: continue
        m=(l==i); w=a*cv2.dilate(m.astype(np.uint8),np.ones((3,3)))
        ys,xs=np.mgrid[:a.shape[0],:a.shape[1]]+0.5
        cx,cy=(w*xs).sum()/w.sum(),(w*ys).sum()/w.sum()
        L.append([round(float(cx+x0),3),round(float(cy+y0),3),2.8,0.0,1])
    R[f]={'white':L}
json.dump(R,open('meas/dots_w.json','w'))
print({f:len(v['white']) for f,v in R.items() if v['white']})
