from pathlib import Path
import json,struct,hashlib,numpy as np
O=Path(__file__).resolve().parents[1]  # 工作資料夾＝工具腳本/ 的上一層
b=(O/'beagle_shake_loop.glb').read_bytes();magic,version,length=struct.unpack_from('<III',b,0);assert magic==0x46546c67 and version==2 and length==len(b)
n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);blen,btype=struct.unpack_from('<II',b,20+n);binary=b[28+n:28+n+blen];assert btype==0x004e4942
sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};types={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}
def data(i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];off=v.get('byteOffset',0)+a.get('byteOffset',0);dtype=np.dtype(types[a['componentType']]);cols=sizes[a['type']];stride=v.get('byteStride',dtype.itemsize*cols);return np.ndarray((a['count'],cols),dtype=dtype,buffer=binary,offset=off,strides=(stride,dtype.itemsize))
assert len(d['animations'])==1;anim=d['animations'][0];seams=[];times=[]
for c in anim['channels']:
 sampler=anim['samplers'][c['sampler']];t=data(sampler['input']).ravel();v=data(sampler['output']);assert np.isfinite(v).all() and np.isfinite(t).all();assert t[0]==0 and abs(float(t[-1])-5)<1e-6;assert len(t)==481 and np.all(np.diff(t)>0)
 path=c['target']['path'];err=min(float(abs(v[-1]-v[0]).max()),float(abs(v[-1]+v[0]).max())) if path=='rotation' else float(abs(v[-1]-v[0]).max());assert err<1e-6;seams.append({'node':d['nodes'][c['target']['node']].get('name'),'path':path,'max_endpoint_difference':err});times.append(float(abs(np.diff(t)-1/96).max()))
r={'animation':anim['name'],'channels':len(anim['channels']),'samples_per_channel':481,'start_seconds':0,'end_seconds':5,'sample_rate_hz':96,'max_first_last_channel_difference':max(x['max_endpoint_difference'] for x in seams),'finite_values':True,'channels_detail':seams};(O/'驗證/GLB結構與Loop驗證.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
summary=json.loads((O/'驗證/交付證據摘要.json').read_text());src=O.parent
for name,path in [('beagle.glb',src/'beagle.glb'),('全身抖毛_正面.mp4',src/'Ai videos/全身抖毛_正面.mp4'),('全身抖毛.mp4',src/'Ai videos/全身抖毛.mp4')]:assert hashlib.sha256(path.read_bytes()).hexdigest()==summary['source_sha256'][name]
summary['source_hashes_reverified_unchanged']=True;summary['glb_roundtrip']=json.loads((O/'驗證/GLB重新匯入驗證.json').read_text());summary['glb_roundtrip'].pop('records');summary['glb_structure']={k:v for k,v in r.items() if k!='channels_detail'};summary['deliverable_sha256']={x:hashlib.sha256((O/x).read_bytes()).hexdigest() for x in ['beagle_shake_loop.blend','beagle_shake_loop.glb','對照_正側面_連續三次Loop.mp4','預覽_抖毛_連續三次Loop.mp4']};summary['comparison_frame_count']=len(list((O/'對照逐幀').glob('F*.jpg')));assert summary['comparison_frame_count']==121
(O/'驗證/交付證據摘要.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='channels_detail'},ensure_ascii=False));print('Source hashes unchanged; 121 comparison images; final hashes recorded.')
