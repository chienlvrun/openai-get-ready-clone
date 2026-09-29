# Clean + RTS-smooth disc tracks with explicit life ranges
import json,numpy as np,sys
sys.path.insert(0,'tools'); from mathfit import rts
T=json.load(open('meas/tracks.json'))
LIFE={'white':(0,268),'purple':(157,289),'orange':(136,272),'green':(144,280),'dark':(141,276),'blue':(156,284)}
OUT={}
for c,(a,b) in LIFE.items():
    fr=np.arange(a,b+1); Z=np.full((len(fr),3),np.nan)
    for i,f in enumerate(fr):
        if str(f) in T[c]: Z[i]=T[c][str(f)][:3]
    raw=Z.copy()
    if c=='white':
        # frames with no visible edge (0..6): extrapolate later
        pass
    S=np.zeros_like(Z)
    for it in range(2):
        for j in range(3):
            z=Z[:,j].copy()
            s,_=rts(z,1/60,q=3e8,r=0.05**2)
            S[:,j]=s
        bad=np.abs(Z-S).max(1)>2.0
        if it==0: print(c,'outliers',fr[bad].tolist()); Z[bad]=np.nan
    OUT[c]={'a':a,'b':b,'raw':np.round(raw,3).tolist(),'s':np.round(S,3).tolist()}
    d=np.nanmax(np.abs(raw-S),0); print(c,'max|raw-s|',d.round(3))
json.dump(OUT,open('meas/tracks2.json','w'))
