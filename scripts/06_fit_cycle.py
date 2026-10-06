"""主角：把一個循環的每一格，骨架對到影片上。
誤差 = 剪影差 + 腳掌離手標點多遠 + 幾條「常識」（關節範圍、落地腳掌放平、左右腳差半圈、前後格要連續）
用法：python scripts/06_fit_cycle.py"""
import os, time
from scipy.optimize import least_squares
from fitlib import *

M = load_masks(); cam = np.load(os.path.join(C.WORK, "cam.npy")); xs = np.load(os.path.join(C.WORK, "x_stand.npy"))
A0, N, legs = C.CYCLE_START, C.CYCLE_LEN, C.LEGS
di = {n: i + 2 for i, n in enumerate(DOF)}
pawW = []
for l in legs:
    w = sum(W[:, idx[b]] for b in C.PAW_BONES(l)); pawW.append(w / w.sum())
pawW = np.array(pawW)
lo = np.full(NP, C.DEFAULT_LIMIT[0]); hi = np.full(NP, C.DEFAULT_LIMIT[1])
for n, i in di.items():
    if n.startswith("Tail"): lo[i], hi[i] = C.TAIL_LIMIT
    if n in C.LIMITS: lo[i], hi[i] = C.LIMITS[n]
    elif n[:-2] in C.LIMITS: lo[i], hi[i] = C.LIMITS[n[:-2]]
chain = {l: [di[n] for n in C.leg_chain(l) if n in di] for l in legs}
footidx = [di[f"foot_{l}"] for l in legs]
Lidx = [i for n, i in di.items() if n.endswith(".L")]; Ridx = [di[n[:-1] + "R"] for n, i in di.items() if n.endswith(".L")]

def prior(z, kp):
    out = [z[footidx] * 0.5]                                # 腳趾別亂翻
    for i, l in enumerate(legs):                            # 踩在地上的腳掌要放平（整條鏈的角度加起來 = 0）
        if kp[i][1] >= C.GROUND_Y[l] and len(kp[i]) == 2: out.append([z[chain[l]].sum() * 2.0])
    return np.concatenate(out)

def res(z, tg, kp, wk, extra=None):
    p2 = project(pose_verts(z), cam); paws = pawW @ p2
    rk = np.concatenate([(paws[i] - np.array(k[:2]) * SC) * wk * (k[2] if len(k) > 2 else 1) for i, k in enumerate(kp)])
    out = [sil_resid(p2, tg), rk, prior(z, kp), (z - xs) * 0.08]
    if extra is not None: out.append(extra(z))
    return np.concatenate(out)

ONESHOT = getattr(C, "MODE", "loop") == "oneshot"
if ONESHOT:
    # 一次性動作：從 START 到 END，每 STEP 格對一次；腳掌預設「留在站姿的位置」（吃、喝、坐下前半段都成立）
    STEP = getattr(C, "STEP", 1); FR = list(range(C.START, C.END + 1, STEP)); N = len(FR)
    p_stand = pawW @ project(pose_verts(xs), cam) / SC
    kp_stand = [(float(p_stand[i][0]), float(p_stand[i][1]), 0.6) for i in range(4)]
    KP = [C.KP.get(f, kp_stand) for f in FR]
else:
    FR = [A0 + k for k in range(N)]; KP = [C.KP[A0 + k] for k in range(N)]
tgs = [Target(M[f]) for f in FR]
X = np.zeros((N, NP)); x = np.clip(xs, lo + 1e-3, hi - 1e-3); t0 = time.time()
# 第一輪：一格接一格。先讓腳掌標記帶路（權重 3），再放手讓剪影收尾（權重 0.6）
for k in range(N):
    r = least_squares(res, x, args=(tgs[k], KP[k], 3.0), diff_step=0.01, max_nfev=25, bounds=(lo, hi))
    r = least_squares(res, r.x, args=(tgs[k], KP[k], 0.6), diff_step=0.01, max_nfev=25, bounds=(lo, hi))
    x = r.x; X[k] = x
print(f"第一輪完成 {time.time() - t0:.0f}s", flush=True)

