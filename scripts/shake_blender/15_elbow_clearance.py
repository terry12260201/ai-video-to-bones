from kinematics import *
from scipy.optimize import least_squares
from scipy.interpolate import PchipInterpolator
p=ROOT/'工具腳本'/'motion_fit.npz';d=dict(np.load(p));aa=d['angles'].copy();trans=d['translation'];times=d['frame_times'];stance=PchipInterpolator([0,22,31,84,97,120],[0,0,1,1,0,0])(times);floor=float(d['floor_shift'])
for f,t in enumerate(times):
 if not 22<t<105:continue
 for side,sgn in [('L',1),('R',-1)]:
  n='foot_f.'+side;ki=list(d['foot_names']).index(n);chain=[idx[x+'_f.'+side] for x in ['hip','thigh','leg','shin']];base=aa[f].copy();goal=d['foot_targets'][f,ki].copy();kneegoal=sgn*(abs(H[chain[2],0])+.023*stance[f]);groups=[idx[x+'_f.'+side] for x in ['foot','claws','shin']];vi=np.where((W[:,groups].sum(1)>.6)&(V[:,2]<.022))[0];lift=0
  if 22<t<31:lift=.009*np.sin(np.pi*(t-22)/9)
  if 84<t<97:lift=.006*np.sin(np.pi*(t-84)/13)
  xorig=np.array([base[chain[0],1],base[chain[1],0],base[chain[1],1],base[chain[2],0],base[chain[2],1],base[chain[3],0]])
  def pose(x):
   a=base.copy();a[chain[0],1]=x[0];a[chain[1],:2]=x[1:3];a[chain[2],:2]=x[3:5];a[chain[3],0]=x[5];S=mats(a,trans[f]);a[idx[n]]=Rotation.from_matrix(S[parents[idx[n]],:3,:3].T).as_euler('xyz');return a
  x=xorig.copy()
  for _ in range(3):
   def res(x):
    S=mats(pose(x),trans[f]);foot=point(S,n,H[idx[n]]);knee=point(S,n,H[chain[2]]);return np.r_[(foot-goal)*2500,(knee[0]-kneegoal)*1500,(x-xorig)*.4]
   sol=least_squares(res,x,bounds=([-.7,-1.05,-.65,-1.15,-.65,-1.15],[.7,1.05,.65,1.15,.65,1.15]),max_nfev=25);x=sol.x;aa[f]=pose(x);S=mats(aa[f],trans[f]);v=np.einsum('vj,jab,vb->va',W[vi],S[:,:3,:],Vh[vi],optimize=True);delta=lift-float(v[:,2].min()+floor)
   if abs(delta)<.000012:break
   goal[2]+=delta
  d['foot_targets'][f,ki]=goal
for f,t in enumerate(times):
 if t>=106:aa[f]=aa[0]
aa[-1]=aa[0];d['angles']=aa;d['S']=np.array([mats(aa[f],trans[f]) for f in range(len(times))]);np.savez(p,**d);print('Elbow clearance solved without moving planted feet')
