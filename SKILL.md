---
name: screencast-tutorial-studio
description: 录屏教程视频的 AI 全流程剪辑师（整合 HyperFrames + OpenMontage 方法论 + appstoy 流水线）。输入 OBS 录屏 + 高清外置音频，AI 分析并重排整体逻辑，去口水词/停顿/失败内容粗剪，自动加 Apple 毛玻璃风格提示框、圈选、B-roll 动画、顶部章节进度条、AI 校对字幕、BGM 与音效、开篇 Hook 与结尾 CTA，输出可直接上传 YouTube/Bilibili 的成片。当用户要剪辑软件演示、操作教程、录屏讲解类视频，或提到"剪视频/粗剪/加字幕/加B-roll/章节进度条/合并音频"时使用。
---

# 录屏教程 AI 剪辑工作室 (screencast-tutorial-studio)

目标：把"一段录得不完美的录屏 + 麦克风音频"变成**逻辑清晰、节奏紧凑、动效精良、能留住人**的教程视频。
脚本负责确定性的活（对齐/剪切/渲染/混音），**AI 负责所有"判断"**：整体逻辑、剪辑取舍、B-roll 位置与内容、提示框文案、字幕纠错、情绪曲线。

> 路径约定：`$SK` = `~/.claude/skills/screencast-tutorial-studio`；`$PY` = `~/.venvs/studio/bin/python`；`$W` = 工程目录（每个视频一个，如 `/app/videos/<slug>`）。
> 首次使用先运行 `bash $SK/scripts/setup_env.sh`，再 `npx hyperframes browser ensure`（下载渲染用 Chrome）。

## 总流程（9 步，★ = 必须由 AI 亲自完成）

| # | 阶段 | 命令 / 动作 | 产物 |
|---|---|---|---|
| 0 | 需求确认 | 问清：素材路径、平台(YouTube/B站/抖音)、语言、目标时长、品牌色、是否有 BGM；默认 16:9、Apple 暗色玻璃、自然档剪辑 | — |
| 1 | 合并 + 转录 + 分析包 | `$PY $SK/scripts/01_merge_and_analyze.py --video V.mp4 --audio MIC.wav --workdir $W --lang zh --prompt "术语1, 术语2"` | `master.mp4` `transcript.txt` `analysis_pack/sheets/*.jpg` `motion.json` |
| 2 ★ | **AI 分析 → story_plan.json** | 读 `transcript.txt` + 用 read 逐张看 `sheets/*.jpg`，按 `references/01-ai-analysis-playbook.md` 写 `$W/story_plan.json`（schema 见 `references/plan-schema.md`） | `story_plan.json` |
| 2b | 校验 | `$PY $SK/scripts/02_validate_plan.py --workdir $W`（ERROR 必须修，WARN 逐条处理） | — |
| 3 | 粗剪 EDL | `$PY $SK/scripts/03_build_edl.py --workdir $W --preset natural` | `edl.json`（含删除审计） |
| 4 | 渲染粗剪 | `$PY $SK/scripts/04_render_cut.py --workdir $W` | `cut_video.mp4` `voice_master.wav` |
| 5 | 时间轴 + 字幕初稿 | `$PY $SK/scripts/05_resolve_timeline.py --workdir $W` | `timeline.json` `captions_draft.json` |
| 5b ★ | **AI 校对字幕** | 按 `references/05-captions-chapters.md` 修错字/术语/断句/高亮，存 `$W/captions.json` | `captions.json` |
| 6 | 生成叠层工程 | `$PY $SK/scripts/06_build_overlay_project.py --workdir $W [--glass real\|fake] [--style dark\|light]`，然后 `cd $W/overlay_project && npx hyperframes check` | `overlay_project/` `mask_project/` |
| 6b ★ | 看效果 | `npx hyperframes snapshot --at <秒,秒>` 抽帧用图片查看，修正文案/位置后重新生成 | — |
| 7 | 渲染 + 合成 | `$PY $SK/scripts/07_render_and_composite.py --workdir $W`（预览用 `--quality draft --fps 24`） | `video_composited.mp4` |
| 8 | 混音 | `$PY $SK/scripts/08_mix_audio.py --workdir $W --bgm auto\|文件\|none` | `final_audio.m4a` |
| 9 | 成片 + 质检 | `$PY $SK/scripts/09_finalize.py --workdir $W --slug My_Video` | `Final_*.mp4` `captions.srt` `chapters.txt` `qa_report.md` `qa/*.jpg` |
| 9b ★ | 验收 | 读 `qa_report.md`，用图片查看 `qa/*.jpg`；对照 `references/06-qa-checklist.md`；有问题回到对应步骤修 | 交付 + 写 `publish.md`(标题/简介/章节/标签) |

