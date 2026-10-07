from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];rig=np.load(ROOT/'工具腳本'/'rig.npz');V=rig['V'];W=rig['W'];T=rig['T'];R=rig['rest'];H=rig['heads'];TAIL=rig['tails'];parents=rig['parents'];names=[str(x) for x in rig['names']];idx={n:i for i,n in enumerate(names)};NB=len(names);Vh=np.c_[V,np.ones(len(V))]
def rotate(h,ang):
 M=np.eye(4);M[:3,:3]=Rotation.from_euler('xyz',ang).as_matrix();M[:3,3]=h-M[:3,:3]@h;return M
def mats(angles,translation=(0,0,0)):
 S=np.zeros((NB,4,4));angles=np.asarray(angles);rots=Rotation.from_euler('xyz',angles).as_matrix()
 for i in range(NB):
  P=S[parents[i]] if parents[i]>=0 else np.eye(4);M=np.eye(4);M[:3,:3]=rots[i];M[:3,3]=H[i]-rots[i]@H[i];
  if i==idx['Spine_base']:M[:3,3]+=translation
  S[i]=P@M
 return S
def point(S,n,p):return (S[idx[n]]@np.r_[p,1])[:3]
def verts(S):return np.einsum('vj,jab,vb->va',W,S[:,:3,:],Vh,optimize=True)
def camera_basis(cam):
 az,el,scale,cx,cy=cam;d=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);rt=np.cross(-d,[0,0,1]);rt/=np.linalg.norm(rt);up=np.cross(rt,-d);return rt,up
TARGET=np.array([0,0,.25])
def project(P,cam):
 rt,up=camera_basis(cam);q=np.asarray(P)-TARGET;return np.c_[cam[3]+cam[2]*(q@rt),cam[4]-cam[2]*(q@up)]
NOSE=V[W[:,idx['nose']]>.8].mean(0);EYES={s:V[W[:,idx['eye.'+s]]>.8].mean(0) for s in ['L','R']}
PAWS={}
for end in ['f','b']:
 for side in ['L','R']:
  group=[idx[f'{p}_{end}.{side}'] for p in ['foot','claws','shin']];mask=(W[:,group].sum(1)>.8)&(V[:,2]<.014);PAWS[f'foot_{end}.{side}']=V[mask].mean(0)
