# Agent 指引

这是 `screencast-tutorial-studio`：录屏教程视频 AI 剪辑技能。接手前**按顺序阅读**：
1. `REQUIREMENTS.md`：用户的完整需求（北极星）
2. `HANDOFF.md`：当前进度、待办、踩坑、git 流程
3. `SKILL.md`：9 步工作流与硬规则
4. `references/`：分析手册、视觉系统、B-roll 库、音频、字幕、质检

## 规则
- 先 `bash scripts/setup_env.sh` 和 `npx hyperframes browser ensure`，用 `~/.venvs/studio/bin/python` 运行脚本。
- 改动必须在小样本上实际跑过并目视检查（`npx hyperframes snapshot` / `qa/*.jpg`），不要只改代码不验证。
- 在新分支 `improve/<主题>` 上工作，提交后 push 并 `gh pr create --fill`；**不要直接推 main**。
- 每次会话结束更新 `HANDOFF.md`（状态、新踩坑、剩余待办）。
- 不在仓库或日志中写入任何 token；认证用 `gh auth login` 或环境变量 `GH_TOKEN`。
- 用中文与用户沟通。
