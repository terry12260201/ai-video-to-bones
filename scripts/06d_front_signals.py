"""正面影片 → 直接量「頭側滾、耳朵外飛」寫進對位結果（剪影最佳化讀不準這些，用量的比較可靠）。
量法：每格取剪影最上面 150px 當「頭＋耳朵」帶；頭中心左右偏移 = 側滾，左右最外點超出站姿多少 = 耳朵飛出去多少。
用法：AV2B_PROJECT=<正面專案> python3 scripts/06d_front_signals.py [側滾最大弧度] [耳朵最大弧度] [方向 1|-1]"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitlib import *
from scipy.ndimage import gaussian_filter1d
ROLL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.7; EAR = float(sys.argv[2]) if len(sys.argv) > 2 else 1.3; SGN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
M = np.load(os.path.join(C.WORK, "masks.npy")); FR = np.load(os.path.join(C.WORK, "frames_used.npy")); X = np.load(os.path.join(C.WORK, "X_final.npy"))
cx, L, R = [], [], []
for f in FR:
    m = M[f]; ys, xs = np.where(m); top = ys.min(); by, bx = np.where(m[top:top + 150])
    cx.append(bx.mean()); L.append(bx.min()); R.append(bx.max())
cx, L, R = map(np.array, (cx, L, R)); cx0, L0, R0 = cx[0], L[0], R[0]
roll = SGN * ROLL * np.clip((cx - cx0) / 20, -1, 1)   # 頭中心偏 20px 就當滾到底
earR_img = np.clip((-(L - L0) - 10) / 60, 0, 1)        # 畫面左邊飛出去 = 狗的右耳（狗面對鏡頭）
earL_img = np.clip(((R - R0) - 10) / 60, 0, 1)         # 畫面右邊 = 狗的左耳
sm = lambda a, s=0.7: gaussian_filter1d(a, s, mode="nearest")
roll, earL, earR = sm(roll), sm(earL_img), sm(earR_img)
lag = lambda a, k: np.r_[np.repeat(a[:1], k), a[:-k]] if k > 0 else a
col = {n: DOF.index(n) + 2 for n in DOF}
def put(n, v):
    if n in col: X[:, col[n]] = v
put("head:Y", roll); put("neck:Y", 0.45 * lag(roll, 1)); put("Tail_01:Z", 0.5 * lag(roll, 5))   # 不碰脊椎：腿掛在脊椎下，一滾腳就離地
put("Ear_01.L:Y", -EAR * earL); put("Ear_01.R:Y", EAR * earR); put("Ear_01.L", -0.5 * earL); put("Ear_01.R", -0.5 * earR); put("Ear_01.L:Z", 0); put("Ear_01.R:Z", 0)   # 垂下的耳朵繞 Y 軸才會往外抬
if "head:Z" in col: X[:, col["head:Z"]] = 0                   # 正面影片的轉頭量不可靠，不用
np.save(os.path.join(C.WORK, "X_final.npy"), X)
print("OK 側滾範圍", roll.min().round(2), roll.max().round(2), "｜耳朵 L/R 最大", earL.max().round(2), earR.max().round(2))
