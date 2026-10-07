from kinematics import *
import json,cv2
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import PchipInterpolator
rows=json.loads((ROOT/'驗證'/'正面逐幀量測_raw.json').read_text());F=121
# Fit neutral camera against actual reference nose, eyes, four paw locations.
points=np.array([NOSE,EYES['R'],EYES['L'],PAWS['foot_f.R'],PAWS['foot_f.L'],PAWS['foot_b.R'],PAWS['foot_b.L']])
target=np.array([rows[0]['nose'],*rows[0]['eyes'],*rows[0]['front_paws'],[624,529],[694,529]])
x0=np.array([-1.38,.24,900,640,360.])
opt=least_squares(lambda c:((project(points,c)-target)*np.array([1,1,1,1,1,.5,.5])[:,None]).ravel(),x0,bounds=([-1.55,.06,750,570,300],[-1.1,.45,1100,700,440]),loss='soft_l1',f_scale=8)
CAM=opt.x;print('CAM',CAM,'neutral pixel errors',np.linalg.norm(project(points,CAM)-target,axis=1))
# Slow crouch profile from measured nose descent, with fast shake removed.
nose=np.array([r['nose'] for r in rows]);drift=gaussian_filter1d(nose[:,1],3);bend=np.clip((drift-drift[0])/145,0,1);bend[:22]=0;bend[100:]=0
roll=np.array([r['head_roll_rad'] if r['head_roll_rad'] is not None else np.nan for r in rows]);valid=np.isfinite(roll)&(abs(roll)<.96)
for f in range(F):
 es=rows[f]['eyes']
 if es:
  mid=np.mean(es,0);dy=nose[f,1]-mid[1]
  if dy<23 or dy>57:valid[f]=False
# Missing eye pair frames use yaw-informed shake prior, fitted from trustworthy frame measurements.
yawproxy=-(nose[:,0]-gaussian_filter1d(nose[:,0],4))/55
A=np.c_[yawproxy[valid],np.ones(valid.sum())];coef=np.linalg.lstsq(A,roll[valid],rcond=None)[0]
prior=np.clip(coef[0]*yawproxy+coef[1],-.70,.70)
roll[~valid]=prior[~valid];roll=np.clip(roll,-.78,.78);roll[:22]=0;roll[99:]=0
angles=np.zeros((F,NB,3));trans=np.zeros((F,3));fit=[];last=np.zeros(3)
for f in range(F):
 a=np.zeros((NB,3));b=bend[f]
 # Distributed torsion: pelvis < ribcage < neck < head. No root horizontal motion.
 a[idx['Spine_base']]=[.045*b,.045*roll[f],0]
 a[idx['Spine_02']]=[.050*b,.03*roll[f],0]
 a[idx['Spine_03']]=[.070*b,.06*roll[f],0]
 a[idx['Spine_04']]=[.070*b,.06*roll[f],0]
 a[idx['Spine_05']]=[.070*b,.06*roll[f],0]
 tr=np.array([0,0,-.040*b]);goalnose=nose[f];es=rows[f]['eyes'];good=bool(es) and valid[f]
 def sethead(x):
  aa=a.copy();neckpitch,headpitch,yaw,rl=x;aa[idx['neck']]=[neckpitch,rl*.28,yaw*.20];aa[idx['head']]=[headpitch,rl*.72,yaw*.80];return aa
 def resid(x):
  S=mats(sethead(x),tr);pred=project([point(S,'nose',NOSE)],CAM)[0];r=list((pred-goalnose)/4)
  if good:
   predeyes=project([point(S,'eye.R',EYES['R']),point(S,'eye.L',EYES['L'])],CAM);r.extend(((predeyes-np.array(es))/5).ravel())
  nod=.45*np.exp(-((f-88)/2.0)**2);r.extend([(x[3]-roll[f])*.8,(x[2]-yawproxy[f]*.32)*.4,(x[0]+x[1]+.305*b-.20*b-nod)*1.5,(x[0]-.38*b)*.15]);return r
 sol=least_squares(resid,np.array([.40*b,-.50*b,.2*yawproxy[f],roll[f]]),bounds=([-.30,-1.15,-.55,-.90],[.85,.7,.55,.90]),max_nfev=45)
 aa=sethead(sol.x);angles[f]=aa;trans[f]=tr;pred=project([point(mats(aa,tr),'nose',NOSE)],CAM)[0];fit.append({'frame':f,'source_nose':goalnose.tolist(),'projected_nose':pred.tolist(),'nose_error_px':float(np.linalg.norm(pred-goalnose)),'eye_pair_used':bool(good),'head_parameters_rad':sol.x.tolist(),'roll_measurement_rad':float(roll[f])})
