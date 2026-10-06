"""Beagle 全身抖毛・正面影片（只拿來讀頭側滾、身體側滾、耳朵外飛；身體四肢用側面那支）"""
VIDEO = "input/shake_front.mp4"
ACTION = "BodyShake_AIVideo_front"
MODE = "oneshot"
CALIB_FRAME = 8
START, END = 8, 120
STEP = 1
GROUND_Y = {"f.L": 9999, "f.R": 9999, "b.L": 9999, "b.R": 9999}   # 正面不做「腳掌放平」判斷
KP = {}
LIMITS_EXTRA = {"Spine_03": (-.2, .2), "Spine_05": (-.2, .2), "neck": (-.5, .5), "head": (-.6, .6),
                "head:Z": (-1.0, 1.0), "head:Y": (-1.1, 1.1), "neck:Z": (-.6, .6), "neck:Y": (-.6, .6),
                "Spine_03:Y": (-.5, .5), "Spine_05:Y": (-.5, .5), "Spine_base:Y": (-.4, .4), "Tail_01:Z": (-1.0, 1.0), "Ear_01": (-1.6, 1.6)}
EXTRA_DOF = ["head:Z", "head:Y", "neck:Z", "neck:Y", "Spine_03:Y", "Spine_05:Y", "Spine_base:Y", "Tail_01:Z", "Ear_01.L:Z", "Ear_01.R:Z", "Ear_01.L:Y", "Ear_01.R:Y"]
TEMPORAL = 0.8
EDGE_FRAMES = 6
