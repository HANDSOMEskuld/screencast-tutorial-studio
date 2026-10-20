# 声音设计

## 人声链（04_render_cut 自动）
`highpass 80Hz → afftdn 去噪(nr=10) → 200Hz -2dB 去浑浊 → 3.2kHz +2.5dB 提亮 → 压缩 2.5:1 → loudnorm -16 LUFS`。每个切口 10ms 淡入淡出，杜绝爆音。外置麦克风与录屏内置音轨用 FFT 互相关对齐（01 步，精度毫秒级；峰值显著度 <5σ 时人工核对）。

## BGM（08_mix_audio）
- 来源优先级：用户提供文件 > `plan.bgm.file` > 程序化兜底 `gen_bgm.py`（calm-tech/upbeat/warm/tense，无版权风险但偏简单；条件允许请换成真实授权音乐，或用 OpenMontage `tools/audio/music_gen.py` 生成）。
- 选曲：软件教程用**低人声、稳定节拍、中低能量**的 lo-fi/ambient/轻电子。BPM 80–110。**绝不选有歌词的曲子**。
- 电平：基准 -23 dB；对人声**侧链闪避**（threshold .02, ratio 9, release 420ms）；带通 90Hz–9kHz 给人声让位。
- **按情绪曲线起伏**：开场 +3dB 抓耳 → 中段压低 → 高潮章 `chapter_db` 抬 +2~3 → 片尾淡出 4s。
- 低谷/踩坑章可 `mood:"tense"` 只需整体换曲，或降低 BGM 突出人声。

## 音效（自动 + 手动）
| 事件 | 默认音效 | 电平 |
|---|---|---|
| 视频 Hook | impact-bass-1 | .30 |
| 章节切换 | whoosh | .34 |
| callout / step | pop / click-soft | .30 |
| ring 圈选 | ping | .22 |
| B-roll 出现 | whoosh-short | .30 |
| bignote warn / success / info | error / chime / ping | .22/.30/.26 |
| 快进段开始 | whoosh-short | .22 |
可选音效（assets/sfx）：chime click click-soft error glitch-1/2/3 impact-bass-1/2 key-press notification ping pop riser sparkle typing whoosh whoosh-cinematic whoosh-short。`manifest.json` 有描述。
原则：**音效服务信息，不抢人声**；同类 0.4s 内去重；高潮前可手动加 `riser` 做 2s 铺垫，落点用 `impact-bass`/`sparkle`；整片音效 ≤ 1 个/1.2s。

## 母带
两遍 loudnorm：目标 **-15 LUFS**（YouTube 可到 -14），True Peak ≤ -1.5 dBFS，LRA ≤ 11；AAC 256k/48kHz。`09_finalize` 会复测并写入 qa_report。
