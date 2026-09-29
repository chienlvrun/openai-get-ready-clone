# Trace big "1 day." from frame 360: white coverage where visible; under dots use the small-trace prediction
import sys,json,cv2,numpy as np,potrace; sys.path.insert(0,'tools')
from glyphraster import *
from bigfit import fit,T,W0
F=360
r=fit(F)
im=cv2.imread('of/%05d.png'%(F+1))[:,:,::-1].astype(np.float32)
white=np.clip(im.min(2)/255,0,1)
org=(np.abs(im[:,:,0]-im[:,:,2])>40).astype(np.uint8); dm=cv2.dilate(org,np.ones((9,9)))>0
UP=8; out=[]
for k in range(5):
    cc,Wm=r[k]
    g=T[k]; P=parse(g['d']); x,y,w,h=g['bbox']; pad=6; x0,y0=x-pad,y-pad
    if cc<0.9:  # '.' : global transform
        Wm=W0.copy(); Wm[:,2]=W0[:,:2]@[x0,y0]+W0[:,2]
    A=Wm.astype(np.float64)
    # predicted coverage in frame coords: map glyph polys (frame coords of small) -> big
    Pb=[ (p-[x0,y0])@A[:,:2].T+A[:,2] for p in P]
    allp=np.concatenate(Pb); bx0,by0=np.floor(allp.min(0)).astype(int)-8; bx1,by1=np.ceil(allp.max(0)).astype(int)+8
    pred=raster([[q-[bx0,by0] for q in Pb]],bx1-bx0,by1-by0,ss=8)
    obs=white[by0:by1,bx0:bx1]; mk=dm[by0:by1,bx0:bx1]
    # also keep only this glyph's neighbourhood: restrict observed to dilated prediction
    near=cv2.dilate((pred>0.02).astype(np.uint8),np.ones((9,9)))>0
    wgt=np.clip(cv2.GaussianBlur(mk.astype(np.float32),(0,0),2.0)*1.5,0,1)
    comp=(wgt*pred+(1-wgt)*obs)*near
    big=cv2.resize(comp,None,fx=UP,fy=UP,interpolation=cv2.INTER_CUBIC)>0.5
    big=np.pad(big,UP)
    path=potrace.Bitmap(~big).trace(turdsize=50,alphamax=1.0,opticurve=True,opttolerance=0.2)
    def Pt(pt): return ((pt.x-UP)/UP+bx0,(pt.y-UP)/UP+by0)
    d=[]
    for curve in path:
        d.append('M%.3f %.3f'%Pt(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner: d.append('L%.3f %.3f L%.3f %.3f'%(*Pt(seg.c),*Pt(seg.end_point)))
            else: d.append('C%.3f %.3f %.3f %.3f %.3f %.3f'%(*Pt(seg.c1),*Pt(seg.c2),*Pt(seg.end_point)))
        d.append('Z')
    out.append({'color':'white','d':' '.join(d),'A':A.tolist(),'src':k,'cc':float(cc)})
    print(k,cc,len(path))
J=json.load(open('meas/text_trace.json')); J['big']=out; json.dump(J,open('meas/text_trace.json','w'))
