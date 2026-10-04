"""[Blender] 把模型的頂點、三角面、權重、骨架匯出成 rig.npz，後面的對位程式就不用再開 Blender。
用法：blender -b --python scripts/01_export_rig.py"""
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

os.makedirs(C.WORK, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(C.GLB))
arm = bpy.data.objects[C.ARMATURE]; me = bpy.data.objects[C.MESH]
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

bones = list(arm.data.bones); names = [b.name for b in bones]
parents = [names.index(b.parent.name) if b.parent else -1 for b in bones]
heads = np.array([b.head_local[:] for b in bones])
mw = np.array(me.matrix_world)
V = np.array([v.co[:] for v in me.data.vertices]); V = (mw[:3, :3] @ V.T).T + mw[:3, 3]
me.data.calc_loop_triangles()
T = np.array([t.vertices[:] for t in me.data.loop_triangles])
W = np.zeros((len(V), len(names)), dtype=np.float32)
vg = {g.index: g.name for g in me.vertex_groups}
for v in me.data.vertices:
    for g in v.groups:
        n = vg[g.group]
        if n in names: W[v.index, names.index(n)] = g.weight
W /= W.sum(1, keepdims=True)
np.savez(os.path.join(C.WORK, "rig.npz"), V=V, T=T, W=W, names=np.array(names), parents=np.array(parents), heads=heads)
print(f"OK rig.npz：{len(V)} 頂點、{len(T)} 三角面、{len(names)} 根骨頭")
