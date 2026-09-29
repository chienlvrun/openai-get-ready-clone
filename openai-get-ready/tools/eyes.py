# Per-frame eye glyph measurement: affine ECC fit of vector templates inside each measured disc.
import cv2,numpy as np,json,sys
T=json.load(open('meas/eye_templates.json'))
for k in T:
    k2=np.sqrt(T[k]['area']); T[k]['polys']=[(np.array(p)/k2).tolist() for p in T[k]['polys']]
S=45.0  # template raster scale (unit -> px)
TS=128
def raster(name,ss=4):
    img=np.zeros((TS*ss,TS*ss),np.uint8)
    pts=[(np.array(p)*S*ss+TS*ss/2).round().astype(np.int32) for p in T[name]['polys']]
    cv2.fillPoly(img,pts,255)
    # holes: polygons with opposite orientation -> use even-odd via xor
    if len(pts)>1:
        img=np.zeros_like(img)
        for p in pts:
            t=np.zeros_like(img); cv2.fillPoly(t,[p],255); img^=t
    return cv2.resize(img,(TS,TS),interpolation=cv2.INTER_AREA).astype(np.float32)/255
TPL={k:raster(k) for k in T}
def moments(cov):
    ys,xs=np.mgrid[:cov.shape[0],:cov.shape[1]]; w=cov.sum()
    cx=(cov*xs).sum()/w; cy=(cov*ys).sum()/w
    C=np.array([[(cov*(xs-cx)**2).sum(),(cov*(xs-cx)*(ys-cy)).sum()],[0,(cov*(ys-cy)**2).sum()]])/w; C[1,0]=C[0,1]
    return cx,cy,C,w
TM={k:moments(v) for k,v in TPL.items()}
def sqrtm(C):
    e,v=np.linalg.eigh(C); return v@np.diag(np.sqrt(np.maximum(e,1e-9)))@v.T
def fit_eye(cov,mask,cands,prev=None):
    if prev is not None: cands=[prev[0]]+[c for c in cands if c!=prev[0]]
    """cov: eye coverage patch, mask: valid region (uint8). returns best (name, 2x3 A mapping template-units->patch px, cc)"""
    ox,oy,C,w=moments(cov*mask)
    best=None
    for name in cands:
        tcx,tcy,TC,tw=TM[name]
        B=sqrtm(C)@np.linalg.inv(sqrtm(TC))
        inits=[]
        for ang in np.arange(0,360,45):
            a=np.deg2rad(ang); R=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
            for fl in [1,-1]:
                M=B@R@np.diag([1,fl]) if True else None
                # use uniform scale init instead of full sqrtm for robustness
                sc=np.sqrt(w/tw)
                M2=sc*R@np.diag([1,fl])
                for MM in (M2,):
                    t=np.array([ox,oy])-MM@np.array([tcx,tcy])
                    inits.append(np.c_[MM,t].astype(np.float32))
        if prev is not None and prev[0]==name: inits=[prev[1].astype(np.float32)]+inits
        for W0 in inits:
            try:
                cc,Wm=cv2.findTransformECC(TPL[name],cov.astype(np.float32),W0.copy(),cv2.MOTION_AFFINE,
                    (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,60,1e-4),mask,1)
            except cv2.error: continue
            if best is None or cc>best[2]: best=(name,Wm,cc)
            if cc>0.97: return best
    return best
