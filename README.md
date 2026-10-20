# screencast-tutorial-studio

**录屏教程视频的 AI 剪辑技能**（Agent Skill，适用于 Claude Code 及任何支持 `SKILL.md` 的 Agent）。

输入「录屏 + 高清外置音频」，由 AI 分析并重排整体逻辑，自动完成粗剪去噪、Apple 毛玻璃风格提示框与圈选、B-roll 动画、顶部章节进度条、AI 校对字幕、BGM 与音效、开篇 Hook 与结尾互动引导，输出可直接上传 YouTube / Bilibili 的成片。适合软件使用演示、操作教程类视频。

## 能做什么
| 能力 | 说明 |
|---|---|
| 音视频合并 | FFT 互相关自动对齐外置麦克风与录屏 |
| AI 流程分析 | 宏观重排顺序、微观处理重复/矛盾/失败/隐私 → `story_plan.json` |
| 粗剪去噪 | 去口水词、语气词、停顿；纯操作等待自动加速 |
| B-roll | flow / compare / stat / checklist / mascot / warning / timeline / custom 动画 |
| 提示框与动效 | 毛玻璃 callout、ring 圈选、step 角标、bignote 大字报 |
| 字幕 | 词级转录 + AI 校对，导出烧录与 `.srt` |
| 章节进度条 | 顶部三态：已播放 / 正在播放 / 未播放 |
| 声音 | 人声链、BGM 侧链闪避、自动音效，-15 LUFS 母带 |
| 节奏与留存 | 3–5s Hook、情绪曲线、空窗检测、结尾 CTA |
| 风格 | Apple 液态玻璃，真实背景模糊；深色 / 浅色 |

## 安装
```bash
git clone https://github.com/HANDSOMEskuld/screencast-tutorial-studio ~/.claude/skills/screencast-tutorial-studio
bash ~/.claude/skills/screencast-tutorial-studio/scripts/setup_env.sh   # ffmpeg / Python 虚拟环境 / 字体
npx hyperframes browser ensure                                          # 渲染用 Chrome
```
依赖：git、node、python3。私有仓库需先 `gh auth login`（或设置 `GH_TOKEN`）。
可选：把 `heygen-com/hyperframes` 的 `skills/*` 复制到 `~/.claude/skills/`，定制 B-roll 时更方便。

## 使用
对 Agent 说：
```
使用 screencast-tutorial-studio 技能剪辑我的录屏教程。
素材：录屏 <视频路径>；高清音频 <音频路径，没有写"无">。
工程目录：<如 ~/videos/my-video>。平台：<YouTube/B站>，语言：中文，目标时长：约 <N> 分钟。
风格：Apple 毛玻璃 <深色/浅色>，主色 <#0A84FF>。BGM：<文件路径 / 自动生成>。
术语表：<产品名、命令、专有名词>
先给我看宏观诊断（要重排哪些、为什么）和 Hook/章节/情绪曲线方案，确认后再渲染；先出 draft 预览，确认后再出终版。
交付：成片、captions.srt、chapters.txt、publish.md。
```
只做某一步（例：重做字幕校对）：
```
使用 screencast-tutorial-studio，工程目录 <W>。只重做阶段 5b：校对 captions_draft.json，术语以 <术语表> 为准，保存 captions.json，然后重跑 06→09。
```

## 工作流（9 步）
合并+转录 → **AI 分析成 story_plan.json** → 校验 → EDL 粗剪 → 渲染粗剪 → 时间轴+字幕草稿 → **AI 校对字幕** → 叠层工程 → 渲染合成 → 混音 → 成片+质检。
详细命令与硬规则见 [`SKILL.md`](SKILL.md)。

## 目录
```
SKILL.md      技能入口：9 步流程与硬规则
AGENTS.md     给 Agent 的使用指引
scripts/      01…09 流水线脚本、setup_env.sh、gen_bgm.py
templates/    overlay.html（HyperFrames 叠层模板）、gsap.min.js
assets/sfx/   20 个音效 + manifest.json
references/   设计目标、AI 分析手册、视觉系统、B-roll 库、音频、字幕章节、质检、plan 规范、来源许可
examples/     make_sample.py：生成合成样例，用于自检
```

## 已知限制
- CPU 渲染较慢，建议先 `--glass fake --quality draft --fps 24` 预览。
- 默认 BGM 为程序合成的简易版，可用 `--bgm` 指定授权音乐。
- 4K / 60fps / 竖屏路径未充分验证。

## 来源与许可
整合 HyperFrames、OpenMontage（仅借鉴流程理念）与 appstoy 流水线的方法论，详见 [`references/CREDITS.md`](references/CREDITS.md)。
