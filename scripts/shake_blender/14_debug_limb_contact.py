import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path('__SHAKE_WORK__');r=np.load(O/'工具腳本'/'rig.npz');W=r['W'];V=r['V'];T=r['T'];names=list(r['names']);idx={str(n):i for i,n in enumerate(names)};body=[i for n,i in idx.items() if n.startswith('Spine_') or n=='neck'];bm=W[:,body].sum(1)>.75;BT=T[np.all(bm[T],axis=1)];gs=[idx[f'{n}_f.R'] for n in ['thigh','leg','shin','foot','claws']];lm=W[:,gs].sum(1)>.85;LT=T[np.all(lm[T],axis=1)];s=bpy.context.scene;s.frame_set(27);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();o=bpy.data.objects['Cartoon_Beagle'].evaluated_get(dg);m=o.to_mesh();vv=np.array([o.matrix_world@v.co for v in m.vertices]);o.to_mesh_clear();bvh=BVHTree.FromPolygons([Vector(v) for v in vv],BT.tolist(),all_triangles=True);edges=set()
for tri in LT:
 for u,v in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:edges.add(tuple(sorted([int(u),int(v)])))
hits=[]
for u,v in edges:
 st=Vector(vv[u]);de=Vector(vv[v]-vv[u]);le=de.length
 if le<1e-6:continue
 de.normalize();pt,no,ix,dist=bvh.ray_cast(st+de*.00001,de,max(0,le-.00002))
 if pt is not None and dist>.00002:hits.append({'edge':[u,v],'rest_start':V[u].tolist(),'rest_end':V[v].tolist(),'current_hit':list(pt),'body_triangle':BT[ix].tolist(),'body_rest':V[BT[ix]].tolist(),'weights_start':{n:float(W[u,i]) for n,i in idx.items() if W[u,i]>.05}})
result={'hits':hits}
