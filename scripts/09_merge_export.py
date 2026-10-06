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

# ── 生命感層：臉、耳朵、舌頭、眼睛從素材包的 Idle_1 借過來 ─────────────────
# 對位只動身體和四肢，臉會死死的。Idle_1 的臉很活，就把它那幾根骨頭的曲線疊到每支新動畫上。
FACE = ["Ear_01.L", "Ear_02.L", "Ear_01.R", "Ear_02.R", "Mouth.L", "Mouth.R", "eye.L", "eye.R",
        "eyelid.L", "eyelid.R", "mouth", "nose", "tongue_1", "tongue_2", "tongue_3", "tongue_4"]
IDLE = os.environ.get("AV2B_FACE_SOURCE", "Idle_1")
def idle_curves():
    a = bpy.data.actions.get(IDLE)
    if not a: return {}, 0
    fcs = list(a.layers[0].strips[0].channelbags[0].fcurves) if a.layers else list(a.fcurves)
    out = {}
    for fc in fcs:
        if '"' not in fc.data_path: continue
        bone = fc.data_path.split('"')[1]
        if bone in FACE: out.setdefault(bone, {}).setdefault(fc.data_path.split(".")[-1], {})[fc.array_index] = fc
    return out, int(a.frame_range[1] - a.frame_range[0])
IDLE_FC, IDLE_LEN = idle_curves()
def face_value(fc, f, L, loop):
    """loop：取 Idle 一段長度 L 的窗，窗尾漸漸混回窗頭前的值，首尾才接得起來；oneshot：照 Idle 自己的週期循環"""
    if loop:
        s0 = max(L, 30); a = (f - 1) / max(L - 1, 1)
        return (1 - a) * fc.evaluate(s0 + f) + a * fc.evaluate(s0 + f - L)
    return fc.evaluate(((f - 1) % IDLE_LEN) + 1)
def add_face_layer(act, last, loop, step, exclude=()):
    if not IDLE_FC: print("  (沒有", IDLE, "，略過生命感層)"); return
    arm.animation_data.action = act
    for f in range(1, last + 1, step):
        for bone, props in IDLE_FC.items():
            if bone in exclude: continue                      # 這支動畫自己有耳朵／嘴巴資料時，不要被 Idle 蓋掉
            pb = arm.pose.bones[bone]
            for prop, idx in props.items():
                vals = [face_value(idx[i], f, last, loop) for i in sorted(idx)]
                if prop == "rotation_quaternion":
                    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = vals
                elif prop == "location": pb.location = vals
                elif prop == "scale": pb.scale = vals
                else: continue
                pb.keyframe_insert(prop, frame=f, group=bone)
    arm.animation_data.action = None

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
        for n in dict.fromkeys(dd.split(':')[0] for dd in C.DOF):
            pb = arm.pose.bones[n]; b = pb.bone
            basis = ((rest[b.parent.name].inverted() @ rest[n]).inverted() @ (pose[b.parent.name].inverted() @ pose[n])) if b.parent else (rest[n].inverted() @ pose[n])
            loc, q, _ = basis.decompose()
            if n in prevq and prevq[n].dot(q) < 0: q.negate()
            prevq[n] = q.copy()
            pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=fi * STEP + 1, group=n)
            if n == C.ROOT: pb.location = loc; pb.keyframe_insert("location", frame=fi * STEP + 1, group=n)
    last = (F - 1) * STEP + 1
    add_face_layer(act, last, LOOP, STEP, exclude=tuple(getattr(C, 'FACE_LAYER_EXCLUDE', ())))
    act.use_frame_range = True; act.frame_start = 1; act.frame_end = last; act.use_cyclic = LOOP; act.use_fake_user = True
    # 推進 NLA，讓匯出器把它當獨立動畫
    tr = arm.animation_data.nla_tracks.new(); tr.name = C.ACTION; tr.strips.new(C.ACTION, 1, act); tr.mute = False
    print("ACTION", C.ACTION, F, "格", "loop" if LOOP else "oneshot", "step", STEP)

for p in projects: build_action(load_cfg(p))
for t in arm.animation_data.nla_tracks: t.mute = False
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "model_all_actions.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "model_all_actions.glb"), export_format="GLB", export_animation_mode="ACTIONS", export_force_sampling=True)
print("DONE", len(bpy.data.actions), "actions")
