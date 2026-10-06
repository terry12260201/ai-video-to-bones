"""把兩支影片的對位結果合成一支：側面給「側面平面」的關節（X 軸），正面給「離開側面平面」的關節（Y／Z 軸、耳朵）。
兩支影片不是同一次生的，節奏不同，用「開始動的格」與「停止動的格」線性對齊。
用法：python3 scripts/06c_combine_views.py <側面專案> <正面專案> <側面起> <側面止> <正面起> <正面止> [master=side|front]
master=front：以正面影片的時間軸為主（抖毛這種以側滾為主的動作用這個），側面的身體動作被拉伸到正面的長度；輸出寫回側面專案。"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
side, front, s0, s1, f0, f1 = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
master = sys.argv[7] if len(sys.argv) > 7 else "side"
import importlib.util as U
def cfg(name):
    os.environ["AV2B_PROJECT"] = name
    sp = U.spec_from_file_location("c_" + name, os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")); m = U.module_from_spec(sp); sp.loader.exec_module(m); return m
CS, CF = cfg(side), cfg(front)
raw, fin = os.path.join(CS.WORK, "X_raw_side.npy"), os.path.join(CS.WORK, "X_final.npy")
if not os.path.exists(raw) or os.path.getmtime(fin) > os.path.getmtime(raw) + 1 and np.load(fin).shape[1] != np.load(raw).shape[1]:
    pass
# 06 剛重跑過（X_final 比留存的側面原版新、且不是本腳本寫的）就重新留存；否則沿用留存版，重跑合成才不會疊兩次
if not os.path.exists(raw) or (os.path.getmtime(fin) > os.path.getmtime(raw) + 1 and not os.path.exists(os.path.join(CS.WORK, "frames_front.npy"))) or np.load(raw).shape[1] != len(CS.DOF) + 2:
    np.save(raw, np.load(fin)); fs_raw = os.path.join(CS.WORK, "frames_side_raw.npy"); np.save(fs_raw, np.load(os.path.join(CS.WORK, "frames_used.npy")))
XS = np.load(raw); FS = np.load(os.path.join(CS.WORK, "frames_side_raw.npy")) if os.path.exists(os.path.join(CS.WORK, "frames_side_raw.npy")) else np.load(os.path.join(CS.WORK, "frames_used.npy"))
XF = np.load(os.path.join(CF.WORK, "X_final.npy")); FF = np.load(os.path.join(CF.WORK, "frames_used.npy"))
def warp(t, a0, a1, b0, b1):                                     # a 時間軸的格 → b 時間軸的格
    if t <= a0: return b0 + (t - a0)
    if t >= a1: return b1 + (t - a1)
    return b0 + (t - a0) * (b1 - b0) / (a1 - a0)
offplane = [n for n in CS.DOF if (":" in n or n.startswith("Ear_01")) and n in CF.DOF]
if master == "side":
    OUT = XS.copy(); T = FS
    for n in offplane:
        OUT[:, CS.DOF.index(n) + 2] = np.interp([warp(t, s0, s1, f0, f1) for t in FS], FF, XF[:, CF.DOF.index(n) + 2])
    a0, a1 = s0, s1
else:
    T = FF; OUT = np.zeros((len(FF), len(CS.DOF) + 2))
    for k, n in enumerate(CS.DOF):                                # 側面的關節全部拉到正面時間軸
        OUT[:, k + 2] = np.interp([warp(t, f0, f1, s0, s1) for t in FF], FS, XS[:, k + 2])
    OUT[:, 0] = np.interp([warp(t, f0, f1, s0, s1) for t in FF], FS, XS[:, 0]); OUT[:, 1] = np.interp([warp(t, f0, f1, s0, s1) for t in FF], FS, XS[:, 1])
    for n in offplane: OUT[:, CS.DOF.index(n) + 2] = XF[:, CF.DOF.index(n) + 2]
    a0, a1 = f0, f1
w = np.clip((T - (a0 - 6)) / 6, 0, 1) * np.clip(((a1 + 10) - T) / 10, 0, 1)   # 動作區間外淡回 0
for n in offplane: OUT[:, CS.DOF.index(n) + 2] *= w
SIDE_T = T if master == "side" else np.clip(np.array([int(round(warp(t, f0, f1, s0, s1))) for t in FF]), int(FS.min()), int(FS.max()))
np.save(os.path.join(CS.WORK, "X_final.npy"), OUT); np.save(os.path.join(CS.WORK, "frames_used.npy"), SIDE_T); np.save(os.path.join(CS.WORK, "frames_front.npy"), FF)
print("OK 合成，主時間軸 =", master, "，來自正面的關節：", offplane, "，格數", len(T))
