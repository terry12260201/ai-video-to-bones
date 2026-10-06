"""把循環裡的每一格放大成兩格一張的特寫（比 sheet 更容易讀座標）"""
import cv2, numpy as np, os, sys
import config as C
M = np.load(os.path.join(C.WORK, "masks.npy")); H, W = M[0].shape
A, N = C.CYCLE_START, C.CYCLE_LEN
ys, xs = np.where(M[A:A + N].any(0))
y0 = int(ys.min() + (ys.max() - ys.min()) * 0.45); y1 = min(H, ys.max() + 30); x0 = max(0, xs.min() - 20); x1 = min(W, xs.max() - 120)
od = os.path.join(C.WORK, "pairs"); os.makedirs(od, exist_ok=True)
def crop(i):
    im = cv2.imread(os.path.join(C.WORK, "frames", f"f_{i + 1:03d}.png"))[y0:y1, x0:x1].copy()
    for x in range((x0 // 50 + 1) * 50, x1, 50):
        cv2.line(im, (x - x0, 0), (x - x0, y1 - y0), (255, 0, 0) if x % 100 == 0 else (255, 190, 140), 1)
        if x % 100 == 0: cv2.putText(im, str(x), (x - x0 + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    for y in range((y0 // 50 + 1) * 50, y1, 50):
        cv2.line(im, (0, y - y0), (x1 - x0, y - y0), (255, 0, 0) if y % 100 == 0 else (255, 190, 140), 1)
        cv2.putText(im, str(y), (2, y - y0 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    cv2.putText(im, f"frame {i}", (x1 - x0 - 120, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return cv2.resize(im, None, fx=1.4, fy=1.4, interpolation=cv2.INTER_CUBIC)
for k in range(0, N, 2):
    t = [crop(A + k + j) for j in range(2) if k + j < N]
    cv2.imwrite(os.path.join(od, f"p_{k // 2}.png"), np.vstack(t))
print("OK", od, N)
