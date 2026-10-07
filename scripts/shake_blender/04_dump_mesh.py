import bpy,numpy as np
from pathlib import Path
out=Path('__SHAKE_WORK__')
a=bpy.data.objects['Arm_Beagle'];m=bpy.data.objects['Cartoon_Beagle'];names=[b.name for b in a.data.bones];idx={n:i for i,n in enumerate(names)}
W=np.zeros((len(m.data.vertices),len(names)))
for v in m.data.vertices:
 for g in v.groups:
  n=m.vertex_groups[g.group].name
  if n in idx:W[v.index,idx[n]]=g.weight
V=np.array([v.co[:] for v in m.data.vertices]);m.data.calc_loop_triangles();T=np.array([t.vertices[:] for t in m.data.loop_triangles]);R=np.array([[r[:] for r in b.matrix_local] for b in a.data.bones]);heads=np.array([b.head_local[:] for b in a.data.bones]);tails=np.array([b.tail_local[:] for b in a.data.bones]);parents=np.array([idx[b.parent.name] if b.parent else -1 for b in a.data.bones]);np.savez(out/'工具腳本'/'rig.npz',V=V,T=T,W=W,names=names,rest=R,heads=heads,tails=tails,parents=parents)
# reference-size cameras and correct side
from mathutils import Vector
for name,loc,tar in [('front',(.15,-2,.8),(0,0,.285)),('side',(2,-.03,.78),(0,0,.285)),('threequarter',(1.3,-1.8,.95),(0,0,.285))]:
 cam=bpy.data.objects['Cam_'+name];cam.location=loc;cam.rotation_euler=(Vector(tar)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.45
s=bpy.context.scene;s.render.resolution_percentage=100
for name in ['front','side']:
 s.camera=bpy.data.objects['Cam_'+name];s.render.filepath=str(out/'驗證'/('rest2_'+name+'.png'));bpy.ops.render.render(write_still=True)
result={'vertices':len(V),'triangles':len(T),'weights_sum_min':float(W.sum(1).min()),'weights_sum_max':float(W.sum(1).max())}
