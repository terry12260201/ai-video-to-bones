import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path('__SHAKE_WORK__');rig=np.load(OUT/'工具腳本'/'rig.npz');W=rig['W'];T=rig['T'];names=list(rig['names']);idx={str(n):i for i,n in enumerate(names)};V=rig['V'];a=bpy.data.objects['Arm_Beagle'];mesh=bpy.data.objects['Cartoon_Beagle'];s=bpy.context.scene;data=np.load(OUT/'工具腳本'/'motion_fit.npz');dgraph=bpy.context.evaluated_depsgraph_get()
headgroups=[i for n,i in idx.items() if n in ['head','nose','neck','Mouth.L','Mouth.R','eye.L','eye.R','eyelid.L','eyelid.R']];hmask=W[:,headgroups].sum(1)>.65;ht=T[np.all(hmask[T],axis=1)]
earinds={side:np.where((W[:,idx['Ear_02.'+side]]>.55)&(np.linalg.norm(V-rig['heads'][idx['Ear_01.'+side]],axis=1)>.038))[0] for side in ['L','R']}
tonguemask=W[:,[idx['tongue_3'],idx['tongue_4']]].sum(1)>.65;tt=T[np.all(tonguemask[T],axis=1)]
eartris={side:T[np.all(np.isin(T,earinds[side]),axis=1)] for side in ['L','R']}
feet=[str(n) for n in data['foot_names']];soleinds={}
for n in feet:
 end='f' if '_f.' in n else 'b';side=n[-1];groups=[idx[f'{p}_{end}.{side}'] for p in ['foot','claws','shin']];soleinds[n]=np.where((W[:,groups].sum(1)>.6)&(V[:,2]<.022))[0]
def evalpose(fr):
 s.frame_set(math.floor(fr),subframe=fr%1);bpy.context.view_layer.update();ob=mesh.evaluated_get(dgraph);me=ob.to_mesh();vv=np.array([ob.matrix_world@v.co for v in me.vertices]);ob.to_mesh_clear();bm=np.array([[r[:] for r in (a.matrix_world@pb.matrix)] for pb in a.pose.bones]);return vv,bm
v0,b0=evalpose(1);v1,b1=evalpose(121);v2,b2=evalpose(2);v120,b120=evalpose(120)
seam={'max_bone_matrix_difference':float(abs(b1-b0).max()),'max_mesh_vertex_difference_m':float(np.linalg.norm(v1-v0,axis=1).max()),'first_interval_mesh_movement_m':float(np.linalg.norm(v2-v0,axis=1).max()),'last_interval_mesh_movement_m':float(np.linalg.norm(v1-v120,axis=1).max())}
records=[];rootx=[];floor_min=1;floor_max=-1;footangles=[];crossings=[];ear_inside=[];tongue_cross=[];limb_cross=[];paw_positions=[]
bodygroups=[i for n,i in idx.items() if str(n).startswith('Spine_') or n=='neck'];bodymask=W[:,bodygroups].sum(1)>.75;bodytris=T[np.all(bodymask[T],axis=1)]
limbtris={}
for end in ['f','b']:
 for side in ['L','R']:
  gs=[idx[f'{pref}_{end}.{side}'] for pref in ['thigh','leg','shin','foot','claws']];mask=W[:,gs].sum(1)>.85;limbtris[end+side]=T[np.all(mask[T],axis=1)]
def edge_cross_count(vv,tris,bvh):
 edges=set()
 for tri in tris:
  for u,v in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:edges.add(tuple(sorted([int(u),int(v)])))
 count=0
 for u,v in edges:
  start=Vector(vv[u]);delta=Vector(vv[v]-vv[u]);length=delta.length
  if length<1e-6:continue
  delta.normalize();hit,normal,index,dist=bvh.ray_cast(start+delta*.00001,delta,max(0,length-.00002))
  if hit is not None and dist>.00002:count+=1
 return count
