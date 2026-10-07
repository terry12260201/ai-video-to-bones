import bpy
p=bpy.ops.export_scene.gltf.get_rna_type().properties
result={'options':{x.identifier:str(x.default) for x in p if any(n in x.identifier for n in ['slide','zero','range'])},'objects':[o.name for o in bpy.data.objects],'actions':[a.name for a in bpy.data.actions if 'Body_Shake' in a.name]}
