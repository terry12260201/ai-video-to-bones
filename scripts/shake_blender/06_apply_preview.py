import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Matrix,Vector
OUT=Path('__SHAKE_WORK__');d=np.load(OUT/'工具腳本'/'motion_fit.npz');S=d['S'];names=[str(n) for n in d['names']];F=len(S)
a=bpy.data.objects['Arm_Beagle'];a.location.z=float(d['floor_shift']);a.animation_data_create()
for tr in a.animation_data.nla_tracks:tr.mute=True
old=bpy.data.actions.get('Body_Shake')
if old:old.name='Body_Shake_Original';old.use_fake_user=True
prev=bpy.data.actions.get('Body_Shake_Reference_Loop')
if prev:bpy.data.actions.remove(prev)
act=bpy.data.actions.new('Body_Shake_Reference_Loop');a.animation_data.action=act;rest={b.name:b.matrix_local.copy() for b in a.data.bones};prevq={}
for pb in a.pose.bones:pb.matrix_basis=Matrix.Identity(4);pb.rotation_mode='QUATERNION'
for fi in range(F):
 ti=float(d['frame_times'][fi]);fr=ti+1
 pose={n:Matrix(S[fi,i].tolist())@rest[n] for i,n in enumerate(names)}
 for n in names:
  pb=a.pose.bones[n];b=pb.bone
  basis=(rest[b.parent.name].inverted()@rest[n]).inverted()@(pose[b.parent.name].inverted()@pose[n]) if b.parent else rest[n].inverted()@pose[n]
  loc,q,sc=basis.decompose()
  if n in prevq and prevq[n].dot(q)<0:q.negate()
  prevq[n]=q.copy();pb.rotation_quaternion=q;pb.location=loc if n=='Spine_base' else (0,0,0);pb.scale=(1,1,1)
  if n=='tongue_1':
   env=float(d['tongue_retraction'][fi]) if 22<=ti<=105 else 0;pb.scale.y=1-.72*env
  pb.keyframe_insert('rotation_quaternion',frame=fr,group=n)
  if n=='Spine_base':pb.keyframe_insert('location',frame=fr,group=n)
  if n=='tongue_1':pb.keyframe_insert('scale',frame=fr,group=n)
act.use_frame_range=True;act.frame_start=1;act.frame_end=121;act.use_cyclic=True;act.use_fake_user=True
# Linear dense keys avoid overshoot between measured video frames.
curves=[]
for layer in act.layers:
 for strip in layer.strips:
  for slot in act.slots:
   bag=strip.channelbag(slot)
   if bag:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
     mod=fc.modifiers.new('CYCLES');mod.mode_before='REPEAT';mod.mode_after='REPEAT';curves.append(fc)
s=bpy.context.scene;s.frame_start=1;s.frame_end=121;s.render.fps=24
az,el,scale,cx,cy=d['cam_front'];target=Vector((0,0,.25));dv=Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)));cam=bpy.data.objects['Cam_front'];cam.location=target+dv*2;cam.rotation_euler=(-dv).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1280/scale;cam.data.shift_x=-(cx-640)/1280;cam.data.shift_y=(cy-360)/1280
az,el,scale,cx,cy=d['cam_side'];dv=Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)));cam=bpy.data.objects['Cam_side'];cam.location=target+dv*2;cam.rotation_euler=(-dv).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1280/scale;cam.data.shift_x=-(cx-640)/1280;cam.data.shift_y=(cy-360)/1280
# Softer reference-like lighting.
bpy.data.lights['SoftKey'].energy=70;s.view_settings.exposure=-.3;s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for label in ['front','side','threequarter']:
 (OUT/'驗證'/('preview_'+label)).mkdir(exist_ok=True)
 s.camera=bpy.data.objects['Cam_'+label]
 for fi in [0,24,26,28,32,40,52,60,72,80,88,92,98,120]:
  s.frame_set(fi+1);s.render.filepath=str(OUT/'驗證'/('preview_'+label)/f'{fi:03d}.png');bpy.ops.render.render(write_still=True)
s.frame_set(1);s.camera=bpy.data.objects['Cam_threequarter'];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'beagle_shake_loop.blend'))
result={'action':act.name,'frames':F,'fcurves':len(curves),'saved':str(OUT/'beagle_shake_loop.blend')}
