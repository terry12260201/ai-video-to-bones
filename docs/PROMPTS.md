# 🎬 影片 Prompt 範本 v2｜快樂的狗，每個細節都要活

這份是給「生影片」那一步用的。目標只有一個：**影片要讓後面的程式對得上骨架**，所以約束擺第一，活潑擺第二。
每支 Prompt ＝ 固定段（約束）＋ 活力段（表情、舌頭、耳朵、喘氣）＋ 動作段 ＋ 聲音段。

> [!IMPORTANT]
> 目前的對位程式只讀**側面**影片。下面標「＋正面」「＋斜角」的動作，是指**同一個動作要多生一支別的角度**：側面那支拿來對骨架，其他角度給 AI 看「身體往哪邊轉、腳往哪邊伸」，手動補那些側面看不出來的關節。多角度自動對位還沒做。

## 1. 固定段（每支都放，不要改）

```text
Animate the exact stylized cartoon {SPECIES} game model in the supplied image.
Preserve its exact body proportions, colors, markings and exactly four legs — do not add, remove or merge limbs.
{VIEW}
Locked-off tracking camera that follows the animal so it stays centered at a constant size.
No cuts, no zoom, no camera rotation, no motion blur, no slow motion.
Keep the plain flat grey studio background and even lighting. No ground shadow, no props, no text.
```

`{VIEW}` 三選一：

| 角度 | 寫法 | 用途 |
|---|---|---|
| 側面（主） | `Strict side-view profile, facing left, the whole body always fully in frame.` | 對骨架用，每個動作一定要有 |
| 正面 | `Strict front view, the animal faces the camera, all four legs visible, the whole body always fully in frame.` | 看左右：歪頭、抬哪隻腳、身體左右擺 |
| 斜角 | `Three-quarter view from the animal's front-left, about 45 degrees, all four legs visible, the whole body always fully in frame.` | 看轉身、繞圈、翻滾的空間關係 |

## 2. 活力段（每支都放）

這隻是快樂的狗，**無時無刻都在喘氣**。這段讓每支影片都有同一個「人格」。

```text
It is a happy, energetic dog: mouth slightly open, panting lightly and continuously with the pink tongue visible and bobbing with each breath, chest rising and falling.
Eyes bright and alert. The long soft ears swing and flop naturally with every movement of the head.
The tail is up and wags; the whole body is loose and lively, never stiff or robotic.
```

## 3. 動作段 ＋ 聲音段（挑一組）

聲音段用 `Audio:` 開頭，Seedance 會一起生出來。對位用不到聲音，但遊戲裡要用，順手一起做。

