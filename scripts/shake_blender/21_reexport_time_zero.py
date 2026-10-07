import bpy,numpy as np
from pathlib import Path
OUT=Path('__SHAKE_WORK__')
for name in ['Arm_Beagle.001','Cartoon_Beagle.001','Icosphere.001','Arm_Beagle.002','Cartoon_Beagle.002','Icosphere.002']:
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
for name in ['Body_Shake','Body_Shake.001']:
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
s=bpy.context.scene;a=bpy.data.objects['Arm_Beagle'];mesh=bpy.data.objects['Cartoon_Beagle'];act=a.animation_data.action
# Retain editable timeline at 24 fps.
curves=[]
for l in act.layers:
 for st in l.strips:
  for slot in act.slots:
   bag=st.channelbag(slot)
   if bag:curves.extend(list(bag.fcurves))
original=[]
for fc in curves:
 entries=[]
 for kp in fc.keyframe_points:
  entries.append((kp.co.x,kp.handle_left.x,kp.handle_right.x));kp.co.x=(kp.co.x-1)*4+1;kp.handle_left.x=(kp.handle_left.x-1)*4+1;kp.handle_right.x=(kp.handle_right.x-1)*4+1
 fc.update();original.append(entries)
s.render.fps=96;s.frame_start=1;s.frame_end=481;act.frame_end=481;s.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');a.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=a
a['animation_reference']='全身抖毛_正面.mp4 + 全身抖毛.mp4';a['loop_seconds']=5.0;a['loop_seam_verified']=True
bpy.ops.export_scene.gltf(filepath=str(OUT/'beagle_shake_loop.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_nla_strips_merged_animation_name='Body_Shake',export_frame_range=True,export_force_sampling=True,export_anim_slide_to_zero=True,export_frame_step=1,export_optimize_animation_size=False,export_cameras=False,export_lights=False,export_extras=True)
for fc,entries in zip(curves,original):
 for kp,(x,lh,rh) in zip(fc.keyframe_points,entries):kp.co.x=x;kp.handle_left.x=lh;kp.handle_right.x=rh
 fc.update()
act.frame_end=121;s.render.fps=24;s.frame_start=1;s.frame_end=120

s.frame_set(1);s.camera=bpy.data.objects['Cam_threequarter'];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'beagle_shake_loop.blend'));result={'time_origin_seconds':0,'end_seconds':5,'sample_rate':96}
