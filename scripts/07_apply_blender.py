"""[Blender] 把對位結果寫成骨架動畫（Action）、存 .blend、匯出 .glb，並用同一個攝影機角度算圖。
用法：blender -b --python scripts/07_apply_blender.py"""
import bpy, sys, os, math, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

d = np.load(os.path.join(C.WORK, "final.npz"))
SM = d["S"]; names = [str(n) for n in d["names"]]; cam = d["cam"]; tgt = d["tgt"]; W_, H_ = [int(v) for v in d["size"]]
OUT = os.path.abspath(C.OUT); os.makedirs(os.path.join(OUT, "render"), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(C.GLB))
arm = bpy.data.objects[C.ARMATURE]
for o in bpy.data.objects:                                   # 模型檔裡的雜物不要算進去
    if o.type == "MESH" and o.name != C.MESH: o.hide_render = True; o.hide_viewport = True
sc = bpy.context.scene; sc.render.fps = 24
arm.animation_data_create()
for t in list(arm.animation_data.nla_tracks): t.mute = True
act = bpy.data.actions.new(C.ACTION); arm.animation_data.action = act
rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
F = SM.shape[0]; prevq = {}
for fi in range(F):
    pose = {n: Matrix(SM[fi, i].tolist()) @ rest[n] for i, n in enumerate(names)}
    for n in C.DOF:
        pb = arm.pose.bones[n]; b = pb.bone
        # 把「骨頭在空間中的最終位置」換算回 Blender 要的「相對父骨頭的局部旋轉」
        if b.parent: basis = (rest[b.parent.name].inverted() @ rest[n]).inverted() @ (pose[b.parent.name].inverted() @ pose[n])
        else: basis = rest[n].inverted() @ pose[n]
        loc, q, _ = basis.decompose()
        if n in prevq and prevq[n].dot(q) < 0: q.negate()      # 四元數正負號保持連續，不然中間會轉一大圈
        prevq[n] = q.copy()
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=fi + 1, group=n)
        if n == C.ROOT: pb.location = loc; pb.keyframe_insert("location", frame=fi + 1, group=n)
act.use_frame_range = True; act.frame_start = 1; act.frame_end = F; act.use_cyclic = True; act.use_fake_user = True
sc.frame_start = 1; sc.frame_end = F - 1                      # 最後一格 = 第一格，算圖不用重複

az, el, dist, f, cx, cy = [float(v) for v in cam]
dv = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
cd = bpy.data.cameras.new("Cam_AIVideo"); co = bpy.data.objects.new("Cam_AIVideo", cd); sc.collection.objects.link(co)
co.location = Vector(tgt.tolist()) + dv * dist; co.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
cd.sensor_width = 36; cd.lens = 36 * (f * 2) / W_; cd.shift_x = (W_ / 2 - cx * 2) / W_; cd.shift_y = (cy * 2 - H_ / 2) / W_
sc.camera = co; sc.render.resolution_x = W_; sc.render.resolution_y = H_
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.55
sd = bpy.data.lights.new("Sun", "SUN"); sd.energy = 2.2; so = bpy.data.objects.new("Sun", sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(-15), math.radians(60))
sc.render.engine = "BLENDER_EEVEE"; sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"; sc.view_settings.view_transform = "Standard"
for fr in range(1, F):
    sc.frame_set(fr); sc.render.filepath = os.path.join(OUT, "render", f"r_{fr:03d}.png"); bpy.ops.render.render(write_still=True)

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "walk_loop.blend"))     # .blend 保留模型原本所有動畫
for t in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(t)
for a in list(bpy.data.actions):
    if a != act: bpy.data.actions.remove(a)
sc.frame_end = F                                              # .glb 要含收尾那格，引擎循環才不會少一拍
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "walk_loop.glb"), export_format="GLB", export_animation_mode="ACTIONS", export_frame_range=True, export_force_sampling=True)
print("DONE", C.ACTION, F, "格")
