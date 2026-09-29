# Build one clean track per coloured disc from raw circle detections
import json,numpy as np
D={}
for fn in ['meas/circ_a.json','meas/circ_b.json']: D.update(json.load(open(fn)))
cols=['white','purple','orange','green','dark','blue']
TR={c:{} for c in cols}
for c in cols:
    prev=None; vel=np.zeros(3)
    for f in range(0,300):
        cand=[x for x in D[str(f)][c] if x[4]>30 and x[5]/max(1,x[6])>0.3 and x[2]>3]
        if not cand: prev=None; continue
        if prev is None:
            # start: largest
            best=max(cand,key=lambda x:x[4])
            if c!='white' and best[2]>1500: continue
        else:
            pred=prev+vel
            best=min(cand,key=lambda x:np.abs(np.array(x[:3])-pred).sum())
            if np.abs(np.array(best[:3])-pred).sum()>120: prev=None; continue
        p=np.array(best[:3])
        if prev is not None: vel=p-prev
        prev=p; TR[c][f]=[round(v,3) for v in best[:4]]
for c in cols:
    fs=sorted(TR[c]); print(c,fs[0] if fs else None,fs[-1] if fs else None,len(fs))
    # gaps
    g=[f for f in range(fs[0],fs[-1]) if f not in TR[c]] if fs else []
    print('  gaps',g[:30])
json.dump(TR,open('meas/tracks.json','w'))
