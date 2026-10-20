# AI 提示词

## 0. 引导提示词（换机器时粘贴给那台机器的 AI Agent）
前提：那台机器已装 git、gh、node、python，并已登录 GitHub（`gh auth login`，或设置新的环境变量 `GH_TOKEN`），且执行过一次 `gh auth setup-git`。
```
请接手并继续完善我的 AI 视频剪辑技能项目，全程自动完成，不要问我无关问题：
1. 拉取项目：git clone https://github.com/HANDSOMEskuld/screencast-tutorial-studio ~/.claude/skills/screencast-tutorial-studio（已存在则 git pull）。
2. 依次完整阅读 AGENTS.md、REQUIREMENTS.md、HANDOFF.md、SKILL.md 和 references/ 下所有文档。REQUIREMENTS.md 是我的原始需求，不得偏离。
3. 运行 scripts/setup_env.sh 和 npx hyperframes browser ensure 准备环境。
4. 按 HANDOFF.md 的"已知问题/待办"从高到低逐项改进。每项都要在小样本上实际跑通并用图片检查效果，不要只改代码。
   如果我提供了真实录屏，优先用它完整跑一遍 9 步。
5. 新建分支 improve/<主题>，提交并 push，用 gh pr create --fill 创建 PR，把 PR 链接发给我。不要直接推 main。
6. 结束前更新 HANDOFF.md（进度、新踩坑、剩余待办），并包含在 PR 里。
7. 不要把任何 token 写进文件或 git remote。
```

## A. 剪辑一个新视频
```
使用 screencast-tutorial-studio 技能剪辑我的录屏教程。
素材：录屏 <视频路径>；高清音频 <音频路径，没有就写"无">。
工程目录：/app/videos/<slug>。平台：<YouTube/B站>，语言：中文，目标时长：约 <N> 分钟。
风格：Apple 毛玻璃 <深色/浅色>，主色 <#0A84FF>。BGM：<文件路径 / 自动生成>。
术语表（用于转录校正）：<产品名、命令、专有名词>
要求：严格按技能 SKILL.md 的 9 步流程执行，阶段 2 先通读转录并逐张查看联系表，
给我看宏观诊断（要重排哪些、为什么）和 Hook/章节/情绪曲线方案，我确认后再继续渲染。
先用 --glass fake --quality draft 出预览，我确认后再出终版。最后给我 Final 成片、字幕 srt、章节 chapters.txt 和 publish.md（标题/简介/标签）。
```

## B. 在新机器上继续完善这个技能
```
这台机器上已克隆技能 ~/.claude/skills/screencast-tutorial-studio（来自 GitHub HANDSOMEskuld/screencast-tutorial-studio）。
请先阅读它的 SKILL.md、README.md 和 references/ 全部文档，然后：
1. 运行 scripts/setup_env.sh，并用一段真实录屏（我会提供）完整跑通 9 步，记录每一步的耗时、报错与效果问题。
2. 重点验证并修复：07 透明叠层(webm alpha)+真实毛玻璃合成、08 混音、09 质检；真实语音转录下 03 的口水词/停顿删除是否过度或不足。
3. 对照 references/02、03，检查提示框/B-roll/章节进度条的视觉质量（用 hyperframes snapshot 抽帧看图），
   按"Apple 液态玻璃、清晰可爱、专业"的标准迭代 templates/overlay.html，并新增更多 B-roll 类型。
4. 想办法加速叠层渲染（当前 CPU 约 8 帧/秒）：例如只渲染有浮层的时间段、降低叠层帧率、拆分并行。
5. 每次改动都要在小样本上验证，更新 SKILL.md/references，然后 git commit 并 push 到新分支，创建 PR 给我。
```

## C. 只做某一步（例：只重做字幕校对）
```
使用 screencast-tutorial-studio，工程目录 <W>。只重做阶段 5b：读取 captions_draft.json，按 references/05-captions-chapters.md 校对，
术语以 <术语表> 为准，保存为 captions.json，然后重跑 06→09。
```