# Use actual nose/eye phase; ears lag angular reversals by one video frame.
headroll=angles[:,idx['head'],1]+angles[:,idx['neck'],1]
# Per-frame reference ear silhouette endpoints (brown mask, each side of eye midpoint).
reference_ears=[]
for f in range(F):
 im=cv2.imread(str(ROOT/'參考逐幀'/f'front_{f:03d}.png'));bb,gg,rr=im.astype(float).transpose(2,0,1);brown=(rr>gg*1.25)&(rr>bb*1.5)&(rr>70)&(rr<175)&(gg<115)
 # constrain to head area, excluding legs, saddle, and background
 ny=nose[f,1];top=max(100,int(ny-190));bot=min(510,int(ny+80));brown[:top]=False;brown[bot:]=False;brown[:,:450]=False;brown[:,765:]=False
 # left / right extremity constrained to outside face center. Used as soft targets only.
 left=brown.copy();left[:,int(nose[f,0]-25):]=False;right=brown.copy();right[:,:int(nose[f,0]+25)]=False
 ears=[]
 for m in [left,right]:
  yy,xx=np.where(m)
  if len(xx):
   # extremity follows whichever is farther from the attachment, including rising ear tip.
   centre=np.array([nose[f,0],ny-40]);dist=(xx-centre[0])**2+(yy-centre[1])**2;sel=np.argsort(dist)[-max(4,len(xx)//100):];ears.append([float(np.mean(xx[sel])),float(np.mean(yy[sel]))])
  else:ears.append(None)
 reference_ears.append(ears)
# Ear tip from actual skinned mesh. R is screen left in the frontal camera.
earverts={}
for side in ['L','R']:
 w=W[:,idx['Ear_02.'+side]];vs=np.where(w>.35)[0];h=H[idx['Ear_01.'+side]];dist=np.linalg.norm(V[vs]-h,axis=1);earverts[side]=vs[np.argsort(dist)[-10:]]
for f in range(F):
 active=0 if f<22 or f>99 else 1
 env=float(np.clip((f-21)/3,0,1)*np.clip((101-f)/8,0,1))
 lag=headroll[max(0,f-1)];rnow=headroll[f];Sbase=mats(angles[f],trans[f]);noseworld=point(Sbase,'nose',NOSE)
 for side,sgn,slot in [('R',-1,0),('L',1,1)]:
  # Lift toward outward hemisphere on each reversal; lag persists into the recovery.
  lift=env*(.72-sgn*1.15*lag)
  angles[f,idx['Ear_01.'+side]]=[-.15*env,-sgn*lift,-.08*sgn*env]
  angles[f,idx['Ear_02.'+side]]=[.06*env,-sgn*(.22*env-.45*sgn*lag*env),.06*sgn*env]
 # mouth closes and tongue withdraws for the fast shake; visible return as reference recovers.
 mouthenv=float(1-np.clip(gaussian_filter1d(np.array([r['tongue_visible_pixels'] for r in rows],dtype=float)/450,.65)[f],0,1))
 if f<22 or f>105:mouthenv=0
 angles[f,idx['mouth'],0]=-.22*mouthenv
 for j in range(1,5):
  angles[f,idx[f'tongue_{j}'],0]=-.04*mouthenv
  angles[f,idx[f'tongue_{j}'],2]=.035*env*np.sin(.5*j)*lag
 for side in ['L','R']:angles[f,idx['eyelid.'+side],0]=.62*float(np.clip((f-21)/3,0,1)*np.clip((98-f)/10,0,1))
 # restrained tail follows trunk with lag, from side-view range; no unrelated wag.
 for j in range(1,6):angles[f,idx[f'Tail_{j:02d}']]=[(-.11-.10*b if j==1 else -.02 if j==2 else 0)+.014*b*np.sin(f*.55-j*.4),0,.025*env*np.sin(f*1.45-j*.4)]
# Fixed floor targets; front paws widen once and hold, then step back during recovery.
# Targets are physical 3D positions, not projected camera motion.
feet={n:H[idx[n]].copy() for n in PAWS};stance=np.clip(PchipInterpolator([0,22,31,84,97,120],[0,0,1,1,0,0])(np.arange(F)),0,1)
foot_targets=np.zeros((F,4,3));foot_names=list(PAWS)
for f in range(F):
 for k,n in enumerate(foot_names):
  goal=feet[n].copy();sgn=1 if n.endswith('L') else -1;front='_f.' in n
  if front:goal[0]+=sgn*.041*stance[f];goal[1]-=.011*stance[f]
  # a small arc during actual stance change keeps the placement from looking like sliding.
  if front:
   if 22<f<31:goal[2]+=.009*np.sin(np.pi*(f-22)/9)
   if 84<f<97:goal[2]+=.006*np.sin(np.pi*(f-84)/13)
  foot_targets[f,k]=goal
  chain=[f'{p}_{"f" if front else "b"}.{n[-1]}' for p in ['hip','thigh','leg','shin']];base=angles[f].copy()
  # two sagittal hinges plus mild upper-limb abduction. Four rigid segments, no translation or scaling.
  def legs(x):
   aa=base.copy();aa[idx[chain[0]],1]=x[0];aa[idx[chain[1]],0]=x[1];aa[idx[chain[2]],0]=x[2];aa[idx[chain[3]],0]=x[3];return aa
  def resleg(x):
   aa=legs(x);S=mats(aa,trans[f]);p=point(S,n,feet[n]);footrotation=S[idx[n],:3,:3];r=(p-goal)*1500
   return np.r_[r,x*np.array([.6,.35,.25,.25])]
  sol=least_squares(resleg,[sgn*.10*stance[f],.10*bend[f],-.12*bend[f],.02*bend[f]],bounds=([-.55,-.8,-.9,-.9],[.55,.8,.9,.9]),max_nfev=55)
  angles[f]=legs(sol.x)
  # Counter-rotate foot to preserve its original floor orientation.
  S=mats(angles[f],trans[f]);ip=idx[n];P=S[parents[ip],:3,:3];angles[f,ip]=Rotation.from_matrix(P.T).as_euler('xyz')
# Exact duplicate seam and still intervals either side => pose and velocity match.
angles[:21]=angles[0];trans[:21]=trans[0]
for f in range(106,F):angles[f]=angles[0];trans[f]=trans[0]
angles[-1]=angles[0];trans[-1]=trans[0]
S=np.array([mats(angles[f],trans[f]) for f in range(F)])
sideinfo=json.loads((ROOT/'驗證'/'側面逐幀量測.json').read_text());np.savez(ROOT/'工具腳本'/'motion_fit.npz',cam_side=sideinfo['camera'],tongue_retraction=np.clip(1-gaussian_filter1d(np.array([r['tongue_visible_pixels'] for r in rows],float)/450,.65),0,1),angles=angles,translation=trans,S=S,names=names,cam_front=CAM,foot_targets=foot_targets,foot_names=foot_names,bend=bend)
(ROOT/'驗證'/'逐幀對照量測.json').write_text(json.dumps({'camera_front':CAM.tolist(),'nose_fit':fit,'ear_silhouette_targets':reference_ears,'policy':'Front nose and eye measurements drive pose. Independent generated side clip constrains anatomical plausibility; not assumed synchronized multiview capture.'},ensure_ascii=False,indent=2))
print('fit nose median/max',np.median([r['nose_error_px'] for r in fit]),max(r['nose_error_px'] for r in fit));print('saved motion',S.shape)
