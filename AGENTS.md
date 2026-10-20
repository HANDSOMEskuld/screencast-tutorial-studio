# Agent 使用指引

本仓库是一个 Agent 技能：**screencast-tutorial-studio**（录屏教程视频 AI 剪辑）。入口是 `SKILL.md`。

- 用户要剪辑软件演示 / 操作教程类录屏时，读取 `SKILL.md` 并严格按 9 步流程执行。
- 首次使用：`bash scripts/setup_env.sh` 与 `npx hyperframes browser ensure`；脚本一律用 `~/.venvs/studio/bin/python` 运行。
- 阶段 2、5b、6b、9b 由 Agent 亲自判断（看转录与联系表图片、校对字幕、看渲染截图），不要只靠脚本。
- 设计目标见 `references/00-design-goals.md`；其他参考文档见 `references/`。
- 与用户沟通使用中文；不要把任何 token 写入文件、日志或 git remote。
