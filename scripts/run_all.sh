#!/bin/bash
# 一鍵跑完（先把 config.py 的 KP 腳掌標記填好）。BLENDER 可用環境變數指定。
set -e
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
"$BLENDER" -b --python scripts/01_export_rig.py | grep OK
python3 scripts/02_segment.py
python3 scripts/03_find_cycle.py
python3 scripts/04_calibrate.py
python3 scripts/05_annotate_sheets.py
python3 scripts/06_fit_cycle.py
python3 - <<'PY'
import sys, os; sys.path.insert(0, "scripts")
from fitlib import *
X = np.load(os.path.join(C.WORK, "X_final.npy")); X = np.vstack([X, X[:1]])      # 最後補一格 = 第一格
np.savez(os.path.join(C.WORK, "final.npz"), S=np.array([skin_mats(x) for x in X]), names=np.array(names),
         cam=np.load(os.path.join(C.WORK, "cam_cycle.npy")), tgt=TGT, size=np.array([FW, FH]))
PY
"$BLENDER" -b --python scripts/07_apply_blender.py | grep DONE
python3 scripts/08_compare.py
