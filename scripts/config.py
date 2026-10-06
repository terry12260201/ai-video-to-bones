"""專案設定：換一隻動物、換一支影片，只需要改這個檔。
下面的值是範例（一隻 Beagle、側面走路影片），請依你的模型調整。"""
import os

# ── 路徑（也可以用環境變數蓋掉）────────────────────────────
PROJECT = os.environ.get("AV2B_PROJECT", "")              # 多支動畫時：projects/<名稱>.py 會蓋掉下面的設定
WORK  = os.environ.get("AV2B_WORK",  "work")              # 中間檔都放這
GLB   = os.environ.get("AV2B_GLB",   "input/model.glb")   # 綁好骨架的模型
VIDEO = os.environ.get("AV2B_VIDEO", "input/video.mp4")   # AI 生成的側面影片
OUT   = os.environ.get("AV2B_OUT",   "output")

# ── 動作類型 ──────────────────────────────────────────────
SYMMETRY = True      # loop 用：左右腳差半圈（走路、小跑成立；奔跑不成立）
MODE = "loop"        # loop = 循環動作（走、跑）；oneshot = 一次性動作（吃、喝、坐下），從 START 做到 END 不接頭尾
START, END = 0, 0    # oneshot 用：影片第幾格到第幾格（0 起算，含 END）

# ── 模型 ──────────────────────────────────────────────────
ARMATURE = "Arm_Beagle"       # 骨架物件名稱
MESH     = "Cartoon_Beagle"   # 網格物件名稱
ACTION   = "Walk_AIVideo_Loop"
ROOT     = "Spine_base"       # 可以上下前後平移的那根骨頭（骨盆／身體根）

# 要讓程式調整的骨頭（都只繞「左右軸」轉，因為側面影片看不到深度）
LEGS = ["f.L", "f.R", "b.L", "b.R"]     # 近前、遠前、近後、遠後（L = 靠鏡頭那側）
DOF = ["Spine_base", "Spine_03", "Spine_05", "neck", "head",
       "Tail_01", "Tail_02", "Tail_03", "Tail_04", "Tail_05"]
for s in ("L", "R"):
    DOF += [f"hip_f.{s}", f"thigh_f.{s}", f"leg_f.{s}", f"shin_f.{s}", f"foot_f.{s}",
            f"hip_b.{s}", f"thigh_b.{s}", f"leg_b.{s}", f"shin_b.{s}", f"foot_b.{s}"]
DOF += ["Ear_01.L", "Ear_01.R", "mouth"]   # 耳朵甩動、嘴巴開合（低頭吃東西時看得到）
# 需要離開側面平面的動作（抖毛、轉頭）在專案檔用 EXTRA_DOF 加："head:Z"=左右轉頭、"neck:Y"=側滾；見 fitlib.dof_split

# 每條腿從身體根到腳掌的骨頭鏈（用來算「腳掌對地面的角度」）
def leg_chain(l):
    if l[0] == "f":
        return ["Spine_base", "Spine_03", "Spine_05"] + [f"{b}_{l}" for b in ("hip", "thigh", "leg", "shin", "foot")]
    return ["Spine_base"] + [f"{b}_{l}" for b in ("hip", "thigh", "leg", "shin", "foot")]

# 腳掌 = 哪幾根骨頭帶的頂點（取它們的中心當「腳掌點」）
PAW_BONES = lambda l: [f"foot_{l}", f"claws_{l}"]

# 關節活動範圍（弧度；正值 = 末端往尾巴方向擺）。沒有這個，膝蓋會反折。
LIMITS = {"hip_f": (-.45, .45), "thigh_f": (-.9, .9), "leg_f": (-1.5, .25), "shin_f": (-.3, 2.0), "foot_f": (-.5, .7),
          "hip_b": (-.35, .35), "thigh_b": (-.9, .7), "leg_b": (-.5, 1.2), "shin_b": (-1.2, .5), "foot_b": (-.5, .8)}
DEFAULT_LIMIT = (-.5, .5)
LIMITS.update({"Ear_01": (-.9, .9), "mouth": (-.1, .7), "neck": (-1.2, .6), "head": (-.9, .9), "Spine_03": (-.5, .5), "Spine_05": (-.7, .5)})
TAIL_LIMIT = (-.8, .8)

# ── 影片 ──────────────────────────────────────────────────
CALIB_FRAME = 4     # 拿哪一格校正攝影機（狗站著不動、最接近模型原始姿勢的那格；0 起算）
CYCLE_START = 96    # 循環從哪一格開始（跑 03_find_cycle.py 會建議）
CYCLE_LEN   = 20    # 一個循環幾格（同上）
BG_THRESHOLD = 6    # 剪影門檻：畫面跟背景差多少算「狗」
BODY_Y_MAX = 470    # 這條線以上的洞一律補起來（身體不會有洞，腿之間才有）

# 落地判斷：腳掌標記的 y 超過這個值就當作踩在地上（近側腳在畫面比較低）
GROUND_Y = {"f.L": 698, "f.R": 671, "b.L": 698, "b.R": 671}

# ── 手標腳掌中心（影片原始像素座標）────────────────────────
# 順序跟 LEGS 一樣。第三個值是權重（看不清楚、用猜的就給 0.3）。
# 用 04_annotate_sheets.py 產生帶格線的特寫圖來讀座標。
KP = {
 96:[(490,703),(238,675),(818,665),(745,675)],  97:[(525,700),(265,682),(730,675),(785,675)],
 98:[(535,690),(285,680),(700,670),(788,675)],  99:[(535,675),(295,680),(685,678),(805,680)],
100:[(505,665),(345,682),(632,700),(848,678)], 101:[(425,665),(375,685),(630,703),(875,675)],
102:[(335,670),(403,680),(648,703),(885,680)], 103:[(285,680),(410,680),(670,705),(900,678,.3)],
104:[(235,682),(450,682),(710,703),(875,642)], 105:[(218,685),(480,682),(740,703),(830,645)],
106:[(225,692),(498,680),(765,705),(770,645,.5)], 107:[(235,697),(520,682),(780,705),(745,640)],
108:[(270,700),(545,665),(820,700),(685,648)], 109:[(305,700),(518,642),(858,700),(638,667)],
110:[(328,702),(485,640),(870,700),(623,672)], 111:[(345,702),(445,640),(880,700),(618,678)],
112:[(382,702),(332,655),(895,692,.3),(640,675)], 113:[(408,702),(288,658),(900,680,.3),(660,675)],
114:[(428,703),(268,662),(890,668,.3),(678,675)], 115:[(448,703),(245,665),(860,662,.3),(692,678)],
}

# ── 多專案：AV2B_PROJECT=trot 會載入 projects/trot.py，裡面的變數蓋掉上面的 ──
if PROJECT:
    import importlib.util as _u, pathlib as _p
    _f = _p.Path(__file__).parent / "projects" / f"{PROJECT}.py"
    _spec = _u.spec_from_file_location("proj", _f); _m = _u.module_from_spec(_spec); _spec.loader.exec_module(_m)
    globals().update({k: v for k, v in vars(_m).items() if not k.startswith("_")})
    LIMITS = dict(LIMITS, **globals().get("LIMITS_EXTRA", {}))
    DOF = DOF + list(globals().get("EXTRA_DOF", []))
    WORK = os.environ.get("AV2B_WORK", f"work/{PROJECT}"); OUT = os.environ.get("AV2B_OUT", f"output/{PROJECT}")
