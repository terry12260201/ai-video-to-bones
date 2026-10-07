import bpy,json
from pathlib import Path
SRC='__SHAKE_PROJECT__/beagle.glb'
OUT=Path('__SHAKE_WORK__')
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=SRC)
a=bpy.data.objects['Arm_Beagle']
for t in a.animation_data.nla_tracks:t.mute=True
a.animation_data.action=None
bpy.context.view_layer.update()
report={'blender':bpy.app.version_string,'objects':[{'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'bounds':[list(c) for c in o.bound_box]} for o in bpy.data.objects],'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local],'constraints':[{'name':c.name,'type':c.type} for c in a.pose.bones[b.name].constraints]} for b in a.data.bones],'actions':[{'name':x.name,'range':list(x.frame_range)} for x in bpy.data.actions]}
(OUT/'驗證'/'骨架檢查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
result=report
