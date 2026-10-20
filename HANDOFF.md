# 交接与进度（每次会话结束必须更新本文件）

最后更新：2026-10-20，由首个开发会话写入。

## 当前状态
| 步骤 | 状态 | 说明 |
|---|---|---|
| 01 合并/转录/分析包 | ✅ 合成数据通过 | 音画偏移 -0.5s 被正确检出。**未用真实录屏 + 真实 Whisper 测过** |
| 02 校验 | ✅ | |
| 03 EDL / 04 粗剪 | ✅ 合成数据 | 真实语音下口水词删除是否过度/不足未知 |
| 05 时间轴/字幕初稿 | ✅ | |
| 06 叠层工程 | ✅ | `hyperframes check` lint 0 错误 |
| 07 渲染+合成 | ✅ 49s 样片通过 | 真毛玻璃已目视确认有效（背景被模糊、进度条三态、提示框、圈选、字幕正常）。CPU 渲染慢（约 8 帧/秒，仅 2.2GB 内存机器） |
| 08 混音 | ✅ | 实测 -15.1 LUFS，TP -2.9 |
| 09 成片/质检 | ✅ | 报告与关键帧正常输出 |

## 已知问题 / 待办（按优先级）
1. **用真实录屏 + 真实 Whisper 转录完整跑一遍**，调 `03_build_edl.py` 的阈值，检查 AI 阶段 2 的流程是否顺手。
2. **加速叠层渲染**：只渲染有浮层的时间段、降低叠层帧率、或拆分并行。目前两遍渲染（叠层+遮罩）较慢。
3. 毛玻璃面板边缘是否"突然出现"（遮罩与叠层同步性）。
4. 新增更多 B-roll 类型；继续提升动画的可爱度与精致度（对标"Claude 写 HTML 做视频"的水平）。
5. 替换 `gen_bgm.py` 的简易合成 BGM：接入真实授权曲库，或 OpenMontage 的音乐生成工具。
6. 验证 4K、60fps、`--style light`、竖屏（9:16）路径。
7. 测试用 plan 里故意放了重叠浮层，校验器能捕获；可再做一个"干净样例" `examples/` 方便回归测试。

## 回归测试（合成素材）
没有真实素材时，用 ffmpeg `testsrc2` + `sine` 生成 60s 视频，麦克风音频人为偏移 0.5s，手写 `transcript.json`（词级时间戳）+ `story_plan.json`，依次跑 01→09。注意 06 之后用 `npx hyperframes check` 检查。

## 踩坑记录
- **后台渲染必须 `setsid -f`**，否则父 shell 退出时 HyperFrames 报 `render_cancelled_parent_exited`。
- 系统 `python3` 没有 numpy，用 `~/.venvs/studio/bin/python`（`setup_env.sh` 创建）。
- ffmpeg 解码 WebM alpha 必须 `-c:v libvpx-vp9` 放在 `-i` 之前。
- `backdrop-filter` 在透明叠层里看不到下层视频，所以真毛玻璃靠"遮罩 WebM + ffmpeg alphamerge"。
- 不要动画 `left/top`，用 `x/y`；`.chk` 类名与 HyperFrames 内部冲突，已改 `.cki`。
- 许可：不得复制 OpenMontage 源码（AGPL）。

## Git 工作流
- 仓库：`HANDSOMEskuld/screencast-tutorial-studio`（私有）。`main` 为稳定分支，**不要直接推 main**。
- 流程：`git checkout -b improve/<主题>` → 改动并在样片上验证 → 更新本文件 → `git commit` → `git push -u origin HEAD` → `gh pr create --fill`，把 PR 链接给用户。
