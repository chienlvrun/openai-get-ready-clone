import sys,json; sys.path.insert(0,'tools')
import dots
a,b=int(sys.argv[1]),int(sys.argv[2]); cols=sys.argv[3].split(','); out=sys.argv[4]
maxarea=int(sys.argv[5]) if len(sys.argv)>5 else 30000
xmin=int(sys.argv[6]) if len(sys.argv)>6 else 0
R={}
import cv2,numpy as np
for f in range(a,b):
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
    res={}
    for n in cols:
        al=dots.alpha(im,n); al[:,:xmin]=0; m=(al>0.3).astype(np.uint8)
        nl,l,st,ce=cv2.connectedComponentsWithStats(m); L=[]
        for i in range(1,nl):
            bx,by,bw,bh,ar=st[i]
            if ar<3 or ar>maxarea: continue
            pad=3; x0,y0=max(0,bx-pad),max(0,by-pad); x1,y1=min(1920,bx+bw+pad),min(1080,by+bh+pad)
            sub=np.clip(al[y0:y1,x0:x1],0,1)*(cv2.dilate((l[y0:y1,x0:x1]==i).astype(np.uint8),np.ones((5,5)))>0)
            d,err,k=dots.fit_comp(sub,x0,y0)
            for q in d: L.append([round(float(q[0]),3),round(float(q[1]),3),round(float(q[2]),3),round(float(err),3),k])
        res[n]=L
    R[f]=res
    if f%5==0: json.dump(R,open(out,'w'))
json.dump(R,open(out,'w'))
