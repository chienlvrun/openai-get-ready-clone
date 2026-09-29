# Vectorise the big-shot outline strokes themselves (frame 331, all glyphs in outline state) as filled paths
import sys,json,cv2,numpy as np,potrace; sys.path.insert(0,'tools')
from glyphraster import parse
from compile_text import compile_shot
F=331; UP=8
o,_,_=compile_shot('big','meas/gs_big.json',301,370,3.3)
T=o['frames'][F-301]['T']; s,tx,ty=T
J=json.load(open('meas/text_trace.json')); G=J['big']
im=cv2.imread('of/%05d.png'%(F+1))[:,:,::-1].astype(np.float32)
U=cv2.cvtColor(im.astype(np.uint8),cv2.COLOR_RGB2YCrCb).astype(np.float32)
white=np.clip(im.min(2)/255,0,1)
dotm=(np.hypot(U[:,:,1]-128,U[:,:,2]-128)>20).astype(np.uint8); dotm=cv2.dilate(dotm,np.ones((5,5)))
pl=np.zeros(white.shape,np.uint8)
for g in G:
    for p in parse(g['d']):
        q=p*s+[tx,ty]; cv2.polylines(pl,[(q*16).round().astype(np.int32)],True,255,3,cv2.LINE_AA,4)
DD=json.load(open('meas/dots_b.json'))[str(F)]['orange']
dm2=np.zeros(white.shape,np.uint8)
for x,y,r,e,kk in DD: cv2.circle(dm2,(int(round(x*16)),int(round(y*16))),int((r-0.5)*16),255,-1,cv2.LINE_8,4)
white=np.maximum(white,(pl.astype(np.float32)/255)*(dm2>0))
# glyph ownership: nearest glyph contour (pose-transformed) within 10px
owner=np.full(white.shape,-1,np.int32); best=np.full(white.shape,1e9,np.float32)
for k,g in enumerate(G):
    m=np.zeros(white.shape,np.uint8)
    for p in parse(g['d']):
        q=p*s+[tx,ty]; cv2.polylines(m,[(q*16).round().astype(np.int32)],True,255,1,cv2.LINE_8,4)
    dist=cv2.distanceTransform(255-m,cv2.DIST_L2,5)
    upd=(dist<best)&(dist<10); owner[upd]=k; best[upd]=dist[upd]
for k,g in enumerate(G):
    a=white*(owner==k)
    ys,xs=np.where(a>0.1); x0,y0=xs.min()-4,ys.min()-4; x1,y1=xs.max()+5,ys.max()+5
    sub=a[y0:y1,x0:x1]
    big=cv2.resize(sub,None,fx=UP,fy=UP,interpolation=cv2.INTER_CUBIC)>0.5
    big=np.pad(big,UP)
    path=potrace.Bitmap(~big).trace(turdsize=30,alphamax=1.0,opticurve=True,opttolerance=0.2)
    def Pt(pt): return ((pt.x-UP)/UP+x0,(pt.y-UP)/UP+y0)
    d=[]
    for curve in path:
        d.append('M%.3f %.3f'%Pt(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner: d.append('L%.3f %.3f L%.3f %.3f'%(*Pt(seg.c),*Pt(seg.end_point)))
            else: d.append('C%.3f %.3f %.3f %.3f %.3f %.3f'%(*Pt(seg.c1),*Pt(seg.c2),*Pt(seg.end_point)))
        d.append('Z')
    g['dline']=' '.join(d); g['lineT']=[s,tx,ty]
    print(k,len(path))
json.dump(J,open('meas/text_trace.json','w'))
