# re-measure only frames that contain badly fitted components (err>0.12)
import sys,json; sys.path.insert(0,'tools')
import dots
fn=sys.argv[1]; cols=sys.argv[2].split(','); maxarea=int(sys.argv[3])
d=json.load(open(fn))
bad=sorted(int(f) for f,r in d.items() if any(x[3]>0.12 for L in r.values() for x in L))
lo,hi=(int(sys.argv[4]),int(sys.argv[5])) if len(sys.argv)>5 else (0,10**6)
xmin=1160 if 'dots_e' in fn else 0
bad=[f for f in bad if lo<=f<hi]
print(len(bad),bad,flush=True)
import cv2,numpy as np
out=fn.replace('.json','_fix_%d.json'%lo); R={}
for f in bad:
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32); res={}
    for n in cols:
        al=dots.alpha(im,n); al[:,:xmin]=0; m=(al>0.3).astype(np.uint8)
        nl,l,st,ce=cv2.connectedComponentsWithStats(m); L=[]
        for i in range(1,nl):
            bx,by,bw,bh,ar=st[i]
            if ar<3 or ar>maxarea: continue
            pad=3; x0,y0=max(0,bx-pad),max(0,by-pad); x1,y1=min(1920,bx+bw+pad),min(1080,by+bh+pad)
            sub=np.clip(al[y0:y1,x0:x1],0,1)*(cv2.dilate((l[y0:y1,x0:x1]==i).astype(np.uint8),np.ones((5,5)))>0)
            dd,err,k=dots.fit_comp(sub,x0,y0)
            for q in dd: L.append([round(float(q[0]),3),round(float(q[1]),3),round(float(q[2]),3),round(float(err),3),k])
        res[n]=L
    R[f]=res; json.dump(R,open(out,'w'))
