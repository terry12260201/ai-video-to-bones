from comparison_lib import *
p=ROOT/'對照逐幀';p.mkdir(exist_ok=True)
for f in range(121):quad(f).save(p/f'F{f:03d}.jpg',quality=92)
print('Saved 121 source/model proof frames')
