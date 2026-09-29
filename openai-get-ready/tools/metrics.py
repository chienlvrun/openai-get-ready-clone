# per-frame mean abs diff + SSIM (gray 360p) clone vs ref; clone frame k*(fps/refFps)
import cv2,numpy as np,sys,json
from skimage.metrics import structural_similarity as ssim
cd=sys.argv[1]; a,b,st=int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]); ratio=float(sys.argv[5]) if len(sys.argv)>5 else 1
R={}
for f in range(a,b,st):
    c=cv2.imread('%s/%05d.png'%(cd,int(round(f*ratio))),0)
    if c is None: continue
    r=cv2.imread('of/%05d.png'%(f+1),0)
    r=cv2.resize(r,(640,360),interpolation=cv2.INTER_AREA).astype(float); c=cv2.resize(c,(640,360),interpolation=cv2.INTER_AREA).astype(float)
    R[f]=(float(np.abs(r-c).mean()),float(ssim(r,c,data_range=255)))
v=np.array(list(R.values()))
print('frames',len(R),'MAD %.3f  SSIM %.4f  worst:'%(v[:,0].mean(),v[:,1].mean()), sorted(R.items(),key=lambda x:-x[1][0])[:6])
if len(sys.argv)>6: json.dump(R,open(sys.argv[6],'w'))
