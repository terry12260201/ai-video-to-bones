from kinematics import *
from scipy.optimize import least_squares
import cv2,json
from PIL import Image,ImageDraw
D=np.load(ROOT/'工具腳本'/'motion_fit.npz');data=dict(D);aa=data['angles'].copy();tr=data['translation'];cam=data['cam_front'];rows=json.loads((ROOT/'驗證'/'正面逐幀量測_raw.json').read_text());tip_indices={}
for s in ['R','L']:
 vs=np.where(W[:,idx['Ear_02.'+s]]>.3)[0];dist=np.linalg.norm(V[vs]-H[idx['Ear_01.'+s]],axis=1);tip_indices[s]=vs[np.argsort(dist)[-8:]]
def tip(S,side):
 vi=tip_indices[side];ps=np.einsum('vj,jab,vb->va',W[vi],S[:,:3,:],Vh[vi],optimize=True);return ps.mean(0)
records=[]
for f in range(121):
 row=rows[f];nx,ny=row['nose'];eyes=row['eyes'];mid=np.mean(eyes,0) if eyes else np.array([nx,ny-40]);im=cv2.imread(str(ROOT/'參考逐幀'/f'front_{f:03d}.png'));bb,gg,rr=im.astype(float).transpose(2,0,1)
 brown=(rr>gg*1.25)&(rr>bb*1.55)&(rr>75)&(rr<176)&(gg<113);brown[:max(100,int(ny-210))]=False;brown[min(510,int(ny+48)):]=False;brown[:,:450]=False;brown[:,760:]=False
 yy,xx=np.where(brown);targets={}
 if len(xx):
  top=yy<np.percentile(yy,1)+1;uptip=np.array([xx[top].mean(),yy[top].mean()]);up=uptip[1]<mid[1]-65
  # Extremity of the other ear in the outward half-plane.
  for side,sgn in [('R',-1),('L',1)]:
   sel=(xx<mid[0]-20) if sgn<0 else (xx>mid[0]+20)
   if sel.any():
    xs,ys=xx[sel],yy[sel];end=(xs<np.percentile(xs,2)+1) if sgn<0 else (xs>np.percentile(xs,98)-1);targets[side]=np.array([xs[end].mean(),ys[end].mean()])
  if up and not 86<=f<=91:
   Sb=mats(aa[f],tr[f]);roots={ss:project([point(Sb,'Ear_01.'+ss,H[idx['Ear_01.'+ss]])],cam)[0] for ss in ['R','L']};side=min(roots,key=lambda ss:np.linalg.norm(roots[ss]-uptip))
   targets[side]=uptip
  # Source transient ears stretch with generative deformation; fit soft targets, do not scale bones.
 if f<23 or f>99:targets={}
 for side,sgn in [('R',-1),('L',1)]:
  if side not in targets:continue
  goal=targets[side];base=aa[f].copy();i1=idx['Ear_01.'+side];i2=idx['Ear_02.'+side]
  priorlift=float(np.clip(-sgn*base[i1,1],0,2.3));priorcurl=float(np.clip(-sgn*base[i2,1],-.65,.65))
  def pose(x):
   a=base.copy();a[i1]=[x[2],-sgn*x[0],sgn*x[3]];a[i2]=[.05,-sgn*x[1],0];return a
  def res(x):
   p=project([tip(mats(pose(x),tr[f]),side)],cam)[0]
   return np.r_[(p-goal)/5,(x[:2]-[priorlift,priorcurl])*.15,x[2:]*.5]
  sols=[least_squares(res,[lift,0,-.08,0],bounds=([-.1,-1.05,-.6,-.65],[2.8,1.4,.6,.65]),max_nfev=35) for lift in [.2,1.3,2.35]]
  sol=min(sols,key=lambda s:np.linalg.norm(s.fun));aa[f]=pose(sol.x);S=mats(aa[f],tr[f]);pred=project([tip(S,side)],cam)[0];records.append({'frame':f,'side':side,'reference_tip':goal.tolist(),'projected_tip':pred.tolist(),'error_px':float(np.linalg.norm(pred-goal)),'angles_rad':sol.x.tolist()})
# Hold neutral at seam, and settle rather than cutting the last ear key.
for f in range(100,106):
 u=(f-99)/7;u=u*u*(3-2*u)
 for s in ['R','L']:
  for prefix in ['Ear_01.','Ear_02.']:i=idx[prefix+s];aa[f,i]=aa[99,i]*(1-u)+aa[0,i]*u
for f in range(106,121):aa[f]=aa[0]
aa[-1]=aa[0];data['angles']=aa;data['S']=np.array([mats(aa[f],tr[f]) for f in range(121)]);np.savez(ROOT/'工具腳本'/'motion_fit.npz',**data)
(ROOT/'驗證'/'耳尖逐幀對位.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('ear median / max px',np.median([r['error_px'] for r in records]),max(r['error_px'] for r in records))
# Numerical support checks before sending the refined data through Blender MCP.
mins=[];footerrors=[]
for f in range(121):
 S=data['S'][f];vv=verts(S);mins.append(float(vv[:,2].min()))
 for k,n in enumerate(data['foot_names']):footerrors.append(float(np.linalg.norm(point(S,str(n),H[idx[str(n)]])-data['foot_targets'][f,k])))
print('mesh lowest z min / max',min(mins),max(mins),'max support error',max(footerrors))
