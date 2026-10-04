"""做對照影片：左=AI 影片、中=Blender 骨架動畫、右=把 Blender 的輪廓疊在 AI 影片上。
用法：python scripts/08_compare.py"""
import cv2, numpy as np, subprocess, os
import config as C

cd = os.path.join(C.OUT, "cmp"); os.makedirs(cd, exist_ok=True); n = 0
for rep in range(5):
    for k in range(C.CYCLE_LEN):
        v = cv2.imread(os.path.join(C.WORK, "frames", f"f_{C.CYCLE_START + k + 1:03d}.png"))
        a = cv2.imread(os.path.join(C.OUT, "render", f"r_{k + 1:03d}.png"), cv2.IMREAD_UNCHANGED)
        al = a[..., 3:] / 255.0; bg = np.zeros_like(v, dtype=np.float32) + np.median(v[:, :12], axis=1)[:, None, :]
        r = (a[..., :3] * al + bg * (1 - al)).astype(np.uint8)
        ov = v.copy(); ov[cv2.dilate(cv2.Canny(a[..., 3], 50, 150), np.ones((2, 2), np.uint8)) > 0] = (0, 0, 255)
        for im, t in ((v, "AI Video"), (r, "Blender (bones)"), (ov, "Overlay")): cv2.putText(im, t, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite(os.path.join(cd, f"c_{n:03d}.png"), np.hstack([v, r, ov])); n += 1
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(cd, "c_%03d.png"), "-vf", "scale=2260:-2", "-pix_fmt", "yuv420p", "-crf", "18", os.path.join(C.OUT, "compare.mp4")], check=True)
print("OK", os.path.join(C.OUT, "compare.mp4"))
