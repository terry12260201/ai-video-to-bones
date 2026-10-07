import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
O=Path('__SHAKE_WORK__');s=bpy.context.scene;oldarm=bpy.data.objects['Arm_Beagle'];oldmesh=bpy.data.objects['Cartoon_Beagle'];before=set(bpy.data.objects);actions_before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(O/'beagle_shake_loop.glb'));new=[o for o in bpy.data.objects if o not in before];arm=next(o for o in new if o.type=='ARMATURE');mesh=next(o for o in new if o.type=='MESH');acts=[a for a in bpy.data.actions if a not in actions_before];assert len(acts)==1
for t in arm.animation_data.nla_tracks:t.mute=True
arm.animation_data.action=acts[0]
# glTF starts at t=0, corresponding to Blender frame 1 in the source scene.
for layer in acts[0].layers:
 for strip in layer.strips:
  for slot in acts[0].slots:
   bag=strip.channelbag(slot)
   if bag:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.co.x+=1;kp.handle_left.x+=1;kp.handle_right.x+=1
     fc.update()
dg=bpy.context.evaluated_depsgraph_get()
def pose(o):
 ob=o.evaluated_get(dg);me=ob.to_mesh();v=np.array([ob.matrix_world@x.co for x in me.vertices]);ob.to_mesh_clear();return v
records=[];first=None;last=None
for fr in np.arange(1,121.001,.25):
 s.frame_set(math.floor(fr),subframe=float(fr%1));bpy.context.view_layer.update();v=pose(oldmesh);w=pose(mesh);kdt=KDTree(len(v))
 for i,p in enumerate(v):kdt.insert(Vector(p),i)
 kdt.balance();dist=max(kdt.find(Vector(p))[2] for p in w);records.append({'frame':float(fr),'max_nearest_vertex_distance_m':float(dist),'glb_mesh_lowest_z_m':float(w[:,2].min())})
 if fr==1:first=w.copy()
 if fr==121:last=w.copy()
report={'imported_animation':acts[0].name,'imported_frame_range':list(acts[0].frame_range),'samples':len(records),'max_geometry_difference_m':max(r['max_nearest_vertex_distance_m'] for r in records),'glb_first_last_vertex_difference_m':float(np.linalg.norm(last-first,axis=1).max()),'glb_mesh_lowest_z_m':min(r['glb_mesh_lowest_z_m'] for r in records),'records':records};(O/'驗證'/'GLB重新匯入驗證.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));assert report['max_geometry_difference_m']<.00002;assert report['glb_first_last_vertex_difference_m']<.000001
for o in new:bpy.data.objects.remove(o,do_unlink=True)
for a in acts:bpy.data.actions.remove(a)
s.frame_set(1);s.frame_start=1;s.frame_end=120;s.camera=bpy.data.objects['Cam_threequarter'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'beagle_shake_loop.blend'));result={k:v for k,v in report.items() if k!='records'}
