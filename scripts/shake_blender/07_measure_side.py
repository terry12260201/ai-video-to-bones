from kinematics import *
from scipy.optimize import least_squares
import cv2,json
from PIL import Image,ImageDraw
# Match neutral side camera using source nose, visible front/rear paw and spine saddle top.
p=np.array([NOSE,PAWS['foot_f.L'],PAWS['foot_b.L'],H[idx['Spine_03']]+[.001,0,.035]])
t=np.array([[313,215],[480,564],[784,573],[593,253]])
opt=least_squares(lambda c:(project(p,c)-t).ravel(),[0,.18,900,640,340],bounds=([-.15,.04,780,580,270],[.15,.40,1100,720,420]),loss='soft_l1',f_scale=8);cam=opt.x
rows=[]
for f in range(121):
 im=cv2.imread(str(ROOT/'參考逐幀'/f'side_{f:03d}.png'));gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);mask=(gray<36).astype('uint8');mask[:150]=0;mask[390:]=0;mask[:,:275]=0;mask[:,470:]=0;n,lab,st,ce=cv2.connectedComponentsWithStats(mask)
 cand=[i for i in range(1,n) if 30<st[i,4]<1000 and st[i,2]<52 and st[i,3]<60]
 ni=min(cand,key=lambda i:ce[i,0]) if cand else None;nose=ce[ni].tolist() if ni else None
 # central torso top/bottom foreground edges in a fixed band; background is neutral grey.
 b,g,r=im.astype(float).transpose(2,0,1);fg=((np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b]))>18)|((r>160)&(g>160)&(b>150));fg[:150]=False;fg[470:]=False;yy,xx=np.where(fg[:,570:640]);bounds=[int(np.percentile(yy,1)),int(np.percentile(yy,99))] if len(yy) else None
 # foot support: lowest foreground pixels per front/rear region.
 paws=[]
 for lo,hi in [(360,560),(680,855)]:
  white=(r>145)&(g>145)&(b>135)&((np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b]))<50);white[:480]=False;white[630:]=False;white[:,:lo]=False;white[:,hi:]=False;n2,l2,s2,c2=cv2.connectedComponentsWithStats(white.astype('uint8'));cs=[i for i in range(1,n2) if s2[i,4]>100]
  if cs:
   i=max(cs,key=lambda i:s2[i,1]+s2[i,3]);y=s2[i,1]+s2[i,3]-1;ys,xs=np.where((l2==i)&(np.indices(l2.shape)[0]>y-12));paws.append([float(xs.mean()),int(y)])
  else:paws.append(None)
 rows.append({'frame':f,'time':f/24,'nose':nose,'torso_vertical_bounds':bounds,'front_rear_paws':paws})
(ROOT/'驗證'/'側面逐幀量測.json').write_text(json.dumps({'camera':cam.tolist(),'neutral_errors_px':np.linalg.norm(project(p,cam)-t,axis=1).tolist(),'measurements':rows},ensure_ascii=False,indent=2))
# Map motion phases; the clips are independent generated takes, not synchronous cameras.
map_side=np.interp(np.arange(121),[0,22,32,86,98,120],[0,12,22,80,90,120]);np.save(ROOT/'工具腳本'/'side_phase_map.npy',map_side)
# [2026-10-07 修正] 歷史版這裡會把 cam_side 追加進既有 motion_fit.npz，從零重建時造成相依循環＋重複 keyword。
# 05_fit_motion.py 已會從 側面逐幀量測.json 讀相機存進 NPZ，所以拿掉。
sh=Image.new('RGB',(4*384,7*244),'#ddd');dr=ImageDraw.Draw(sh)
for k,f in enumerate(range(0,121,5)):
 im=Image.open(ROOT/'參考逐幀'/f'side_{f:03d}.png');draw=ImageDraw.Draw(im);row=rows[f]
 for pt in [row['nose']]+row['front_rear_paws']:
  if pt:x,y=pt;draw.ellipse((x-5,y-5,x+5,y+5),outline='red',width=3)
 if row['torso_vertical_bounds']:
  for y in row['torso_vertical_bounds']:draw.line((570,y,640,y),fill='cyan',width=3)
 im.thumbnail((384,216));x=k%4*384;y=k//4*244;sh.paste(im,(x,y));dr.text((x+5,y+218),f'Side F{f} / {f/24:.3f}s',fill='black')
sh.save(ROOT/'驗證'/'量測標記_側面.jpg');print('SIDE_CAM',cam)
