# pop detector: consecutive-frame diffs at 180p gray, clone vs reference
import cv2,numpy as np,sys
cd=sys.argv[1]; N=int(sys.argv[2])
def seq(get):
    prev=None; d=[]
    for f in range(N):
        g=cv2.resize(get(f),(320,180),interpolation=cv2.INTER_AREA).astype(float)
        d.append(0 if prev is None else np.abs(g-prev).mean()); prev=g
    return np.array(d)
dc=seq(lambda f:cv2.imread('%s/%05d.png'%(cd,f),0)); dr=seq(lambda f:cv2.imread('of/%05d.png'%(f+1),0))
flag=[]
for k in range(1,N):
    nb=np.median(np.r_[dc[max(1,k-4):k],dc[k+1:k+5]])
    if dc[k]>0.6 and dc[k]>3*nb:
        flag.append((k,round(dc[k],2),round(dr[k],2)))
print('clone flags',len(flag),flag)
# genuine pops = flagged in clone but not in reference
print('clone-only',[x for x in flag if not (x[2]>0.6 and abs(x[1]-x[2])<0.5*max(x[1],x[2]))])
