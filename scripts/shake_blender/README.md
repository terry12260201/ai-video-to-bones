# 🫨 shake_blender｜全身抖毛（Blender 雙視角）腳本包

GPT（Codex）2026-10-06 做出南瓜認定「效果最好」那支抖毛時實際用的腳本。完整原理與數值設定看 [docs/SHAKE.md](../../docs/SHAKE.md)。

> [!WARNING]
> **檔名編號不是執行順序。** 這些是開發過程留下來的檔，照下面的表跑。`17` 每跑一次會把胸口側翻再乘 0.3，**不可以對最終資料重跑**；`01` 會清空 Blender 場景，只能在獨立工作副本跑。

## 開始前

1. 開一個新的工作資料夾，放在專案根目錄底下：`<專案根>/輸出_抖毛_<你的版本>/`。
   `<專案根>` 要有 `beagle.glb` 和 `Ai videos/全身抖毛_正面.mp4`、`Ai videos/全身抖毛.mp4`。
2. 把這整個資料夾複製成 `<工作資料夾>/工具腳本/`，並建 `參考逐幀/`、`驗證/`、`對照逐幀/`。
3. Blender 開著並啟動 MCP 擴充（127.0.0.1:9876），本機 Python 裝 `mcp numpy scipy opencv-python pillow`＋ffmpeg。
4. 先送一段唯讀測試（只回報 Blender 版本與物件），確認連得上、回應格式對。

路徑代號：Blender 端腳本裡的 `__SHAKE_WORK__`／`__SHAKE_PROJECT__` 由 `mcp_call.py` 在送出前換成實際路徑（預設＝`工具腳本/` 的上一層／再上一層，可用環境變數 `SHAKE_WORK`、`SHAKE_PROJECT` 覆蓋）。本機端腳本用 `kinematics.py` 的 `ROOT`（＝`工具腳本/` 的上一層）。

```bash
W='<工作資料夾>/工具腳本'
python3 "$W/mcp_call.py" "$W/04_dump_mesh.py"   # Blender 端：一律經 mcp_call 送
python3 "$W/05_fit_motion.py"                    # 本機端：直接跑
```

## 從零重建的順序

| 階段 | 在哪跑 | 腳本 | 產出 |
|---|---|---|---|
| 1 | 本機 | ffmpeg 拆兩支影片（`-fps_mode passthrough -start_number 0`） | `參考逐幀/front_000…120.png`、`side_…` |
| 2 | Blender | `01_inspect.py` | 獨立場景匯入 `beagle.glb`、`骨架檢查.json` |
| 3 | Blender | `02_preview_setup.py` | 三台攝影機與燈 |
| 4 | Blender | `04_dump_mesh.py` | `rig.npz`（頂點、三角形、權重、rest matrix） |
| 5 | 本機 | `03_measure_reference.py` | 正面鼻尖／眼睛／舌頭量測＋標記總覽（**一定要看標記圖**） |
| 6 | 本機 | `07_measure_side.py`（repo 版已修相依問題） | 側面相機、量測、`side_phase_map.npy` |
| 7 | 本機 | `05_fit_motion.py` | 初始 121 點動作 `motion_fit.npz` |
| 8 | 本機 | `08_fit_ears.py` | 耳尖柔性擬合 |
| 9 | 本機 | `09_correct_support.py` | 整幀腳底修正、`floor_shift` |
| 10 | 本機 | `11_prevent_collisions.py` | 限制耳角、舌頭方向 |
| 11 | 本機 | `12_subframe_support.py` | 細分成 481 點（每 1/4 幀） |
| 12 | 本機 | `17_stabilize_chest.py` ⚠ 只跑一次 | 胸口側翻×0.3＋頸補償 |
| 13 | 本機 | `15_elbow_clearance.py` | 重解肘與前腳 |
| 14 | Blender | `06_apply_preview.py` | 寫入動作、預覽、`.blend` |
| 15 | Blender | `10_verify_blender.py` | 481 點真網格檢查（腳底、穿插、接縫） |
| 16 | Blender | `16_export_render.py` | GLB 匯出（時間歸零、96 Hz）＋三視角渲染 |
| 17 | Blender | `19_roundtrip_glb.py` | GLB 讀回比對 |
| 18 | Blender | `23_final_scene_check.py` | 場景與動作檢查、存檔 |
| 19 | 本機 | `18_make_comparison.py`、`22_all_proof_frames.py` | 四格對照影片、逐幀圖、摘要 |
| 20 | 本機 | `24_audit_delivery.py` | GLB 通道、0–5 秒、首尾一致、SHA |
| 21 | 本機 | `merge_into_review.py <新.glb> <heka-pet-review/beagle.glb> BodyShake_Loop` | 原封不動併進審片室 |

改 NPZ 的階段（7、9、11、12、13）前各存一份 checkpoint，重試時從 checkpoint 還原，不要疊加修改。

## 每支腳本

| 腳本 | 用途 |
|---|---|
| `kinematics.py` | 外部蒙皮與投影（XYZ 角→累積矩陣→近似變形），本機端共用 |
| `comparison_lib.py` | 四格對照圖共用 |
| `mcp_call.py`／`mcp_bridge.py` | MCP stdio 客戶端／轉接到 Blender 擴充的 TCP；會檢查內層 `status`，失敗就丟錯 |
| `13_inspect_export.py`、`20_check_time_options.py` | 唯讀：查本機 glTF exporter 支援哪些參數 |
| `14_debug_limb_contact.py` | 診斷用：追腿與胸口相交，不是固定步驟 |
| `21_reexport_time_zero.py` | 歷史修正：時間起點歸零重匯出；新流程 `16` 已內建，不用跑 |
| `merge_into_review.py` | 把單支動畫 GLB 依骨頭名稱併進審片室 `beagle.glb`，不重取樣、自帶逐 byte 自檢 |

## 不在這包裡的東西

`rig.npz`（含模型網格與權重）、`motion_fit.npz`、模型、影片都有授權或衍生自模型，不公開。原始成果在南瓜本機 `<專案根>/輸出_抖毛_Loop_20261006/`。
