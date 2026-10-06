"""[Blender] 把對位結果寫成骨架動畫（Action）、存 .blend、匯出 .glb，並用同一個攝影機角度算圖。
用法：blender -b --python scripts/07_apply_blender.py"""
import bpy, sys, os, math, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

d = np.load(os.path.join(C.WORK, "final.npz"))
LOOP = bool(d["loop"]) if "loop" in d else True; STEP = int(d["step"]) if "step" in d else 1
SM = d["S"]; names = [str(n) for n in d["names"]]; cam = d["cam"]; tgt = d["tgt"]; W_, H_ = [int(v) for v in d["size"]]
RDIR = "render"
if os.environ.get("AV2B_CAM_FILE"):                            # 用另一支影片的攝影機算圖（例如正面），只算圖不存檔
    cam = np.load(os.environ["AV2B_CAM_FILE"]); RDIR = "render_" + os.path.basename(os.environ["AV2B_CAM_FILE"]).split(".")[0]
OUT = os.path.abspath(C.OUT); os.makedirs(os.path.join(OUT, RDIR), exist_ok=True)

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
def frame_no(fi): return fi * STEP + 1
for fi in range(F):
    pose = {n: Matrix(SM[fi, i].tolist()) @ rest[n] for i, n in enumerate(names)}
    for n in dict.fromkeys(d.split(':')[0] for d in C.DOF):   # 去掉軸向後綴、去重
        pb = arm.pose.bones[n]; b = pb.bone
        # 把「骨頭在空間中的最終位置」換算回 Blender 要的「相對父骨頭的局部旋轉」
        if b.parent: basis = (rest[b.parent.name].inverted() @ rest[n]).inverted() @ (pose[b.parent.name].inverted() @ pose[n])
        else: basis = rest[n].inverted() @ pose[n]
        loc, q, _ = basis.decompose()
        if n in prevq and prevq[n].dot(q) < 0: q.negate()      # 四元數正負號保持連續，不然中間會轉一大圈
        prevq[n] = q.copy()
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=frame_no(fi), group=n)
        if n == C.ROOT: pb.location = loc; pb.keyframe_insert("location", frame=frame_no(fi), group=n)
LAST = frame_no(F - 1)
act.use_frame_range = True; act.frame_start = 1; act.frame_end = LAST; act.use_cyclic = LOOP; act.use_fake_user = True
sc.frame_start = 1; sc.frame_end = (LAST - 1) if LOOP else LAST   # 循環：最後一格 = 第一格，算圖不用重複

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
for fr in range(1, sc.frame_end + 1):
    sc.frame_set(fr); sc.render.filepath = os.path.join(OUT, RDIR, f"r_{fr:03d}.png"); bpy.ops.render.render(write_still=True)

if os.environ.get("AV2B_CAM_FILE"): print("DONE render only", RDIR); raise SystemExit
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "walk_loop.blend"))     # .blend 保留模型原本所有動畫
sc.frame_end = LAST
if os.environ.get("AV2B_EXPORT_ALL"):                         # 連同模型原本的動畫一起匯出一顆「全動畫」GLB
    for t in arm.animation_data.nla_tracks: t.mute = False
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "model_all_actions.glb"), export_format="GLB", export_animation_mode="ACTIONS", export_force_sampling=True)
for t in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(t)
for a in list(bpy.data.actions):
    if a != act: bpy.data.actions.remove(a)                                              # .glb 要含收尾那格，引擎循環才不會少一拍
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "walk_loop.glb"), export_format="GLB", export_animation_mode="ACTIONS", export_frame_range=True, export_force_sampling=True)
print("DONE", C.ACTION, F, "格")
