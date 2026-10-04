"""對位核心：用 numpy 自己做蒙皮（骨頭帶動外皮）＋投影＋畫剪影，不用每比一次就開 Blender 算圖。"""
import cv2, numpy as np, os
import scipy.sparse as sp
import config as C

rig = np.load(os.path.join(C.WORK, "rig.npz"))
V = rig["V"]; T = rig["T"]; W = rig["W"].astype(np.float64)
names = [str(n) for n in rig["names"]]; parents = rig["parents"]; heads = rig["heads"]
NB = len(names); idx = {n: i for i, n in enumerate(names)}
DOF = C.DOF; NP = 2 + len(DOF)            # 參數 = 身體根的前後、上下平移 + 每根骨頭一個角度
dof_bone = [idx[n] for n in DOF]
Vh = np.c_[V, np.ones(len(V))]
BW = sp.csr_matrix((W[:, :, None] * Vh[:, None, :]).reshape(len(V), -1))   # 稀疏矩陣：蒙皮快 100 倍
TGT = (V.min(0) + V.max(0)) / 2           # 攝影機看向模型中心
SC = 0.5                                  # 用半解析度比對，快 4 倍
_m = np.load(os.path.join(C.WORK, "masks.npy"), mmap_mode="r")
FH, FW = _m.shape[1:]; HW = (int(FH * SC), int(FW * SC))

def rotx(h, a):
    """繞著通過 h 點的左右軸（X）轉 a 弧度"""
    c, s = np.cos(a), np.sin(a); M = np.eye(4); M[1:3, 1:3] = [[c, -s], [s, c]]
    M[:3, 3] = h - M[:3, :3] @ h; return M

def skin_mats(x):
    """參數 → 每根骨頭的「相對原始姿勢的變換矩陣」（父骨頭帶著子骨頭一起動）"""
    ang = np.zeros(NB); ang[dof_bone] = x[2:]
    Sm = np.zeros((NB, 4, 4))
    for b in range(NB):                                   # 骨頭清單本來就是父在前
        P = Sm[parents[b]] if parents[b] >= 0 else np.eye(4)
        M = rotx(heads[b], ang[b]) if ang[b] != 0 else np.eye(4)
        if names[b] == C.ROOT:
            Tm = np.eye(4); Tm[1, 3] = x[0] * 0.1; Tm[2, 3] = x[1] * 0.1; M = Tm @ M
        Sm[b] = P @ M
    return Sm

def pose_verts(x):
    Sm = skin_mats(x)
    return np.stack([BW @ Sm[:, i, :].reshape(-1) for i in range(3)], 1)

def project(P, cam):
    """透視投影。cam = 方位角、仰角、距離、焦距(px)、畫面中心 x、y（半解析度）"""
    az, el, dist, f, cx, cy = cam
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    Cc = TGT + d * dist; fw = -d; rt = np.cross(fw, [0, 0, 1]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
    Q = P - Cc; z = Q @ fw
    return np.c_[cx + f * (Q @ rt) / z, cy - f * (Q @ up) / z]

def raster(p2):
    """精確剪影（慢，驗收用）"""
    m = np.zeros(HW, np.uint8)
    for q in np.round(p2[T] * 16).astype(np.int32): cv2.fillConvexPoly(m, q, 1, shift=4)
    return m

_ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
def fast_mask(p2):
    """快速剪影（對位用）：把頂點、三角形中心、邊中點灑成點，再把點之間的縫補起來"""
    q = np.vstack([p2, p2[T].mean(1), (p2[T[:, 0]] + p2[T[:, 1]]) / 2])
    xi = np.clip(np.round(q[:, 0]).astype(int), 0, HW[1] - 1); yi = np.clip(np.round(q[:, 1]).astype(int), 0, HW[0] - 1)
    m = np.zeros(HW, np.uint8); m[yi, xi] = 1
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, _ker)

def bil(img, p):
    return cv2.remap(img, p[:, 0].astype(np.float32)[None], p[:, 1].astype(np.float32)[None], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)[0]

class Target:
    """一格影片的剪影，預先算好「離剪影多遠」的距離圖"""
    def __init__(s, mask):
        m = cv2.resize(mask.astype(np.uint8), (HW[1], HW[0]), interpolation=cv2.INTER_AREA)
        s.m = m; s.dt = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
        ys, xs = np.where(m); sel = np.arange(len(xs))[::17]; pts = np.c_[xs[sel], ys[sel]].astype(np.float32)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=len)[:, 0, :][::3].astype(np.float32)
        s.pts = np.vstack([pts, c, c])                    # 輪廓點放兩份 = 邊緣比內部重要

VS = np.arange(len(V))[::4]
def sil_resid(p2, tg):
    """剪影誤差，兩個方向都要算：①模型跑出影片剪影外多遠 ②影片剪影有多少沒被模型蓋到"""
    r1 = bil(tg.dt, p2[VS])
    mm = fast_mask(p2); r2 = bil(cv2.distanceTransform(1 - mm, cv2.DIST_L2, 5), tg.pts)
    return np.r_[r1 / np.sqrt(len(r1)), r2 / np.sqrt(len(r2))] * 10

def iou(a, b): return (a & b).sum() / max((a | b).sum(), 1)
def load_masks(): return np.load(os.path.join(C.WORK, "masks.npy"))