| 代號 | 動作 | 角度 | 動作段 | 聲音段 | 秒數 |
|---|---|---|---|---|---|
| `Walk` | 走路循環 | 側面 | `The dog walks forward in place at a calm, steady pace with a natural four-beat walking gait. Even rhythm, each paw clearly lifts and lands. The motion loops seamlessly.` | `Audio: soft rhythmic paw steps on a hard floor, light panting, no music.` | 5 |
| `Trot` | 小跑循環 | 側面 | `The dog trots forward in place at a brisk, steady pace with a natural two-beat diagonal gait. Light bounce in the body, ears flopping, even rhythm. The motion loops seamlessly.` | `Audio: quick light paw steps, steady happy panting, jingling of a collar tag, no music.` | 5 |
| `Run` | 奔跑循環 | 側面 | `The dog runs forward in place at full speed with a natural gallop: the spine flexes and extends, front and hind legs gather and stretch, ears streaming back. Even rhythm. The motion loops seamlessly.` | `Audio: fast pounding paw steps, excited heavy panting, no music.` | 5 |
| `Eat` | 吃東西 | 側面 | `The dog stands still, lowers its head to the ground and eats from the floor with small rhythmic head bobs and chewing, ears falling forward around the muzzle, tail wagging slowly. Legs stay planted. Then it raises its head, licks its lips and looks up happily.` | `Audio: crunchy chewing and munching, little snorts, a satisfied lick, no music.` | 10 |
| `Drink` | 喝水 | 側面 | `The dog stands still, lowers its head to a water bowl on the floor and laps water with quick tongue flicks, ears hanging forward. Legs stay planted. Then it raises its head with water dripping from its chin and shakes its head once.` | `Audio: rapid wet lapping, dripping water, one quick head-shake flutter, no music.` | 10 |
| `Sit` | 坐下 | 側面 | `The dog stands still for one second, then smoothly sits down, lowering its hindquarters to the ground while the front legs stay straight, tail sweeping the floor. It holds the sit, panting happily.` | `Audio: a soft thump as it sits, happy panting, tail brushing the floor, no music.` | 5 |
| `LieDown` | 趴下 | 側面 | `The dog stands still for one second, then smoothly lies down on its belly, front legs stretched forward, head up and alert, tail thumping the floor.` | `Audio: a soft settling thump, slow content panting, tail thumps, no music.` | 10 |
| `Stretch` | 伸懶腰 | 側面 | `The dog stands still for one second, then stretches: front legs slide forward and the chest lowers to the ground while the hips stay high, a big yawn with the tongue curling, then it rises back to standing and shakes lightly.` | `Audio: a long drawn-out yawn, a little groan of pleasure, a light shake, no music.` | 10 |
| `SniffGround` | 低頭嗅聞 | 側面 | `The dog stands still, lowers its head and sniffs the floor intently, nose twitching, head moving in small arcs left and right, ears forward. Legs stay planted. Then it raises its head.` | `Audio: rapid wet sniffing, small snorts, no music.` | 5 |
| `SniffAir` | 聞空氣 | 側面 | `The dog stands still, lifts its head about 30 degrees and sniffs the air with its nose twitching and small head tilts, ears perking, then lowers its head back to neutral.` | `Audio: short sharp sniffs, a curious little whine, light panting, no music.` | 5 |
| `PlayBow` | 邀玩鞠躬 | 側面 | `The dog drops into a play bow: front legs slide forward and the chest goes to the ground while the hindquarters stay high in the air, tail wagging fast, mouth open in a happy grin, then it bounces back up.` | `Audio: an excited playful bark, fast tail swishing, a bouncy paw thump, no music.` | 5 |
| `PawBall` | 拍球 | 側面 ＋ 正面 | `The dog stands still, locks its eyes on the floor in front of it, lifts one front paw and bats downward twice at the floor playfully, head bobbing with each swat, ears bouncing.` | `Audio: two soft paw pats on the floor, a playful huff, light panting, no music.` | 5 |
| `HungryBeg` | 討食 | 側面 | `The dog sits, then rises up on its hind legs into a begging pose with both front paws held up in front of its chest, head tilted up looking at its owner, tongue out, licking its lips hopefully, then drops back to sitting.` | `Audio: an eager high-pitched whine, lip-licking, a hopeful little bark, no music.` | 5 |
| `BodyShake` | 全身抖毛 | 側面 ＋ 正面 | `The dog stands still, then shakes its whole body vigorously from head to tail in a wave: the head twists first, ears flapping wildly, then the body, then the tail, slowing down to a stop, then a happy pant.` | `Audio: a fast flapping shake with jingling collar, ears slapping, then a relaxed pant, no music.` | 5 |
| `HeadTilt` | 歪頭 | **正面**（側面看不出來） | `The dog faces the camera, ears perked, tilts its head about 25 degrees to its left in a curious way, holds, then tilts back upright.` | `Audio: a curious soft whimper, light panting, no music.` | 5 |
| `HeadNod` | 點頭 | 側面 | `The dog stands still and nods its head twice in a clear up-and-down motion as if agreeing, ears swinging, tail wagging.` | `Audio: two soft happy huffs, light panting, no music.` | 5 |
| `PetHead` | 摸頭反應 | 側面 ＋ 正面 | `A hand is NOT shown. The dog lowers its head slightly as if being petted, squints its eyes in pleasure, leans gently into the touch, then lifts its head and licks the air, tail wagging slowly.` | `Audio: a long content sigh, soft happy panting, no music.` | 5 |
| `Spin` | 原地轉圈 | 側面 ＋ 斜角 | `The dog spins quickly in one full circle in place, chasing its own tail with its head turned back, body curved, little bouncy steps, then stops facing the same direction it started.` | `Audio: quick scrambling paw steps, excited yips, no music.` | 5 |
| `BellyUp` | 翻肚 | 側面 ＋ 斜角 | `The dog is lying down, then rolls onto its back with all four legs in the air, paws relaxed and curled, belly up, head tilted sideways, tongue lolling out, tail wagging.` | `Audio: a rustling roll, a happy groan, relaxed panting, no music.` | 10 |

## 4. 組合範例（直接貼）

```text
Animate the exact stylized cartoon beagle dog game model in the supplied image.
Preserve its exact body proportions, colors, markings and exactly four legs — do not add, remove or merge limbs.
Strict side-view profile, facing left, the whole body always fully in frame.
Locked-off tracking camera that follows the animal so it stays centered at a constant size.
No cuts, no zoom, no camera rotation, no motion blur, no slow motion.
Keep the plain flat grey studio background and even lighting. No ground shadow, no props, no text.
It is a happy, energetic dog: mouth slightly open, panting lightly and continuously with the pink tongue visible and bobbing with each breath, chest rising and falling.
Eyes bright and alert. The long soft ears swing and flop naturally with every movement of the head.
The tail is up and wags; the whole body is loose and lively, never stiff or robotic.
The dog drops into a play bow: front legs slide forward and the chest goes to the ground while the hindquarters stay high in the air, tail wagging fast, mouth open in a happy grin, then it bounces back up.
Audio: an excited playful bark, fast tail swishing, a bouncy paw thump, no music.
```

## 5. 哪些動作側面不夠，要補角度

判斷方法：**這個動作有沒有「往鏡頭方向」或「左右方向」的位移？**有就要補。

| 情況 | 補什麼 | 為什麼 |
|---|---|---|
| 頭或身體左右偏（歪頭、回頭看、聞空氣轉頭） | 正面 | 側面只看得到頭上下，看不到左右 |
| 單腳動作（拍球、擋爪、舉手） | 正面 | 側面分不出是左腳還是右腳 |
| 身體轉向（轉圈、追尾、回頭） | 斜角 45° | 側面會看到腿交疊成一團 |
| 翻滾（翻肚、睡中翻身） | 斜角 45° ＋ 側面 | 背部朝上朝下在側面幾乎一樣 |
| 純上下、前後的動作（走、跑、吃、喝、坐、趴、伸懶腰、鞠躬） | 只要側面 | 所有關節都在同一個平面上動 |

補的角度**目前只給人和 AI 看**，程式還不會自動吃進去。做這類動作時，AI 要先用側面對好，再看正面／斜角影片手動調左右。
