import bpy,math,json
from mathutils import Vector
from pathlib import Path
OUT=Path('__SHAKE_WORK__')
a=bpy.data.objects['Arm_Beagle'];a.animation_data.action=None
for pb in a.pose.bones:pb.matrix_basis.identity()
bpy.data.objects['Icosphere'].hide_render=True;bpy.data.objects['Icosphere'].hide_viewport=True
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=16;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=70;s.render.fps=24;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard'
w=bpy.data.worlds.new('ReferenceWorld');s.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(1,1,1,1);w.node_tree.nodes['Background'].inputs[1].default_value=.65
ld=bpy.data.lights.new('SoftKey','AREA');lo=bpy.data.objects.new('SoftKey',ld);s.collection.objects.link(lo);lo.location=(-1,-2,3);lo.rotation_euler=(Vector((0,0,.2))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=250;ld.shape='DISK';ld.size=4
for name,loc,target,scale in [('front',(-.15,-2,.75),(0,0,.245),.79),('side',(-2,-.03,.85),(0,0,.245),.82),('threequarter',(-1.3,-1.8,.95),(0,0,.25),.9)]:
 cd=bpy.data.cameras.new('Cam_'+name);co=bpy.data.objects.new('Cam_'+name,cd);s.collection.objects.link(co);co.location=loc;co.rotation_euler=(Vector(target)-co.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=scale;s.camera=co;s.render.filepath=str(OUT/'驗證'/('rest_'+name+'.png'));bpy.ops.render.render(write_still=True)
result={'rendered':['rest_front.png','rest_side.png','rest_threequarter.png']}
