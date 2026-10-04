"""找出「走一圈要幾格」以及「從哪一格開始接得最順」。
做法：拿每一格的剪影跟 N 格之後的剪影比重疊率，重疊率最高的 N 就是週期。
用法：python scripts/03_find_cycle.py"""
import numpy as np, os
import config as C

M = np.load(os.path.join(C.WORK, "masks.npy")); n = len(M)
iou = lambda a, b: (a & b).sum() / (a | b).sum()
s0 = n // 4                                    # 跳過開頭（通常是站著、起步）
best = []
for lag in range(8, min(60, n - s0 - 1)):
    v = np.mean([iou(M[k], M[k + lag]) for k in range(s0, n - lag, 2)]); best.append((v, lag))
best.sort(reverse=True)
print("週期候選（重疊率, 格數）：", [(round(float(v), 3), l) for v, l in best[:4]])
lag = min(l for v, l in best[:3] if v > best[0][0] - 0.06)   # 取最短的那個（其他是它的倍數）
st = sorted([(iou(M[a], M[a + lag]), a) for a in range(s0, n - lag)], reverse=True)[:5]
print(f"建議 CYCLE_LEN = {lag}")
print("建議 CYCLE_START（首尾重疊率, 起始格）：", [(round(float(v), 3), a) for v, a in st])