**长视频提示**：叠层渲染在 CPU 上较慢（1 分钟成片约数分钟）。先用 `--glass fake --quality draft` 快速审阅，定稿再 `--glass real --quality looks`。每步产物都落盘，失败可从该步重跑。

## 阶段 2 要点（AI 的核心价值，必须认真做）

先读 `references/01-ai-analysis-playbook.md`，然后：
1. **通读转录**，用一句话概括这个视频要教会观众什么、观众是谁、完成后能得到什么（"承诺"）。
2. **看联系表**（`read` 图片）：对照转录判断每段画面是在"操作 / 等待 / 讲解静止页 / 报错"。
3. **宏观诊断**：现有顺序是否是最佳教学顺序？标出需要前移的结论、后移的补充、应拆章或合并的内容，写进 `diagnosis.macro`，再据此**重排 segments**（segments 的顺序即成片顺序，源区间可乱序、可复用做预告片）。
4. **微观诊断**：找出重复讲解、前后矛盾（以最终正确版本为准）、失败重录（留最后一次成功）、隐私信息（密码/Key/邮箱，直接剔除或让提示框遮盖）、无意义等待 → `diagnosis.micro` + 不要放进 segments。
5. **设计情绪曲线**：选一种形状（默认"痛点低谷→爽感高点"），给每章标 energy/valence，决定哪里放 B-roll、大字报、BGM 抬升。
6. **设计 Hook**（前 3–5 秒）：从全片挑最有冲击力的结果画面做 `teaser_src` + 一句 ≤ 22 字的 headline（公式见 playbook）。
7. **布置 overlays**：每分钟 ≥ 1 个 B-roll、2–4 个提示框；任何连续 8 秒无视觉/听觉事件的"空窗"都要补情绪点。每个 overlay 要有存在理由。
8. **写 CTA**：结尾 4–6 秒，点赞/关注/评论引导，可 `extend` 冻结尾帧延长 1–2 秒。

## 硬规则（违反即不合格）

1. **绝不遮挡正在操作的区域**：提示框只放右侧/左侧留白；底部 18% 留给字幕；操作区用 `ring` 圈选而不是盖住。看联系表判断鼠标/菜单所在位置，选 `pos`。
2. **不切断主画面**：B-roll 默认 `mode:"pip"`（画中画毛玻璃卡片）。`mode:"full"` 只用于画面静止的讲解点，且 ≤ 5 秒，矢量动画不得低清。
3. **每个剪辑决策有据可查**：`why` 必填；`edl.json.removed` 保留审计。
4. **静默 ≠ 废话**：画面在动的静默是演示操作，保留或加速；只有画面静止的静默才删。
5. **进度条语义固定**：已完成(绿勾) / 进行中(主色+进度填充) / 未开始(暗)；同一胶囊内禁止左右渐变色（避免误读为滑块）。
6. **音频专业**：人声 -15~-16 LUFS，TP ≤ -1.0 dBFS，切口 10ms 淡变，BGM 对人声侧链闪避。
7. **所有文字用简体中文**（除非用户另有要求），错别字/术语必须校对，产品名大小写按官方写法。

## 与其他技能的关系（本技能自包含，下列为增强）

- **/hyperframes-core、/hyperframes-animation、/hyperframes-keyframes**：写 `broll.kind:"custom"` 的定制动画、或改造 `templates/overlay.html` 时先读，遵守其确定性规则（单一 paused GSAP 时间轴、不用 Math.random/Date）。
- **/hyperframes-registry**：需要现成特效/转场块（如光效、粒子）时搜索安装。
- **/media-use**：需要生成/获取图片、图标、素材时使用。
- **OpenMontage（/app/OpenMontage）**：需要 AI 生成配乐/配音/图片时，参考 `/app/OpenMontage/tools/audio/`（music_gen、elevenlabs 等，需 API Key）。本技能不依赖它即可完成全流程。
- 参考资料：`references/` 下 7 份文档；设计来源与许可见 `references/CREDITS.md`。

## 目录

```
SKILL.md
scripts/   setup_env.sh common.py 01…09_*.py gen_bgm.py
templates/ overlay.html(HyperFrames 叠层模板：章节条/字幕/提示框/圈选/B-roll库/CTA)  gsap.min.js
assets/sfx/ 20 个音效(whoosh/pop/chime/error/riser/impact…)+ manifest.json
references/ 01-ai-analysis-playbook 02-visual-system-apple-glass 03-broll-library
            04-audio-design 05-captions-chapters 06-qa-checklist plan-schema CREDITS
```
