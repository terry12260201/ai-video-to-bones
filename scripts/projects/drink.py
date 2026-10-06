"""Beagle 喝水（2026-10-06）"""
VIDEO = "input/drink.mp4"
ACTION = "Drink_AIVideo"
MODE = "oneshot"
CALIB_FRAME = 2
CYCLE_START, CYCLE_LEN = 0, 0
START, END = 2, 240
STEP = 2            # 每 2 格對一次，中間由 Blender 內插（10 秒影片省一半時間）
GROUND_Y = {"f.L": 698, "f.R": 671, "b.L": 698, "b.R": 671}
KP = {}
