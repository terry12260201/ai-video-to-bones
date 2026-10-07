from kinematics import *
import json
p=ROOT/'工具腳本'/'motion_fit.npz';d=dict(np.load(p));a=d['angles'].copy();changes=[]
for f in range(len(a)):
 for side,sgn in [('R',-1),('L',1)]:
  i1=idx['Ear_01.'+side];i2=idx['Ear_02.'+side];old=np.r_[a[f,i1],a[f,i2]].copy();lift=float(np.clip(-sgn*a[f,i1,1],-.05,2.55));curl=float(np.clip(-sgn*a[f,i2,1],-.25,.55));curl=min(curl,2.78-lift);curl=max(curl,-.03-lift);a[f,i1]=[np.clip(a[f,i1,0],-.18,.18),-sgn*lift,np.clip(a[f,i1,2],-.18,.18)];a[f,i2]=[np.clip(a[f,i2,0],-.10,.10),-sgn*curl,np.clip(a[f,i2,2],-.15,.15)]
  if np.linalg.norm(np.r_[a[f,i1],a[f,i2]]-old)>.001:changes.append({'frame':f,'side':side,'before':old.tolist(),'after':np.r_[a[f,i1],a[f,i2]].tolist()})
 env=float(d['tongue_retraction'][f]) if 22<=f<=105 else 0
 for j in range(1,5):a[f,idx[f'tongue_{j}'],0]=.04*env
for f in range(106,121):a[f]=a[0]
a[-1]=a[0];d['angles']=a;d['S']=np.array([mats(a[f],d['translation'][f]) for f in range(len(a))]);np.savez(p,**d);(ROOT/'驗證'/'避免穿插校正.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2));print('ear bounds changes',len(changes))
