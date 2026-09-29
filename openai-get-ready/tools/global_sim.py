import json,numpy as np,sys
key,gtf=sys.argv[1],sys.argv[2]
T=json.load(open('meas/text_trace.json'))[key]; d=json.load(open(gtf))
C0=np.array([[g['bbox'][0]+g['bbox'][2]/2, g['bbox'][1]+g['bbox'][3]/2] for g in T])
def pos(x,i):
    W=np.array(x[1:]).reshape(2,3); g=T[i]; x0,y0=g['bbox'][0]-8,g['bbox'][1]-8
    return W@[C0[i,0]-x0,C0[i,1]-y0,1]
out={}
for f in sorted(d,key=int):
    r=d[f]; ok=[i for i,x in enumerate(r) if x and x[0]>0.975]
    if len(ok)<3: continue
    X=C0[ok]; Y=np.array([pos(r[i],i) for i in ok])
    # similarity with uniform scale: [x';y'] = s*[x;y]+t
    A=np.zeros((2*len(ok),3)); b=Y.ravel()
    A[0::2,0]=X[:,0]; A[0::2,1]=1; A[1::2,0]=X[:,1]; A[1::2,2]=1
    p,*_=np.linalg.lstsq(A,b,rcond=None); res=(A@p-b).reshape(-1,2)
    out[int(f)]=[p.tolist(),len(ok),float(np.abs(res).max()),{i:(Y[k]-(p[0]*X[k]+p[1:])).round(2).tolist() for k,i in enumerate(ok)}]
json.dump(out,open(gtf.replace('.json','_sim.json'),'w'))
for f in sorted(out)[::4]+list(range(476,491)):
    if f in out: print(f,out[f][1],np.round(out[f][0],4),round(out[f][2],2))
