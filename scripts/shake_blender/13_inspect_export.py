import bpy
r=bpy.ops.export_scene.gltf.get_rna_type()
result={p.identifier:{'default':str(p.default) if hasattr(p,'default') else None,'enum':[(e.identifier,e.name) for e in p.enum_items] if p.type=='ENUM' else None,'type':p.type} for p in r.properties if any(x in p.identifier for x in ['animation','frame','sampling','selection','nla','optimize'])}
