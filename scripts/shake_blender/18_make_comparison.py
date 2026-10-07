from pathlib import Path
import json,subprocess,numpy as np,hashlib
from PIL import Image,ImageDraw,ImageFont
from kinematics import *
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',26);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf',20)
D=np.load(ROOT/'工具腳本'/'motion_fit.npz');mapping=np.load(ROOT/'工具腳本'/'side_phase_map.npy');rows=json.loads((ROOT/'驗證'/'正面逐幀量測_raw.json').read_text());side=json.loads((ROOT/'驗證'/'側面逐幀量測.json').read_text())['measurements'];ear_targets=json.loads((ROOT/'驗證'/'耳尖逐幀對位.json').read_text());bg=(136,137,134,255)
def flattened(path):
 im=Image.open(path).convert('RGBA');back=Image.new('RGBA',im.size,bg);back.alpha_composite(im);return back.convert('RGB')
def mark(im,p,color):
 x,y=p;dr=ImageDraw.Draw(im);dr.ellipse((x-6,y-6,x+6,y+6),outline=color,width=3);dr.line((x-10,y,x+10,y),fill=color,width=2);dr.line((x,y-10,x,y+10),fill=color,width=2)
def quad(f,markers=True):
 sf=int(round(mapping[f]));ref=Image.open(ROOT/'參考逐幀'/f'front_{f:03d}.png').convert('RGB');model=flattened(ROOT/'驗證'/'render_front'/f'{f:03d}.png');rs=Image.open(ROOT/'參考逐幀'/f'side_{sf:03d}.png').convert('RGB');ms=flattened(ROOT/'驗證'/'render_side'/f'{f:03d}.png')
 if markers:
  mark(ref,rows[f]['nose'],'#ff4545');S=D['S'][f*4];pred=project([point(S,'nose',NOSE)],D['cam_front'])[0];mark(model,pred,'#35ff9b')
  if rows[f]['eyes']:ImageDraw.Draw(ref).line(sum(rows[f]['eyes'],[]),fill='#49dfff',width=3)
  if side[sf]['nose']:mark(rs,side[sf]['nose'],'#ff4545')
  pred=project([point(S,'nose',NOSE)],D['cam_side'])[0];mark(ms,pred,'#35ff9b')
 canvas=Image.new('RGB',(2560,1520),'#181a1d');draw=ImageDraw.Draw(canvas)
 labels=[f'正面參考影片｜來源 F{f:03d}｜{f/24:.3f} 秒',f'Blender 正面｜F{f+1:03d}｜{f/24:.3f} 秒',f'側面參考影片｜來源 F{sf:03d}｜分階段對齊',f'Blender 側面｜F{f+1:03d}｜原模型骨架']
 for k,im in enumerate([ref,model,rs,ms]):
  x=k%2*1280;y=k//2*760;canvas.paste(im,(x,y+40));draw.text((x+14,y+5),labels[k],font=font,fill='white')
 return canvas
# H.264, native 24 fps reference cadence, one 5-second cycle.
def pipe_encode(path,size,images):
 p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{size[0]}x{size[1]}','-r','24','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
 for im in images:p.stdin.write(np.asarray(im.convert('RGB')).tobytes())
 p.stdin.close();rc=p.wait()
 if rc:raise RuntimeError('ffmpeg failed')
print('encoding comparison',flush=True);pipe_encode(ROOT/'驗證'/'對照_單次Loop.mp4',(2560,1520),(quad(f) for f in range(120)))
subprocess.run(['ffmpeg','-y','-v','error','-stream_loop','2','-i',str(ROOT/'驗證'/'對照_單次Loop.mp4'),'-t','15','-c','copy','-movflags','+faststart',str(ROOT/'對照_正側面_連續三次Loop.mp4')],check=True)
print('encoding model',flush=True);pipe_encode(ROOT/'驗證'/'模型_單次Loop.mp4',(1280,720),(flattened(ROOT/'驗證'/'render_threequarter'/f'{f:03d}.png') for f in range(120)))
subprocess.run(['ffmpeg','-y','-v','error','-stream_loop','2','-i',str(ROOT/'驗證'/'模型_單次Loop.mp4'),'-t','15','-c','copy','-movflags','+faststart',str(ROOT/'預覽_抖毛_連續三次Loop.mp4')],check=True)
for f in [0,24,26,40,60,88,92,98]:quad(f).save(ROOT/'驗證'/f'逐幀對照_F{f:03d}.jpg',quality=92)
# Compact final contact sheet, exact same crop for reference and model.
frames=[0,24,26,32,40,60,80,88,92,98,106,120];sh=Image.new('RGB',(4*500,3*500),'#ddd');dr=ImageDraw.Draw(sh)
for k,f in enumerate(frames):
 ref=Image.open(ROOT/'參考逐幀'/f'front_{f:03d}.png').crop((430,100,800,655));im=flattened(ROOT/'驗證'/'render_front'/f'{f:03d}.png').crop((430,100,800,655));ref=ref.resize((250,375));im=im.resize((250,375));x=k%4*500;y=k//4*500;sh.paste(ref,(x,y+36));sh.paste(im,(x+250,y+36));dr.text((x+8,y+4),f'參考 F{f} ／ Blender F{f+1}',font=small,fill='black');dr.text((x+8,y+420),'左：影片　右：調整後',font=small,fill='black')
sh.save(ROOT/'逐幀對照_正面總覽.jpg',quality=94)
errors=[]
for f in range(121):
 pr=project([point(D['S'][f*4],'nose',NOSE)],D['cam_front'])[0];errors.append(float(np.linalg.norm(pr-np.array(rows[f]['nose']))))
render_seam={}
for view in ['front','side','threequarter']:
 x=np.array(Image.open(ROOT/'驗證'/('render_'+view)/'000.png'));y=np.array(Image.open(ROOT/'驗證'/('render_'+view)/'120.png'));render_seam[view]={'different_channels':int((x!=y).sum()),'max_channel_difference':int(np.abs(x.astype(int)-y.astype(int)).max())}
sourcehash={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT.parent/'beagle.glb',ROOT.parent/'Ai videos'/'全身抖毛_正面.mp4',ROOT.parent/'Ai videos'/'全身抖毛.mp4']}
meta={'source_sha256':sourcehash,'reference_fps':24,'reference_frames_each':121,'loop_seconds':5,'nose_control_point_error_px':{'median':float(np.median(errors)),'max':max(errors),'meaning':'僅鼻尖控制點投影，不代表全輪廓像素相同'},'rendered_seam':render_seam,'phase_map_control_points':{'model_source_frame':[0,22,32,86,98,120],'side_source_frame':[0,12,22,80,90,120]}}
(ROOT/'驗證'/'交付證據摘要.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False,indent=2))
