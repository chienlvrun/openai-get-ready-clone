# Trace glyph outlines from a clean reference frame -> bezier paths (potrace on 8x upsampled coverage)
import cv2,numpy as np,json,sys,potrace
UP=8
def coverage(im,col):
    c=np.array(col,np.float32); return np.clip((im@c)/(c@c),0,1)
def trace_frame(f,colors,box):
    im=cv2.imread('of/%05d.png'%(f+1))[:,:,::-1].astype(np.float32)
    x0,y0,x1,y1=box; p=im[y0:y1,x0:x1]
    glyphs=[]
    for cname,col in colors.items():
        c=np.array(col,np.float32)
        a=coverage(p,col); resid=np.linalg.norm(p-a[...,None]*c,axis=2); a[resid>60]=0
        if cname!='white':
            # luma coverage is full resolution (chroma is 4:2:0): Y/Yc near the colour mask
            Y=cv2.cvtColor(p.astype(np.uint8),cv2.COLOR_RGB2YCrCb)[:,:,0].astype(np.float32)
            yc=float(cv2.cvtColor(np.array([[col]],np.uint8),cv2.COLOR_RGB2YCrCb)[0,0,0])
            near=cv2.dilate((a>0.3).astype(np.uint8),np.ones((5,5)))>0
            a=np.clip(Y/yc,0,1)*near
        m=(a>0.5).astype(np.uint8); n,l,st,ce=cv2.connectedComponentsWithStats(m)
        for i in range(1,n):
            if st[i,4]<(30 if cname=='white' else 300): continue
            bx,by,bw,bh,_=st[i]; pad=3
            sx0,sy0=max(0,bx-pad),max(0,by-pad); sx1,sy1=min(p.shape[1],bx+bw+pad),min(p.shape[0],by+bh+pad)
            keep=cv2.dilate((l[sy0:sy1,sx0:sx1]==i).astype(np.uint8),np.ones((3,3)))>0
            sub=a[sy0:sy1,sx0:sx1]*keep
            big=cv2.resize(sub,None,fx=UP,fy=UP,interpolation=cv2.INTER_CUBIC)
            bm=big>0.5
            bm=np.pad(bm,UP)
            path=potrace.Bitmap(~bm).trace(turdsize=20,alphamax=1.0,opticurve=True,opttolerance=0.2)
            ox,oy=x0+sx0-1,y0+sy0-1   # offset: pixel-center convention handled below
            def P(pt): # upsampled coords -> frame coords (pixel edges at integers)
                return [round((pt.x-UP)/UP+x0+sx0,3),round((pt.y-UP)/UP+y0+sy0,3)]
            d=[]
            for curve in path:
                d.append('M%.3f %.3f'%tuple(P(curve.start_point)))
                for seg in curve.segments:
                    if seg.is_corner:
                        d.append('L%.3f %.3f L%.3f %.3f'%(*P(seg.c),*P(seg.end_point)))
                    else:
                        d.append('C%.3f %.3f %.3f %.3f %.3f %.3f'%(*P(seg.c1),*P(seg.c2),*P(seg.end_point)))
                d.append('Z')
            glyphs.append({'color':cname,'bbox':[int(x0+bx),int(y0+by),int(bw),int(bh)],'cx':float(x0+ce[i][0]),'d':' '.join(d),'area':int(st[i,4])})
    glyphs.sort(key=lambda g:g['bbox'][0])
    return glyphs
if __name__=='__main__':
    T2=trace_frame(700,{'white':(255,255,255),'green':(17,208,78),'purple':(140,58,239)},(460,470,1470,630))
    J=json.load(open('meas/text_trace.json')); old=J['t2']
    assert len(old)==len(T2) and all(a['color']==b['color'] for a,b in zip(old,T2))
    J['t2']=T2; json.dump(J,open('meas/text_trace.json','w')); T1=J['t1']
    for T in (T1,T2): print([(g['color'][0],g['bbox']) for g in T])
