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
EXTRA_DOF = ["head:Y", "neck:Y", "Tail_01:Z", "Ear_01.L:Y", "Ear_01.R:Y"]   # 這些側面讀不到，對位時鎖 0，之後由正面影片填入
LIMITS_EXTRA.update({n: (-0.005, 0.005) for n in EXTRA_DOF})   # 鎖 0：側面剪影猜這些只會猜出噪音，還會把腳拉歪
# 不開脊椎側滾：腿掛在脊椎下，脊椎一滾腳就離地
STAND_KP_W = 1.0   # 抖毛四腳基本不動：腳掌留在站姿的位置
ROOT_PRIOR = 0.6   # 身體根別亂飄
LIMITS_EXTRA.update({"head:Z": (-1.3, 1.3), "head:Y": (-.9, .9), "neck:Z": (-.9, .9), "neck:Y": (-.6, .6), "Spine_03:Y": (-.5, .5), "Spine_05:Y": (-.5, .5), "Spine_base:Y": (-.4, .4), "Tail_01:Z": (-.9, .9), "Ear_01": (-1.6, 1.6)})
FACE_LAYER_EXCLUDE = ["Ear_01.L", "Ear_01.R"]   # 耳朵外飛是正面影片量出來的，別讓 Idle 的耳朵蓋掉（Ear_02 仍沿用 Idle 的垂擺）
