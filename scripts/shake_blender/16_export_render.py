import bpy,numpy as np,json,math
from pathlib import Path
OUT=Path('__SHAKE_WORK__');s=bpy.context.scene;a=bpy.data.objects['Arm_Beagle'];mesh=bpy.data.objects['Cartoon_Beagle'];act=a.animation_data.action
verify=json.loads((OUT/'驗證'/'Blender逐幀驗證.json').read_text())
assert verify['seam']['max_mesh_vertex_difference_m']<1e-8
assert not verify['free_ear_edge_crossing_frames'], 'Ear collision remains'
assert not verify['free_tongue_edge_crossing_frames'], 'Tongue collision remains'
assert not verify['free_limb_edge_crossing_frames'], 'Limb collision remains'
# Explicit ground datum for editing and inspection. Excluded from the character GLB.
if 'Ground_Datum' not in bpy.data.objects:
 bpy.ops.mesh.primitive_plane_add(size=3,location=(0,0,-.00002));g=bpy.context.object;g.name='Ground_Datum';g.hide_render=True;g.display_type='WIRE';g['purpose']='Z=0 腳底水平面；不屬於狗模型，不匯出 GLB'
# Actual reference movies are attached to the matching camera views for scrubbing in Blender.
root=OUT.parent
for name,fn,offset in [('front','全身抖毛_正面.mp4',0),('side','全身抖毛.mp4',-10)]:
 cam=bpy.data.objects['Cam_'+name].data;cam.show_background_images=True
 if not len(cam.background_images):
  im=bpy.data.images.load(str(root/'Ai videos'/fn),check_existing=True);bg=cam.background_images.new();bg.image=im;bg.alpha=.35;bg.display_depth='BACK';bg.frame_method='FIT';bg.image_user.frame_duration=121;bg.image_user.frame_start=1;bg.image_user.frame_offset=offset;bg.image_user.use_auto_refresh=True;bg.image_user.use_cyclic=True
 cam['reference_video']=fn;cam['reference_note']='正面原時間對照' if name=='front' else '側面為獨立 AI 片，視窗粗對齊 -10 幀；成品對照片使用分階段時間映射'
# Export 96 Hz keys while retaining the editable Blender timeline at 24 fps.
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
# Full render, including the duplicate endpoint to make image equality testable.
for label in ['front','side','threequarter']:
 folder=OUT/'驗證'/('render_'+label);folder.mkdir(exist_ok=True);s.camera=bpy.data.objects['Cam_'+label]
 for fi in range(121):
  s.frame_set(fi+1);s.render.filepath=str(folder/f'{fi:03d}.png');bpy.ops.render.render(write_still=True)
s.frame_set(1);s.camera=bpy.data.objects['Cam_threequarter'];bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False;area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'beagle_shake_loop.blend'))
result={'blend':str(OUT/'beagle_shake_loop.blend'),'glb':str(OUT/'beagle_shake_loop.glb'),'rendered_views':3,'frames_per_view':121,'glb_sample_rate':96,'duration_seconds':5,'preserved_actions':len(bpy.data.actions)}
