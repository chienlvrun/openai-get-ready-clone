# final per-frame disc table: raw sub-pixel fits, gaps linearly interpolated
import json,numpy as np
T=json.load(open('meas/tracks.json'))
LIFE={'white':(0,268),'purple':(157,289),'orange':(136,272),'green':(144,280),'dark':(141,276),'blue':(156,284)}
C={}
for c,(a,b) in LIFE.items():
    fr=np.arange(a,b+1); Z=np.full((len(fr),3),np.nan)
    for i,f in enumerate(fr):
        if str(f) in T[c]: Z[i]=T[c][str(f)][:3]
    if c=='white':
        for i,f in enumerate(fr):
            if f<7: Z[i]=[943.93,539.52,1109.39+ (7-f)*1.5]
    # purple 157 is a sliver fit; drop & interpolate
    if c=='purple': Z[0]=np.nan
    for j in range(3):
        ok=~np.isnan(Z[:,j]); Z[:,j]=np.interp(fr,fr[ok],Z[ok,j])
    for i,f in enumerate(fr): C.setdefault(int(f),[]).append([c]+np.round(Z[i],3).tolist())
json.dump(C,open('meas/discs.json','w'))
print(len(C))
