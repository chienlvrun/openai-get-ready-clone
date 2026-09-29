# Refine per-frame global pose with one ECC on the composite state model (all glyphs, fills + outlines)
import sys,json,cv2,numpy as np; sys.path.insert(0,'tools')
from glyphraster import parse,raster
from glyphstate import cover,outline_raster
from compile_text import compile_shot
LINE={'white':(None,1.0),'green':(1.0,0.62),'purple':(1.0,0.62)}  # (width override, alpha)
def model_img(G,P,st,sw,W,H,YO):
    img=np.zeros((H,W),np.float32)
    for i,g in enumerate(G):
        if st[i]==0: continue
        L=[p-[0,YO] for p in P[i]]
        allp=np.concatenate(L); x0,y0=np.floor(allp.min(0)).astype(int)-4; x1,y1=np.ceil(allp.max(0)).astype(int)+4
        Ls=[q-[x0,y0] for q in L]
        if st[i]==2: m=raster([Ls],x1-x0,y1-y0,ss=4)
        else:
            w,al=LINE[g['color']]; m=al*outline_raster(Ls,x1-x0,y1-y0,w or sw,ss=4)
        img[y0:y1,x0:x1]=np.maximum(img[y0:y1,x0:x1],m)
    return img
def run(key,gs,stf,a,b,sw,out,frames=None):
    o,_,_=compile_shot(key,gs,a,b,sw)
    S=json.load(open(stf))['st']; G=json.load(open('meas/text_trace.json'))[key]; P=[parse(g['d']) for g in G]
    YO=300; H=480
    res={}
    for f in (frames or range(a,b+1)):
        st=S[str(f)]
        if sum(st)==0: continue
        s,tx,ty=o['frames'][f-a]['T']
        tpl=model_img(G,P,st,sw,1920,H,YO)
        im=cv2.imread('of/%05d.png'%(f+1))[YO:YO+H,:,::-1].astype(np.float32)
        U=cv2.cvtColor(im.astype(np.uint8),cv2.COLOR_RGB2YCrCb).astype(np.float32)
        obs=np.maximum.reduce([cover(im,'white'),cover(im,'green'),cover(im,'purple')])
        # mask dot colours (orange/blue) — strongly chromatic but not green/purple
        cb,cr=U[:,:,2]-128,U[:,:,1]-128
        dotm=((cr>40)&(cb<0))|((cb>40)&(cr<0))|((cr>40)&(cb>40)&False)
        mask=(cv2.dilate(dotm.astype(np.uint8),np.ones((5,5)))==0).astype(np.uint8)
        # warp maps template (ref coords, y offset YO) -> image (y offset YO)
        W0=np.array([[s,0,tx],[0,s,ty+(s-1)*YO]],np.float32)
        try:
            cc,Wm=cv2.findTransformECC(tpl,obs,W0.copy(),cv2.MOTION_AFFINE,(3,200,1e-7),mask,1)
        except cv2.error: continue
        sn=(Wm[0,0]+Wm[1,1])/2
        res[f]=[float(sn),float(Wm[0,2]),float(Wm[1,2]-(sn-1)*YO),float(cc),[float(s),float(tx),float(ty)]]
    json.dump(res,open(out,'w'))
if __name__=='__main__':
    run(sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]),float(sys.argv[6]),sys.argv[7])