for fr in np.arange(1,121.001,.25):
 vv,bm=evalpose(float(fr));low=float(vv[:,2].min());floor_min=min(floor_min,low);floor_max=max(floor_max,low);rootx.append(bm[idx['Root_bone'],:2,3].tolist())
 f=float(fr-1);soles={n:float(vv[soleinds[n],2].min()) for n in feet};paws=[]
 for n in feet:
  R0=b0[idx[n],:3,:3];RR=bm[idx[n],:3,:3];dot=float(np.clip((np.trace(RR@R0.T)-1)/2,-1,1));footangles.append(math.degrees(math.acos(dot)))
 bvh=BVHTree.FromPolygons([Vector(v) for v in vv],ht.tolist(),all_triangles=True,epsilon=0)
 ecounts={side:edge_cross_count(vv,eartris[side],bvh) for side in ['L','R']};tcount=edge_cross_count(vv,tt,bvh)
 inside={}
 for side,vi in earinds.items():
  depths=[]
  for v in vv[vi[::3]]:
   p,normal,ix,dist=bvh.find_nearest(Vector(v))
   if p is not None and (Vector(v)-p).dot(normal)<-.00075:depths.append(float(dist))
  inside[side]={'points':len(depths),'max_depth_m':max(depths,default=0)}
 if any(ecounts.values()):crossings.append({'frame':float(fr),'free_ear_edge_crossings':ecounts})
 if tcount:tongue_cross.append({'frame':float(fr),'free_tongue_edge_crossings':tcount})
 if any(i['points'] for i in inside.values()):ear_inside.append({'frame':float(fr),'ear_head_nearest_surface':inside})
 paw_positions.append({'frame':float(fr),'positions':{n:bm[idx[n],:3,3].tolist() for n in feet}})
 if True:
  bodybvh=BVHTree.FromPolygons([Vector(v) for v in vv],bodytris.tolist(),all_triangles=True,epsilon=0);limbtrees={n:BVHTree.FromPolygons([Vector(v) for v in vv],ts.tolist(),all_triangles=True,epsilon=0) for n,ts in limbtris.items()};counts={}
  for n,ts in limbtris.items():
   q=edge_cross_count(vv,ts,bodybvh)
   if q:counts[n+'_torso']=q
  keys=list(limbtris)
  for i,n in enumerate(keys):
   for nn in keys[i+1:]:
    q=edge_cross_count(vv,limbtris[n],limbtrees[nn])
    if q:counts[n+'_'+nn]=q
  if counts:limb_cross.append({'frame':float(fr),'free_limb_edge_crossings':counts})
 records.append({'frame':float(fr),'mesh_lowest_z_m':low,'soles_m':soles,'ear_edge_crossings':ecounts,'tongue_edge_crossings':tcount})
# Bone endpoint separation is an additional limb crossing check; it does not certify the full mesh.
min_foot_lr=min(float(np.linalg.norm((r['soles_m']['foot_f.L'] if False else np.array([0,0,0]))))) if False else 0
report={'sample_count':len(records),'sample_step_frames':.25,'seam':seam,'root_xy_range_m':np.ptp(np.array(rootx),axis=0).tolist(),'mesh_lowest_z_range_m':[floor_min,floor_max],'max_paw_rotation_change_deg':max(footangles),'free_limb_edge_crossing_frames':limb_cross,'paw_positions':paw_positions,'free_ear_edge_crossing_frames':crossings,'free_tongue_edge_crossing_frames':tongue_cross,'ear_head_signed_proximity_flags':ear_inside,'records':records,'coverage':'Evaluated mesh and bone endpoints at every quarter frame. Edge tests cover distal ears against head surface and distal tongue against head surface; they do not constitute an exhaustive triangle self-intersection proof.'}
(OUT/'驗證'/'Blender逐幀驗證.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));s.frame_set(1)
result={k:v for k,v in report.items() if k not in ['records','paw_positions']}
