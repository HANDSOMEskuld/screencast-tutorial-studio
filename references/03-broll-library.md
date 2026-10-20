# B-roll 与提示动画库

## 1. 什么时候放 B-roll（AI 判断依据）
| 触发场景 | 推荐 kind | 目的 |
|---|---|---|
| 讲"原理/它是怎么工作的"，画面却只是静止页面 | `flow` | 用动画把抽象关系画出来 |
| "以前 vs 现在 / 错误 vs 正确 / A vs B" | `compare` | 一眼看出差异 |
| 有可量化的收益（速度、体积、耗时、价格） | `stat` | 数字冲击 |
| 前置条件、总结回顾 | `checklist` | 逐项打钩，满足感 |
| 情绪点：踩坑后安慰、成功后庆祝、小贴士 | `mascot`（可爱） | 拟人化，缓冲节奏 |
| 容易出错的地方 | `warning` | 先警示再给解法 |
| 预告/回顾整体路线 | `timeline` | 让观众有"地图" |
| 以上都不贴切 | `custom` | AI 现写 |
节奏：每分钟 ≥1 个；3–6 秒；同类型不连续出现；放在**讲解静止/操作等待/情绪转折**处，不要放在关键点击瞬间。

## 2. 模式
- `pip`（默认）：右上(或 `pos:"left"`)毛玻璃画中画 620×380，录屏继续播放，不遮挡操作。
- `full`：居中 1240×680 大卡片，仅用于画面静止的讲解点，≤5s。

## 3. 内置 kind 的动画编排（模板里已实现）
- **flow**：节点逐个弹入(0.45s 间隔) → 连线生长 → 光点沿路径流动。
- **compare**：左右两张卡依次滑入 → "VS" 弹出 → 条目逐行出现；左红右绿描边。
- **stat**：数字 0→目标值缓出滚动 (1.3s) + 弹性放大 → 标签淡入。
- **checklist**：行滑入 → 方框填绿+✓ 弹跳。
- **mascot**：emoji 角色弹入并持续上下呼吸 → 对话气泡弹出 → ✨⭐💫 星光依次飞出。
- **warning**：⚠️ 弹入并抖动 → 文案 → ✅ 正确做法。
- **timeline**：进度线生长，节点依次点亮并交替上下标注。

## 4. `custom`：AI 现写动画（对标"用 Claude 写 HTML 做视频"的效果）
```json
{"type":"broll","kind":"custom","mode":"pip","src_t":120,"dur":5,"title":"缓存命中",
 "html":"<div id='b1' style='position:absolute;left:60px;top:110px;font-size:64px;font-weight:900;opacity:0'>⚡ 3ms</div>",
 "script":"tl.fromTo(card.querySelector('#b1'),{opacity:0,y:30},{opacity:1,y:0,duration:.6,ease:'back.out(1.6)',immediateRender:true},S.t);"}
```
- `script` 是函数体，可用变量：`tl`(主时间轴) `card`(卡片 DOM) `S`(`{t:动画起点,w,h,full}`) `gsap`。
- 所有动画必须挂到 `tl` 上、用 `S.t` 作起点；**不得**用 `setTimeout/Date/Math.random`；不要动画 `left/top/width`（用 `x/y/scale`）；同一元素的 CSS transform 与 GSAP 不能同属性冲突。
- 卡片内坐标系是 `S.w × S.h` 像素，元素用 `position:absolute`。
- 复杂场景（3D、粒子、SVG 路径、Lottie）：读 `/hyperframes-animation` 的 adapters/blueprints，在 `overlay.html` 的 `BROLL` 对象里新增一个 kind（所有内置 kind 都是 `BROLL.xxx(o,S)` 函数，照写即可）。
- **质量标准**：清晰（一屏只讲一件事、文字 ≥ 26px）、可爱（emoji/圆角/弹性动效/星光点缀）、专业（对齐网格、统一圆角与描边、动效 ≤0.7s、有"入-停-出"完整节拍）、美观（只用设计令牌里的颜色）。

## 5. 提示框文案规范
- title ≤ 12 字，动词开头最佳（"点这里新建项目"）；body ≤ 30 字，只说"为什么/注意什么"，不复述画面。
- 一个提示框一个信息。需要强调坑点用 `tone:"warn"`，成功确认用 `success`，快捷键/技巧用 `tip`。
- `ring.x/y/w/h` 是相对整个画面的 0–1 坐标（左上为原点），从联系表目测，**宁大勿小**（外扩 10px 已内置）。
- 提示框默认放右侧；若圈选目标在右半屏，会自动放左侧。
