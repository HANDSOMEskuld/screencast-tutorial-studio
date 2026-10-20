# AI 提示词

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
