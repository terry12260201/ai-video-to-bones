from kinematics import *
from scipy.spatial.transform import Slerp
from scipy.optimize import least_squares
import json
p=ROOT/'工具腳本'/'motion_fit.npz';d=dict(np.load(p));a0=d['angles'];times0=np.arange(121);times=np.arange(0,120.0001,.25);F=len(times);a=np.empty((F,NB,3))
for i in range(NB):a[:,i]=Slerp(times0,Rotation.from_euler('xyz',a0[:,i]))(times).as_euler('xyz')
trans=np.stack([np.interp(times,times0,d['translation'][:,i]) for i in range(3)],1);targets=np.empty((F,4,3))
for k in range(4):
 for j in range(3):targets[:,k,j]=np.interp(times,times0,d['foot_targets'][:,k,j])
records=[];floor_shift=float(d['floor_shift'])
for f,t in enumerate(times):
 for k,n0 in enumerate(d['foot_names']):
  n=str(n0);end='f' if '_f.' in n else 'b';side=n[-1];chain=[idx[f'{b}_{end}.{side}'] for b in ['hip','thigh','leg','shin']];group=[idx[f'{b}_{end}.{side}'] for b in ['foot','claws','shin']];vi=np.where((W[:,group].sum(1)>.6)&(V[:,2]<.022))[0];goal=targets[f,k].copy();lift=0
  if end=='f':
   if 22<t<31:lift=.009*np.sin(np.pi*(t-22)/9)
   if 84<t<97:lift=.006*np.sin(np.pi*(t-84)/13)
  # Re-solve the chain and counter-rotate paw at every quarter frame.
  for _ in range(3):
   base=a[f].copy();S=mats(base,trans[f]);base[idx[n]]=Rotation.from_matrix(S[parents[idx[n]],:3,:3].T).as_euler('xyz');a[f]=base;S=mats(base,trans[f]);v=np.einsum('vj,jab,vb->va',W[vi],S[:,:3,:],Vh[vi],optimize=True);low=float(v[:,2].min()+floor_shift);correction=lift-low
   current=point(S,n,H[idx[n]]);xyerr=np.linalg.norm(current[:2]-goal[:2]);goal[2]=current[2]+correction
   if abs(correction)<.000015 and xyerr<.000015:break
   x0=np.array([base[chain[0],1],base[chain[1],0],base[chain[2],0],base[chain[3],0]])
   def pose(x):
    aa=base.copy();aa[chain[0],1]=x[0]
    for j in range(1,4):aa[chain[j],0]=x[j]
    Sm=mats(aa,trans[f]);aa[idx[n]]=Rotation.from_matrix(Sm[parents[idx[n]],:3,:3].T).as_euler('xyz');return aa
   def res(x):
    Sm=mats(pose(x),trans[f]);return np.r_[(point(Sm,n,H[idx[n]])-goal)*2500,(x-x0)*.03]
   sol=least_squares(res,x0,bounds=([-.65,-.95,-1.1,-1.1],[.65,.95,1.1,1.1]),max_nfev=15);a[f]=pose(sol.x)
  targets[f,k]=goal;S=mats(a[f],trans[f]);v=np.einsum('vj,jab,vb->va',W[vi],S[:,:3,:],Vh[vi],optimize=True);records.append({'reference_frame':float(t),'paw':n,'sole_height_m':float(v[:,2].min()+floor_shift),'target_lift_m':float(lift)})
 if f%80==0:print('fine support',f,'/',F,flush=True)
for i,t in enumerate(times):
 if t>=106:a[i]=a[0];trans[i]=trans[0]
a[-1]=a[0];trans[-1]=trans[0];d['angles']=a;d['translation']=trans;d['S']=np.array([mats(a[f],trans[f]) for f in range(F)]);d['frame_times']=times;d['foot_targets']=targets;d['tongue_retraction']=np.interp(times,times0,d['tongue_retraction']);d['bend']=np.interp(times,times0,d['bend']);np.savez(p,**d);(ROOT/'驗證'/'四分之一幀腳底校正.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('fine max sole error',max(abs(x['sole_height_m']-x['target_lift_m']) for x in records))
