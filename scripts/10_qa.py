"""最後的數字 QA：拿 Blender 算出來的圖（透明度當剪影）跟影片剪影逐格比，再量腳掌有沒有踩在地上。
用法：AV2B_PROJECT=<側面專案> python3 scripts/10_qa.py [正面專案]"""
import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitlib import *
front = sys.argv[1] if len(sys.argv) > 1 else None
M = load_masks(); FR = np.load(os.path.join(C.WORK, "frames_used.npy")); STEP = getattr(C, "STEP", 1)
def iou_dir(rdir, masks, frames):
    out = []
    for k, f in enumerate(frames):
        p = os.path.join(C.OUT, rdir, f"r_{k * STEP + 1:03d}.png")
        if not os.path.exists(p): continue
        a = cv2.imread(p, cv2.IMREAD_UNCHANGED)[..., 3] > 127; m = masks[f] > 0
        out.append((f, (a & m).sum() / max((a | m).sum(), 1)))
    return out
side = iou_dir("render", M, FR); v = np.array([x[1] for x in side])
print(f"側面 剪影重疊率：平均 {v.mean():.3f}｜最低 {v.min():.3f}｜<0.80 的格：{[f for f, x in side if x < 0.8]}")
if front:
    os.environ["AV2B_PROJECT"] = front
    import importlib.util as U
    sp = U.spec_from_file_location("cf", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")); CF = U.module_from_spec(sp); sp.loader.exec_module(CF)
    MF = np.load(os.path.join(CF.WORK, "masks.npy")); FF = np.load(os.path.join(C.WORK, "frames_front.npy"))
    fr = iou_dir("render_cam_front", MF, FF); v2 = np.array([x[1] for x in fr])
    print(f"正面 剪影重疊率：平均 {v2.mean():.3f}｜最低 {v2.min():.3f}｜<0.70 的格：{[f for f, x in fr if x < 0.7]}")
# 腳掌：站姿腳掌 y vs 每格腳掌 y（側面攝影機），超過 12px 就列出
X = np.load(os.path.join(C.WORK, "X_final.npy")); cam = np.load(os.path.join(C.WORK, "cam_cycle.npy")); xs = np.load(os.path.join(C.WORK, "x_stand.npy")); xs = np.r_[xs, np.zeros(NP - len(xs))]
pawW = []
for l in C.LEGS:
    w = sum(W[:, idx[b]] for b in C.PAW_BONES(l)); pawW.append(w / w.sum())
pawW = np.array(pawW); p0 = pawW @ project(pose_verts(xs), cam) / SC
bad = []
for k, x in enumerate(X):
    p = pawW @ project(pose_verts(x), cam) / SC
    d = p[:, 1] - p0[:, 1]
    if np.abs(d).max() > 12: bad.append((int(FR[k]), np.round(d).astype(int).tolist()))
print(f"腳掌離地面線 >12px 的格數：{len(bad)}/{len(X)}", bad[:8])
