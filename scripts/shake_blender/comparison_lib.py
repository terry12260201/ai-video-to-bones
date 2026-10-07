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
