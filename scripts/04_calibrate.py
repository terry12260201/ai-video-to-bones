"""校正攝影機：找出「影片是從哪個角度、多遠拍的」，同時把模型擺成影片裡站著的樣子。
用法：python scripts/04_calibrate.py"""
import os
from scipy.optimize import least_squares
from fitlib import *

M = load_masks(); tg = Target(M[C.CALIB_FRAME])
def f(z): return np.r_[sil_resid(project(pose_verts(z[6:]), z[:6]), tg), z[6:] * 0.3]
best = None
for az in (-0.25, 0.0, 0.25):                              # 多試幾個起點，避免卡在錯的角度
    z0 = np.r_[[az, 0.25, 4.5 * np.ptp(V, axis=0).max(), 3.5 * HW[1], HW[1] / 2, HW[0] / 2], np.zeros(NP)]
    r = least_squares(f, z0, diff_step=0.01, x_scale=np.r_[[0.2, 0.2, 1, 500, 50, 50], np.ones(NP)], max_nfev=60)
    if best is None or r.cost < best.cost: best = r
z = best.x; mm = raster(project(pose_verts(z[6:]), z[:6]))
np.save(os.path.join(C.WORK, "cam.npy"), z[:6]); np.save(os.path.join(C.WORK, "x_stand.npy"), z[6:])
vis = np.zeros(HW + (3,), np.uint8); vis[..., 1] = tg.m * 255; vis[..., 2] = mm * 255
cv2.imwrite(os.path.join(C.WORK, "check_calib.png"), vis)
print("攝影機：", z[:6].round(3).tolist())
print(f"重疊率 {iou(mm > 0, tg.m > 0):.3f}（0.9 以上才往下做）。疊圖：{C.WORK}/check_calib.png（黃=重疊、綠=只有影片、紅=只有模型）")
