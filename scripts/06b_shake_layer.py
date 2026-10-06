"""抖毛專用的「甩動層」：側面剪影看不出頭左右側滾、耳朵外甩，這些從影片讀出節奏後用程式補上去。
用法：AV2B_PROJECT=shake python3 scripts/06b_shake_layer.py <影片開始甩的格> <停止甩的格> [週期格數]
會改寫 work/<p>/X_final.npy 裡 head:Y／neck:Y／Spine:Y／Ear:Z／Tail:Z 這幾欄，其餘保留對位結果。"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitlib import *
f0, f1 = int(sys.argv[1]), int(sys.argv[2]); period = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
X = np.load(os.path.join(C.WORK, "X_final.npy")); FR = np.load(os.path.join(C.WORK, "frames_used.npy"))
col = {n: DOF.index(n) + 2 for n in DOF}
t = np.array(FR, float); phase = 2 * np.pi * (t - f0) / period
# 包絡：4 格起、中段全力、最後 12 格收
env = np.clip((t - f0) / 4, 0, 1) * np.clip((f1 - t) / 12, 0, 1); env[t < f0] = 0; env[t > f1] = 0
def put(n, v):
    if n in col: X[:, col[n]] = v
put("head:Y",      0.85 * env * np.sin(phase))                 # 頭左右側滾（最大）
put("neck:Y",      0.35 * env * np.sin(phase - 0.6))           # 脖子跟著，晚一點
put("Spine_05:Y",  0.22 * env * np.sin(phase - 1.2))           # 波浪往後傳
put("Spine_03:Y",  0.16 * env * np.sin(phase - 1.8))
put("Spine_base:Y",0.10 * env * np.sin(phase - 2.4))
put("Tail_01:Z",   0.50 * env * np.sin(phase - 2.8))           # 尾巴最後甩
flap = env * np.abs(np.sin(phase))                              # 耳朵：每次甩到底就往外飛
put("Ear_01.L:Z",  1.3 * flap); put("Ear_01.R:Z", -1.3 * flap)
put("Ear_01.L:Y",  0.4 * env * np.sin(phase)); put("Ear_01.R:Y", 0.4 * env * np.sin(phase))
put("Ear_01.L",   -0.6 * flap); put("Ear_01.R", -0.6 * flap)   # 同時往上翹
# 轉頭（head:Z）保留對位值但壓一半，別一直盯鏡頭
if "head:Z" in col: X[:, col["head:Z"]] *= 0.5
np.save(os.path.join(C.WORK, "X_final.npy"), X)
print("OK 甩動層", f0, "→", f1, "週期", period, "格；影響", int(env.sum()), "格")
