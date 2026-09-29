import sys,json,cv2,numpy as np; sys.path.insert(0,'tools')
from glyphraster import *
T=json.load(open('meas/text_trace.json'))['t1']
W0=np.load('meas/big1day_A.npy')
def fit(f,gl=range(5),init=None):
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
    white=np.clip(im.min(2)/255,0,1)
    org=(im[:,:,0]-im[:,:,2]>60).astype(np.uint8); mask=(1-cv2.dilate(org,np.ones((9,9)))).astype(np.uint8)
    out=[]
    for k in gl:
        g=T[k]; P=parse(g['d']); x,y,w,h=g['bbox']; pad=6; x0,y0=x-pad,y-pad
        tpl=raster([[p-[x0,y0] for p in P]],w+2*pad,h+2*pad,ss=8)
        Wi=(init[k] if init is not None else W0).astype(np.float32).copy()
        if init is None: Wi[:,2]=W0[:,:2]@[x0,y0]+W0[:,2]
        try:
            cc,Wm=cv2.findTransformECC(tpl,white,Wi,cv2.MOTION_AFFINE,(3,300,1e-7),mask,1)
        except cv2.error as e: cc,Wm=-1,Wi
        out.append((cc,Wm))
    return out
if __name__=='__main__':
    for f in [336,345,360,369]:
        r=fit(f)
        print(f,[(round(cc,4),Wm[0,0].round(4),Wm[1,1].round(4),Wm[0,1].round(4),Wm[:,2].round(2)) for cc,Wm in r])
