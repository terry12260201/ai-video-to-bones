import bpy,json
from pathlib import Path
O=Path('__SHAKE_WORK__')
s=bpy.context.scene;a=bpy.data.objects['Arm_Beagle'];act=a.animation_data.action
report={'objects':[o.name for o in s.objects],'actions':[x.name for x in bpy.data.actions],'active_action':act.name,'action_frame_range':list(act.frame_range),'playback_frame_range':[s.frame_start,s.frame_end],'fps':s.render.fps,'bones':len(a.data.bones),'blend_path':bpy.data.filepath}
assert len([o for o in s.objects if o.type=='ARMATURE'])==1
assert len(bpy.data.actions)==28
assert act.name=='Body_Shake_Reference_Loop'
assert list(act.frame_range)==[1,121]
assert [s.frame_start,s.frame_end,s.render.fps]==[1,120,24]
(O/'驗證/Blender交付場景檢查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
# Remove only unused imported data from the round-trip tests; preserve all original actions.
for coll in [bpy.data.meshes,bpy.data.armatures,bpy.data.materials,bpy.data.images]:
 for item in list(coll):
  if item.users==0:coll.remove(item)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(O/'beagle_shake_loop.blend'));result=report
