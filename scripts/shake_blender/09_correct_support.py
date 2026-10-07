from kinematics import *
from scipy.optimize import least_squares
import json
D=np.load(ROOT/'工具腳本'/'motion_fit.npz');d=dict(D);aa=d['angles'].copy();trans=d['translation'];feet=d['foot_names'];targets=d['foot_targets'].copy();floor_shift=.0001773;records=[]
for f in range(121):
 for k,n0 in enumerate(feet):
  n=str(n0);end='f' if '_f.' in n else 'b';side=n[-1];indices=[idx[f'{p}_{end}.{side}'] for p in ['foot','claws','shin']];vi=np.where((W[:,indices].sum(1)>.6)&(V[:,2]<.022))[0];goal=targets[f,k].copy();lift=goal[2]-H[idx[n],2]
  chain=[idx[f'{p}_{end}.{side}'] for p in ['hip','thigh','leg','shin']]
  for _ in range(2):
   S=mats(aa[f],trans[f]);v=np.einsum('vj,jab,vb->va',W[vi],S[:,:3,:],Vh[vi],optimize=True);low=float(v[:,2].min()+floor_shift);correction=lift-low
   if abs(correction)<.00002:break
   goal[2]+=correction;base=aa[f].copy();x0=np.array([base[chain[0],1],base[chain[1],0],base[chain[2],0],base[chain[3],0]])
   def pose(x):
    a=base.copy();a[chain[0],1]=x[0]
    for j in range(1,4):a[chain[j],0]=x[j]
    S=mats(a,trans[f]);a[idx[n]]=Rotation.from_matrix(S[parents[idx[n]],:3,:3].T).as_euler('xyz');return a
   def res(x):
    a=pose(x);S=mats(a,trans[f]);return np.r_[(point(S,n,H[idx[n]])-goal)*2000,(x-x0)*.08]
   sol=least_squares(res,x0,bounds=([-.6,-.85,-.95,-.95],[.6,.85,.95,.95]),max_nfev=20);aa[f]=pose(sol.x)
  S=mats(aa[f],trans[f]);v=np.einsum('vj,jab,vb->va',W[vi],S[:,:3,:],Vh[vi],optimize=True);records.append({'frame':f,'paw':n,'sole_height_m':float(v[:,2].min()+floor_shift),'target_lift_m':float(lift),'floor_error_m':float(v[:,2].min()+floor_shift-lift)})
  targets[f,k]=goal
for f in range(106,121):aa[f]=aa[0]
aa[-1]=aa[0];d['angles']=aa;d['S']=np.array([mats(aa[f],trans[f]) for f in range(121)]);d['foot_targets']=targets;d['floor_shift']=floor_shift;np.savez(ROOT/'工具腳本'/'motion_fit.npz',**d);(ROOT/'驗證'/'腳底逐幀校正.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('sole max error',max(abs(r['floor_error_m']) for r in records))
