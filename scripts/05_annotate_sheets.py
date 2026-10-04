"""產生「帶座標格線的腿部特寫圖」，讓你（或 AI）逐格讀出四個腳掌的位置，填進 config.py 的 KP。
用法：python scripts/05_annotate_sheets.py"""
import cv2, numpy as np, os
import config as C

M = np.load(os.path.join(C.WORK, "masks.npy")); H, W = M[0].shape
ys, xs = np.where(M[C.CYCLE_START:C.CYCLE_START + C.CYCLE_LEN].any(0))
y0 = int(ys.min() + (ys.max() - ys.min()) * 0.52); y1 = min(H, ys.max() + 35); x0 = max(0, xs.min() - 20); x1 = min(W, xs.max() - 150)
od = os.path.join(C.WORK, "annotate"); os.makedirs(od, exist_ok=True)
def crop(i):
    im = cv2.imread(os.path.join(C.WORK, "frames", f"f_{i + 1:03d}.png"))[y0:y1, x0:x1].copy()
    for x in range((x0 // 50 + 1) * 50, x1, 50):
        cv2.line(im, (x - x0, 0), (x - x0, y1 - y0), (255, 0, 0) if x % 100 == 0 else (255, 180, 120), 1)
        if x % 100 == 0: cv2.putText(im, str(x), (x - x0 + 2, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 0), 1)
    for y in range((y0 // 50 + 1) * 50, y1, 50):
        cv2.line(im, (0, y - y0), (x1 - x0, y - y0), (255, 0, 0) if y % 100 == 0 else (255, 180, 120), 1)
        cv2.putText(im, str(y), (2, y - y0 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 0), 1)
    cv2.putText(im, f"frame {i}", (x1 - x0 - 130, y1 - y0 - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return im
for k in range(0, C.CYCLE_LEN, 4):
    t = [crop(C.CYCLE_START + k + j) for j in range(4) if k + j < C.CYCLE_LEN]
    while len(t) < 4: t.append(np.zeros_like(t[0]))
    cv2.imwrite(os.path.join(od, f"sheet_{k // 4}.png"), np.vstack([np.hstack(t[:2]), np.hstack(t[2:])]))
print(f"OK 特寫圖在 {od}/。格線數字就是影片的像素座標，把每格四個腳掌中心填進 config.py 的 KP")
