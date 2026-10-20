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

## 状态
- ✅ 已测：01 合并对齐、02 校验、03 EDL、04 渲染粗剪、05 时间轴、06 叠层工程（HyperFrames lint 通过）
- ⚠ 待充分验证：07 透明叠层渲染+真实毛玻璃合成、08 混音、09 成片/质检；真实语音转录（测试用的是合成数据）
- 待改进想法见 SKILL.md 与下方提示词 B

## 提示词 A：日常剪辑
见仓库根目录 `PROMPTS.md`。
