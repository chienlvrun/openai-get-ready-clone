# rasterise traced glyph paths (SVG-ish d strings) with AA via 4x supersampling (numpy/cv2)
import numpy as np,cv2,re
def parse(d):
    toks=re.findall(r'[MLCZ]|-?\d+\.?\d*',d); polys=[];cur=[];i=0;p=None
    while i<len(toks):
        t=toks[i]
        if t=='M':
            if cur: polys.append(np.array(cur))
            p=(float(toks[i+1]),float(toks[i+2])); cur=[p]; i+=3
        elif t=='L': p=(float(toks[i+1]),float(toks[i+2])); cur.append(p); i+=3
        elif t=='C':
            c1=(float(toks[i+1]),float(toks[i+2])); c2=(float(toks[i+3]),float(toks[i+4])); e=(float(toks[i+5]),float(toks[i+6]))
            for u in np.linspace(0,1,17)[1:]:
                x=(1-u)**3*p[0]+3*(1-u)**2*u*c1[0]+3*(1-u)*u*u*c2[0]+u**3*e[0]
                y=(1-u)**3*p[1]+3*(1-u)**2*u*c1[1]+3*(1-u)*u*u*c2[1]+u**3*e[1]
                cur.append((x,y))
            p=e; i+=7
        elif t=='Z': i+=1
        else: i+=1
    if cur: polys.append(np.array(cur))
    return polys
def raster(polys_list,W,H,A=None,ss=4):
    """polys in frame coords; A optional 2x3 affine applied; even-odd fill per glyph"""
    out=np.zeros((H*ss,W*ss),np.uint8)
    for polys in polys_list:
        g=np.zeros_like(out)
        for p in polys:
            q=p if A is None else p@A[:,:2].T+A[:,2]
            t=np.zeros_like(out); cv2.fillPoly(t,[(q*ss*16).round().astype(np.int32)],255,cv2.LINE_8,4); g^=t
        out|=g
    return cv2.resize(out,(W,H),interpolation=cv2.INTER_AREA).astype(np.float32)/255
