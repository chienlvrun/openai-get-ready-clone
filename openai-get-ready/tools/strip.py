# strip.py a b step out size cloneDir : tiles [ref | clone] with frame numbers
import cv2,numpy as np,sys
a,b,st=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[4]; W=int(sys.argv[5]); cd=sys.argv[6]
rows=[]
for f in range(a,b,st):
    r=cv2.imread('of/%05d.png'%(f+1)); c=cv2.imread('%s/%05d.png'%(cd,f))
    if c is None: continue
    h=int(W*1080/1920)
    r=cv2.resize(r,(W,h),interpolation=cv2.INTER_AREA); c=cv2.resize(c,(W,h),interpolation=cv2.INTER_AREA)
    d=np.clip(np.abs(r.astype(int)-c.astype(int))*3,0,255).astype(np.uint8)
    for im in (r,c): cv2.putText(im,str(f),(4,18),0,.5,(0,0,255),1)
    rows.append(np.hstack([r,np.full((h,3,3),80,np.uint8),c,np.full((h,3,3),80,np.uint8),d]))
cv2.imwrite(out,np.vstack(rows))
