"""把兩支影片的對位結果合成一支：側面給「側面平面」的關節（X 軸），正面給「離開側面平面」的關節（Y／Z 軸、耳朵）。
兩支影片不是同一次生的，節奏不同，所以用「開始動的格」與「停止動的格」線性對齊。
用法：python3 scripts/06c_combine_views.py <側面專案> <正面專案> <側面起> <側面止> <正面起> <正面止>"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
side, front, s0, s1, f0, f1 = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
import importlib.util as U
def cfg(name):
    os.environ["AV2B_PROJECT"] = name
    sp = U.spec_from_file_location("c_" + name, os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")); m = U.module_from_spec(sp); sp.loader.exec_module(m); return m
CS, CF = cfg(side), cfg(front)
XS = np.load(os.path.join(CS.WORK, "X_final.npy")); FS = np.load(os.path.join(CS.WORK, "frames_used.npy"))
XF = np.load(os.path.join(CF.WORK, "X_final.npy")); FF = np.load(os.path.join(CF.WORK, "frames_used.npy"))
# 側面格 t → 正面格：動作區間線性對應，區間外貼邊
def warp(t):
    if t <= s0: return f0 + (t - s0)
    if t >= s1: return f1 + (t - s1)
    return f0 + (t - s0) * (f1 - f0) / (s1 - s0)
OUT = XS.copy(); taken = []
for n in CS.DOF:
    if ":" not in n and not n.startswith("Ear_01"): continue          # 只拿離開側面平面的關節＋耳朵
    if n not in CF.DOF: continue
    i, j = CS.DOF.index(n) + 2, CF.DOF.index(n) + 2
    OUT[:, i] = np.interp([warp(t) for t in FS], FF, XF[:, j]); taken.append(n)
# 動作區間外（站著）把這些關節淡回 0，接點才乾淨
w = np.clip((FS - (s0 - 6)) / 6, 0, 1) * np.clip(((s1 + 10) - FS) / 10, 0, 1)
for n in taken: OUT[:, CS.DOF.index(n) + 2] *= w
np.save(os.path.join(CS.WORK, "X_final.npy"), OUT)
print("OK 合成", len(taken), "個關節來自正面：", taken)
