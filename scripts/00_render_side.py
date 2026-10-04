"""[Blender] 算一張「正側面、素色灰底」的模型圖，拿去當 AI 影片的首幀參考圖。
用法：blender -b --python scripts/00_render_side.py
輸出：output/side_ref.png（16:9，1280×720）"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C

os.makedirs(C.OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(C.GLB))
arm = bpy.data.objects[C.ARMATURE]; me = bpy.data.objects[C.MESH]
for o in bpy.data.objects:
    if o.type == "MESH" and o.name != C.MESH: o.hide_render = True
if arm.animation_data: arm.animation_data.action = None            # 用原始站姿
for t in (arm.animation_data.nla_tracks if arm.animation_data else []): t.mute = True
for pb in arm.pose.bones: pb.matrix_basis.identity()
sc = bpy.context.scene; bpy.context.view_layer.update()

bb = [me.matrix_world @ Vector(c) for c in me.bound_box]
lo = Vector([min(v[i] for v in bb) for i in range(3)]); hi = Vector([max(v[i] for v in bb) for i in range(3)])
ctr = (lo + hi) / 2; length = max(hi.y - lo.y, hi.z - lo.z)
cd = bpy.data.cameras.new("Cam"); co = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(co)
cd.lens = 85; dist = length * 85 / 36 * 1.9                         # 動物佔畫面寬度約一半，四周留空間給牠跨步
az, el = math.radians(6), math.radians(8)                           # 稍微偏一點，讓遠側的腿露出來
dv = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
co.location = ctr + dv * dist; co.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler(); sc.camera = co
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.25, 0.25, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sd = bpy.data.lights.new("Sun", "SUN"); sd.energy = 2.5; so = bpy.data.objects.new("Sun", sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(-15), math.radians(60))
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"
sc.render.filepath = os.path.join(os.path.abspath(C.OUT), "side_ref.png"); bpy.ops.render.render(write_still=True)
print("OK", sc.render.filepath)
