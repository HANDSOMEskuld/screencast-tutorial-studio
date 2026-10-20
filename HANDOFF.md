# 交接与进度（每次会话结束必须更新本文件）

最后更新：2026-10-20，第二次会话（improve/render-speed）。

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
2. **加速叠层渲染**（部分完成）：遮罩改为半分辨率 + draft + `--vp9-cpu-used 5`，31s 样例两遍渲染+合成总计 142s（此前约 190s+）。剩余：章节条常驻所以无法按"有浮层时段"裁剪；`BeginFrame did not run` 说明仍走慢速截图路径，可研究 chrome 参数/GPU；有真实 CPU 多核机时试 `--workers`。
3. 毛玻璃面板边缘（遮罩与叠层同步性）：半分辨率遮罩在样例上边缘干净，已目视确认；真实复杂画面仍待验。
4. 新增更多 B-roll 类型；继续提升动画的可爱度与精致度（对标"Claude 写 HTML 做视频"的水平）。
5. 替换 `gen_bgm.py` 的简易合成 BGM：接入真实授权曲库，或 OpenMontage 的音乐生成工具。
6. 验证 4K、60fps、`--style light`、竖屏（9:16）路径。
7. ~~干净样例~~ 已加 `examples/make_sample.py`（见下）。

## 回归测试（合成素材）
没有真实素材时，用 ffmpeg `testsrc2` + `sine` 生成 60s 视频，麦克风音频人为偏移 0.5s，手写 `transcript.json`（词级时间戳）+ `story_plan.json`，依次跑 01→09。注意 06 之后用 `npx hyperframes check` 检查。

## 干净回归样例
`~/.venvs/studio/bin/python examples/make_sample.py /tmp/sample` 生成 60s 视频 + 偏移 0.5s 的同源噪声麦克风 + transcript.json + story_plan.json；
然后 `01 --skip-transcribe`（应检出 -0.5000s，148σ）→ 02…05 → `cp captions_draft.json captions.json` → 06 → 07 → 08 → 09。本会话已全流程跑通。

## 本会话说明
- 没有真实录屏，待办 1 仍未完成（仍是最高优先级）。
- 本会话机器 2 核/约 1GB 内存；叠层 1280x720 约 11fps，遮罩 640x360 约 23fps。

## 踩坑记录
- 旧版样例用不相关的 sine 与噪声做对齐只有 2.8σ，样例须用同源信号。
- 新增 06 参数 `--mask-scale`（默认 0.5），`overlay_meta.json` 增加 mw/mh。
- **后台渲染必须 `setsid -f`**，否则父 shell 退出时 HyperFrames 报 `render_cancelled_parent_exited`。
- 系统 `python3` 没有 numpy，用 `~/.venvs/studio/bin/python`（`setup_env.sh` 创建）。
- ffmpeg 解码 WebM alpha 必须 `-c:v libvpx-vp9` 放在 `-i` 之前。
- `backdrop-filter` 在透明叠层里看不到下层视频，所以真毛玻璃靠"遮罩 WebM + ffmpeg alphamerge"。
- 不要动画 `left/top`，用 `x/y`；`.chk` 类名与 HyperFrames 内部冲突，已改 `.cki`。
- 许可：不得复制 OpenMontage 源码（AGPL）。

## Git 工作流
- 仓库：`HANDSOMEskuld/screencast-tutorial-studio`（私有）。`main` 为稳定分支，**不要直接推 main**。
- 流程：`git checkout -b improve/<主题>` → 改动并在样片上验证 → 更新本文件 → `git commit` → `git push -u origin HEAD` → `gh pr create --fill`，把 PR 链接给用户。