def refit_cam():
    """影片裡的狗會微微變形、漂移，所以回頭微調攝影機"""
    global cam
    c0 = cam.copy()
    def f(c):
        cc = np.r_[c0[:1], c]; return np.concatenate([sil_resid(project(pose_verts(X[k]), cc), tgs[k]) for k in range(0, N, max(2, N // 10))])
    cam = np.r_[c0[:1], least_squares(f, c0[1:], diff_step=0.003, x_scale=[0.2, 1, 500, 50, 50], max_nfev=15).x]

# 第二輪：繞著循環掃 4 次，每格都被「前後鄰居的平均」和「半圈前另一側的腿」拉住
for sweep in range(4):
    if sweep < 3: refit_cam()
    for k in range(N):
        if ONESHOT:
            nb = 0.5 * (X[max(k - 1, 0)] + X[min(k + 1, N - 1)]); ex = lambda z: (z - nb) * 1.2
        else:
            nb = 0.5 * (X[(k - 1) % N] + X[(k + 1) % N]); o = X[(k + N // 2) % N]
            ex = (lambda z: np.r_[(z - nb) * 1.2, (z[Lidx] - o[Ridx]) * 0.4, (z[Ridx] - o[Lidx]) * 0.4]) if getattr(C, 'SYMMETRY', True) else (lambda z: (z - nb) * 1.2)
        X[k] = least_squares(res, X[k], args=(tgs[k], KP[k], 0.4, ex), diff_step=0.01, max_nfev=15, bounds=(lo, hi)).x
    print(f"掃描 {sweep + 1}/4 完成 {time.time() - t0:.0f}s", flush=True)

# 循環平滑：只留前 5 個頻率（腳趾留 3 個）。這樣曲線一定平順，而且頭尾一定接得起來
def lowpass(X, K):
    F = np.fft.rfft(X, axis=0); F[K + 1:] = 0; return np.fft.irfft(F, n=N, axis=0)
if ONESHOT:
    # 不接頭尾：用高斯平滑（頭尾用邊界值補），腳趾抹得更平
    from scipy.ndimage import gaussian_filter1d
    Y = gaussian_filter1d(X, 1.0, axis=0, mode="nearest"); Y3 = gaussian_filter1d(X, 2.0, axis=0, mode="nearest")
else:
    Y = lowpass(X, 5); Y3 = lowpass(X, 3)
for i in footidx: Y[:, i] = Y3[:, i]
np.save(os.path.join(C.WORK, "X_raw.npy"), X); np.save(os.path.join(C.WORK, "X_final.npy"), Y); np.save(os.path.join(C.WORK, "cam_cycle.npy"), cam)

ious = []; tiles = []
for k in range(N):
    p2 = project(pose_verts(Y[k]), cam); mm = raster(p2); ious.append(iou(mm > 0, tgs[k].m > 0))
    vis = np.zeros(HW + (3,), np.uint8); vis[..., 1] = tgs[k].m * 255; vis[..., 2] = mm * 255
    for i, kpt in enumerate(KP[k]):
        cv2.circle(vis, (int(kpt[0] * SC), int(kpt[1] * SC)), 3, (255, 255, 255), -1)
        cv2.circle(vis, tuple((pawW @ p2)[i].astype(int)), 3, (255, 0, 255), -1)
    tiles.append(vis)
if N > 20: tiles = [tiles[i] for i in np.linspace(0, N - 1, 20).astype(int)]
rows = [np.hstack(tiles[i:i + 5]) for i in range(0, len(tiles) - len(tiles) % 5, 5)]
cv2.imwrite(os.path.join(C.WORK, "check_fit.png"), cv2.resize(np.vstack(rows), None, fx=0.6, fy=0.6))
step = np.abs(np.diff(np.vstack([Y, Y[:1]]) if not ONESHOT else Y, axis=0)).max()
np.save(os.path.join(C.WORK, "frames_used.npy"), np.array(FR))
print("每格重疊率：", np.round(ious, 3).tolist())
print(f"平均 {np.mean(ious):.3f}｜最低 {np.min(ious):.3f}｜單格最大轉動 {step:.2f} 弧度（含最後一格接回第一格）")
print(f"疊圖：{C.WORK}/check_fit.png（白點=你標的腳掌、紫點=模型的腳掌）")
