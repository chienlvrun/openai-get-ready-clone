# Glyph state per frame by model comparison under the measured global pose: none / outline / fill
import sys,json,cv2,numpy as np; sys.path.insert(0,'tools')
from glyphraster import parse,raster
from glyphstate import cover,outline_raster
COLC={'green':(17,208,78),'purple':(140,58,239)}
from compile_text import compile_shot
def run(key,gs,a,b,sw,out):
    o,_,_=compile_shot(key,gs,a,b,sw)
    from scipy.ndimage import gaussian_filter1d
    T0=np.array([fr['T'] for fr in o['frames']]); T=np.stack([gaussian_filter1d(T0[:,j],1.0,mode='nearest') for j in range(3)],1); T[:12]=T0[:12]; T[-12:]=T0[-12:]
    G=json.load(open('meas/text_trace.json'))[key]; P=[parse(g['d']) for g in G]
    ST={}; ERR={}
    for k,f in enumerate(range(a,b+1)):
        im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
        U=cv2.cvtColor(im.astype(np.uint8),cv2.COLOR_RGB2YCrCb).astype(np.float32)
        chroma=np.hypot(U[:,:,1]-128,U[:,:,2]-128); Ycc=U
        s,tx,ty=T[k]; row=[]; er=[]
        for i,g in enumerate(G):
            Q=[p*s+[tx,ty] for p in P[i]]; allp=np.concatenate(Q)
            x0,y0=np.floor(allp.min(0)).astype(int)-6; x1,y1=np.ceil(allp.max(0)).astype(int)+6
            x0,y0=max(0,x0),max(0,y0); x1,y1=min(1920,x1),min(1080,y1)
            L=[q-[x0,y0] for q in Q]
            fill=raster([L],x1-x0,y1-y0,ss=4)
            lw,la=((1.0,1.0) if g['color']!='white' else (sw,1.0))
            line=la*outline_raster(L,x1-x0,y1-y0,lw,ss=4)
            obs=cover(im[y0:y1,x0:x1],g['color'])
            if g['color']=='white':
                dm=(chroma[y0:y1,x0:x1]<25).astype(np.uint8); dm=cv2.erode(dm,np.ones((5,5)))>0
            else:
                # luma coverage (chroma of thin lines is blurred by 4:2:0); mask pixels whose chroma points elsewhere (dots)
                c=np.array(COLC[g['color']],np.float32)
                yc=float(np.array([[c]],np.uint8).astype(np.uint8) is None) or float(cv2.cvtColor(np.array([[c]],np.uint8),cv2.COLOR_RGB2YCrCb)[0,0,0])
                ccr,ccb=[float(v)-128 for v in cv2.cvtColor(np.array([[c]],np.uint8),cv2.COLOR_RGB2YCrCb)[0,0,1:]]
                Yp=Ycc[y0:y1,x0:x1,0]; cr=Ycc[y0:y1,x0:x1,1]-128; cb=Ycc[y0:y1,x0:x1,2]-128
                obs=np.clip(Yp/yc,0,1)
                cosang=(cr*ccr+cb*ccb)/(np.hypot(cr,cb)*np.hypot(ccr,ccb)+1e-6)
                bad=(np.hypot(cr,cb)>15)&(cosang<0.5)
                dm=cv2.dilate(bad.astype(np.uint8),np.ones((5,5)))==0
            o_=obs[dm]; l_=line[dm]
            al=float(np.clip((o_*l_).sum()/max((l_*l_).sum(),1e-6),0,1.5))
            e0=np.mean(o_**2); e1=np.mean((o_-al*l_)**2); e2=np.mean((o_-fill[dm])**2)
            if e2<=min(e0,e1): v=2
            elif al>0.06 and e1<e0*0.85: v=round(min(al,1.0),3)
            else: v=0
            row.append(v); er.append([round(float(x),4) for x in (e0,e1,e2,al)])
        ST[f]=row; ERR[f]=er
    json.dump({'st':ST,'err':ERR},open(out,'w'))
if __name__=='__main__':
    run(sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),float(sys.argv[5]),sys.argv[6])
