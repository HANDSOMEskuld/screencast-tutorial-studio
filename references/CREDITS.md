# 来源与许可
本技能是对以下三个来源的**方法论整合**，叠层模板、脚本与文档均为重新编写，未复制 OpenMontage 源码：
- **HyperFrames** (heygen-com/hyperframes, Apache-2.0)：HTML→视频渲染框架；本技能用其 `render --format webm` 输出透明叠层，并遵循其确定性动画规范。`templates/gsap.min.js` 为 GSAP 3.14.2（GreenSock 标准许可）。
- **OpenMontage** (calesthio/OpenMontage, AGPL-3.0)：多管线 Agent 视频生产理念——分阶段 + 产物落盘 + 人在回路审查。仅借鉴流程思想。
- **appstoy-video-editing-v2**：FFT 音画同步、EDL 决策、EBU R128 母带、玻璃 UI 设计令牌与"绝不遮挡操作"等硬规则；`assets/sfx/` 来自该项目，音效来源 Pixabay（Pixabay Content License，见 appstoy 的 CREDITS）。
BGM 兜底由 `scripts/gen_bgm.py` 程序合成，无版权问题。
