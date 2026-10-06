"""Beagle 全身抖毛（2026-10-06，第一格模式重生版）"""
VIDEO = "input/shake.mp4"
ACTION = "BodyShake_AIVideo"
MODE = "oneshot"
CALIB_FRAME = 8
START, END = 8, 120
STEP = 1            # 抖毛很快，每格都對
GROUND_Y = {"f.L": 698, "f.R": 671, "b.L": 698, "b.R": 671}
KP = {}
LIMITS_EXTRA = {"Spine_03": (-.3, .3), "Spine_05": (-.35, .35), "neck": (-1.0, .8), "head": (-1.0, 1.0)}
TEMPORAL = 0.8      # 抖毛是高頻動作，前後格不要拉太緊
EDGE_FRAMES = 6
EXTRA_DOF = ["head:Z", "head:Y", "neck:Z", "neck:Y", "Spine_03:Y", "Spine_05:Y", "Spine_base:Y", "Tail_01:Z", "Ear_01.L:Z", "Ear_01.R:Z", "Ear_01.L:Y", "Ear_01.R:Y"]
LIMITS_EXTRA.update({"head:Z": (-1.3, 1.3), "head:Y": (-.9, .9), "neck:Z": (-.9, .9), "neck:Y": (-.6, .6), "Spine_03:Y": (-.5, .5), "Spine_05:Y": (-.5, .5), "Spine_base:Y": (-.4, .4), "Tail_01:Z": (-.9, .9), "Ear_01": (-1.6, 1.6)})
