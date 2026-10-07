from pathlib import Path
import cv2,numpy as np,json,itertools
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'參考逐幀'
rows=[]
for f in range(121):
 im=cv2.imread(str(D/f'front_{f:03d}.png'));b,g,r=im.astype(float).transpose(2,0,1);gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
 mask=(gray<35).astype('uint8');mask[:230]=0;mask[490:]=0;mask[:,:510]=0;mask[:,720:]=0
 n,lab,st,ce=cv2.connectedComponentsWithStats(mask)
 cand=[]
 for i in range(1,n):
  x,y,w,h,area=st[i];cx,cy=ce[i]
  if area<130 or area>1400 or w>53 or h>54 or w<14 or h<10:continue
  ring=im[max(0,y-3):y+h+3,max(0,x-3):x+w+3].astype(float);white=np.mean(np.min(ring,axis=2)>155)
  cand.append((white*200+min(area,900)*.12+cy*.10,i))
 if not cand:raise RuntimeError(f'No nose {f}')
 i=max(cand)[1];nose=ce[i];nx,ny=nose
 mask=(gray<62).astype('uint8');mask[:int(max(170,ny-85))]=0;mask[int(ny+12):]=0;mask[:,:int(nx-80)]=0;mask[:,int(nx+90):]=0
 n,lab,st,ce=cv2.connectedComponentsWithStats(mask);eyes=[]
 for j in range(1,n):
  x,y,w,h,area=st[j];cx,cy=ce[j]
  if 25<area<650 and 6<w<39 and 3<h<32 and (np.linalg.norm(ce[j]-nose)>21):eyes.append((j,ce[j],area))
 pairs=[]
 for e1,e2 in itertools.combinations(eyes,2):
  if e1[1][0]>e2[1][0]:e1,e2=e2,e1
  v=e2[1]-e1[1];dist=np.linalg.norm(v);mid=(e1[1]+e2[1])/2
  if not 28<dist<85 or v[0]<23 or not 12<ny-mid[1]<65:continue
  score=abs(dist-55)*.3+abs((ny-mid[1])-36)*.3+abs(mid[0]-nx)*.05- min(e1[2],e2[2])*.005
  pairs.append((score,e1[1],e2[1]))
 if pairs:_,e1,e2=min(pairs,key=lambda x:x[0]);roll=float(np.arctan2(*(e2-e1)[::-1]));eyes=[e1.tolist(),e2.tolist()]
 else:roll=None;eyes=[]
 # planted front paws from white/low-saturation foreground, not grey background
 mask=((r>155)&(g>155)&(b>145)&(np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b])<45)).astype('uint8');mask[:480]=0;mask[630:]=0;mask[:,:510]=0;mask[:,735:]=0
 n,lab,st,ce=cv2.connectedComponentsWithStats(mask);paws=[]
 for j in range(1,n):
  x,y,w,h,area=st[j]
  if area>250 and y+h>570:
   yy,xx=np.where((lab==j)&(np.indices(lab.shape)[0]>y+h-15));paws.append([float(np.mean(xx)),float(y+h-1)])
 paws=sorted(paws)
 # pink visible tongue area (surface visibility, not hidden 3D data)
 pink=((r>80)&(r>g*1.17)&(b>g*.88)&(r>b*1.10)).astype('uint8');pink[:int(ny+9)]=0;pink[int(ny+75):]=0;pink[:,:int(nx-35)]=0;pink[:,int(nx+45):]=0
 rows.append({'frame':f,'time':f/24,'nose':nose.tolist(),'eyes':eyes,'head_roll_rad':roll,'front_paws':paws,'tongue_visible_pixels':int(pink.sum())})
(ROOT/'驗證'/'正面逐幀量測_raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
ids=list(range(0,121,3));w=230;h=310;sh=Image.new('RGB',(7*w,6*h),'#ddd')
for k,f in enumerate(ids):
 im=Image.open(D/f'front_{f:03d}.png');dr=ImageDraw.Draw(im);row=rows[f]
 for point in [row['nose']]+row['eyes']+row['front_paws']:
  x,y=point;dr.ellipse((x-5,y-5,x+5,y+5),outline='red',width=2)
 if row['eyes']:dr.line(row['eyes'][0]+row['eyes'][1],fill='cyan',width=2)
 im=im.crop((470,120,780,640));im.thumbnail((w,h-22));x=k%7*w;y=k//7*h;sh.paste(im,(x,y));ImageDraw.Draw(sh).text((x+4,y+h-20),f'F{f} roll {round(row["head_roll_rad"]*180/np.pi) if row["head_roll_rad"] is not None else "?"}',fill='black')
sh.save(ROOT/'驗證'/'量測標記_正面.jpg')
print('measured',len(rows),'eye_missing',[r['frame'] for r in rows if r['head_roll_rad'] is None])
for f in range(0,121,4):print(f,rows[f]['nose'],rows[f]['head_roll_rad'],rows[f]['front_paws'],rows[f]['tongue_visible_pixels'])
