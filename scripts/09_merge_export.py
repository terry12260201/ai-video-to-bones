"""[Blender] 把多個專案的對位結果一起寫進同一顆模型：原本的動畫 ＋ 每支新動畫，存 .blend、匯出 .glb。
用法：blender -b --python scripts/09_merge_export.py -- walk trot run eat drink
輸出：output/merged/model_all_actions.glb、model_all_actions.blend"""
import bpy, sys, os, numpy as np
from mathutils import Matrix
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib.util as U
projects = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath("output/merged"); os.makedirs(OUT, exist_ok=True)

def load_cfg(name):
    os.environ["AV2B_PROJECT"] = name
    spec = U.spec_from_file_location(f"config_{name}", os.path.join(HERE, "config.py")); m = U.module_from_spec(spec); spec.loader.exec_module(m); return m

C0 = load_cfg(projects[0])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(C0.GLB))
arm = bpy.data.objects[C0.ARMATURE]
arm.animation_data_create()
rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
base_actions = set(a.name for a in bpy.data.actions)

def build_action(C):
    d = np.load(os.path.join(C.WORK, "final.npz")); SM = d["S"]; names = [str(n) for n in d["names"]]
    LOOP = bool(d["loop"]) if "loop" in d else True; STEP = int(d["step"]) if "step" in d else 1
    old = bpy.data.actions.get(C.ACTION)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(C.ACTION); arm.animation_data.action = act
    for pb in arm.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    prevq = {}; F = SM.shape[0]
    for fi in range(F):
        pose = {n: Matrix(SM[fi, i].tolist()) @ rest[n] for i, n in enumerate(names)}
        for n in C.DOF:
            pb = arm.pose.bones[n]; b = pb.bone
            basis = ((rest[b.parent.name].inverted() @ rest[n]).inverted() @ (pose[b.parent.name].inverted() @ pose[n])) if b.parent else (rest[n].inverted() @ pose[n])
            loc, q, _ = basis.decompose()
            if n in prevq and prevq[n].dot(q) < 0: q.negate()
            prevq[n] = q.copy()
            pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=fi * STEP + 1, group=n)
            if n == C.ROOT: pb.location = loc; pb.keyframe_insert("location", frame=fi * STEP + 1, group=n)
    last = (F - 1) * STEP + 1
    act.use_frame_range = True; act.frame_start = 1; act.frame_end = last; act.use_cyclic = LOOP; act.use_fake_user = True
    # 推進 NLA，讓匯出器把它當獨立動畫
    tr = arm.animation_data.nla_tracks.new(); tr.name = C.ACTION; tr.strips.new(C.ACTION, 1, act); tr.mute = False
    arm.animation_data.action = None
    print("ACTION", C.ACTION, F, "格", "loop" if LOOP else "oneshot", "step", STEP)

for p in projects: build_action(load_cfg(p))
for t in arm.animation_data.nla_tracks: t.mute = False
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "model_all_actions.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "model_all_actions.glb"), export_format="GLB", export_animation_mode="ACTIONS", export_force_sampling=True)
print("DONE", len(bpy.data.actions), "actions")
