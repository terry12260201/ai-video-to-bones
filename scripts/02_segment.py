"""把影片拆成一格一格，再把每一格的動物剪影（黑白遮罩）抓出來。
做法：背景是素色漸層，所以用每一列最左、最右的顏色當背景，跟背景差很多的就是動物。
用法：python scripts/02_segment.py"""
import cv2, numpy as np, os, subprocess, glob
import config as C

fd = os.path.join(C.WORK, "frames"); os.makedirs(fd, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", C.VIDEO, os.path.join(fd, "f_%03d.png")], check=True)
files = sorted(glob.glob(os.path.join(fd, "f_*.png")))
masks = []
for p in files:
    im = cv2.imread(p).astype(np.float32)
    L = np.median(im[:, :12], axis=1); R = np.median(im[:, -6:], axis=1)
    t = np.linspace(0, 1, im.shape[1])[None, :, None]
    d = np.abs(im - (L[:, None, :] * (1 - t) + R[:, None, :] * t)).max(2)
    m = (cv2.GaussianBlur(d, (3, 3), 0) > C.BG_THRESHOLD).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    m = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)          # 只留最大那塊
    n, lab, st, cen = cv2.connectedComponentsWithStats(1 - m)       # 補洞
    for k in range(1, n):
        if st[k, 0] > 0 and st[k, 1] > 0 and (st[k, 4] < 2500 or cen[k, 1] < C.BODY_Y_MAX): m[lab == k] = 1
    masks.append(m.astype(bool))
masks = np.array(masks); np.save(os.path.join(C.WORK, "masks.npy"), masks)
ids = np.linspace(0, len(masks) - 1, 8).astype(int)
tiles = [cv2.resize((masks[i] * 255).astype(np.uint8), None, fx=0.4, fy=0.4) for i in ids]
cv2.imwrite(os.path.join(C.WORK, "check_masks.png"), np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])]))
print(f"OK {len(masks)} 格。請打開 {C.WORK}/check_masks.png 確認剪影乾淨（腿沒有斷、沒有多餘的線）")
