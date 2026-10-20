# screencast-tutorial-studio

录屏教程视频的 AI 全流程剪辑技能（Claude Code / 任何支持 SKILL.md 的 Agent）。
整合 HyperFrames（HTML→视频）+ OpenMontage（分阶段 Agent 流水线理念）+ appstoy-video-editing-v2（音画同步/EDL/母带）。

## 安装（新机器）
```bash
git clone https://github.com/HANDSOMEskuld/screencast-tutorial-studio ~/.claude/skills/screencast-tutorial-studio
bash ~/.claude/skills/screencast-tutorial-studio/scripts/setup_env.sh   # ffmpeg / venv / 字体
npx hyperframes browser ensure                                          # 渲染用 Chrome
```
可选增强（强烈建议一并安装，定制 B-roll 时用）：`heygen-com/hyperframes` 仓库的 `skills/*` 复制到 `~/.claude/skills/`。

## 交接文档
`REQUIREMENTS.md`（需求）· `ORIGINAL_REQUEST.md`（最初请求原文）· `HANDOFF.md`（进度/待办）· `AGENTS.md`（Agent 指引）· `PROMPTS.md`（提示词，含换机器引导）

## 状态
- ✅ 01–09 已在 49s 合成样片上全部跑通，真毛玻璃合成已目视确认
- ⚠ 待验证：真实录屏 + 真实 Whisper 转录；渲染速度；详见 HANDOFF.md
- 待改进想法见 SKILL.md 与下方提示词 B

## 提示词 A：日常剪辑
见仓库根目录 `PROMPTS.md`。
