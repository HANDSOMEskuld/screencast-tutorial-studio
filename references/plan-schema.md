# story_plan.json 规范

所有时间一律是**源素材时间（秒，master.mp4 时间轴）**。脚本 05 会通过 EDL 自动映射到成片时间。

```jsonc
{
  "meta": {
    "title": "视频标题", "language": "zh", "platform": "youtube|bilibili|douyin",
    "style": "dark|light",            // Apple 玻璃深色/浅色
    "accent": "#0A84FF",              // 主色，默认 Apple 蓝
    "fillers_extra": ["对吧"]         // 该视频博主特有的口头禅（额外删除）
  },
  "diagnosis": {
    "macro": [{"issue": "结论放在最后，开头无动机", "fix": "把成果演示前置做 Hook，再回到第 1 步"}],
    "micro": [{"type": "repeat|contradiction|failed_take|dead_air|privacy", "src": [123.0, 140.5], "action": "drop", "why": "第一次安装报错，2:40 重录成功"}]
  },
  "emotion_curve": {
    "shape": "man_in_hole|cinderella|rags_to_riches|rise_fall_rise",
    "beats": [{"chapter": "c1", "energy": 0.9, "valence": 0.2, "note": "痛点低谷"}]   // energy 节奏强度 0-1, valence 情绪正负 0-1
  },
  "hook": {
    "teaser_src": [412.0, 417.0],     // 可选：取未来最爽的画面做 3-5s 预告；省略则只在首段叠加标题
    "headline": "3 分钟搞定，再也不踩坑",   // ≤ 22 字
    "sub": "跟着做一遍就会", "dur": 4.0, "sfx": "impact-bass-1"
  },
  "chapters": [{"id": "c1", "title": "痛点"}],         // 4-7 章，标题 2-6 字
  "segments": [                                       // 顺序 = 成片顺序；章节必须连续
    {"id": "s1", "src": [2.0, 55.3], "chapter": "c1", "role": "setup|step|payoff|recap|cta",
     "why": "说明痛点与目标", "speed": null}           // speed 仅用于纯操作段强制加速
  ],
  "overlays": [
    {"type": "callout", "src_t": 64.0, "dur": 3.5, "title": "先打开终端", "body": "按 ⌘+空格 搜索 Terminal",
     "icon": "💻", "tone": "info|warn|success|tip", "pos": "auto|right|left|right-low|left-low",
     "ring": {"x": 0.42, "y": 0.31, "w": 0.18, "h": 0.07},   // 归一化坐标：圈住要点击的位置
     "spot": true,                                            // 聚光灯：暗化其余区域
     "sfx": true},                                            // false 关闭自动音效；或字符串指定音效名
    {"type": "step", "src_t": 60.0, "dur": 3, "num": 1, "text": "打开终端"},
    {"type": "bignote", "src_t": 90.0, "dur": 2.5, "text": "这一步最容易出错", "sub": "注意版本号", "tone": "warn"},
    {"type": "broll", "src_t": 70.0, "dur": 5, "kind": "flow", "mode": "pip|full", "pos": "right|left", "title": "原理",
     "nodes": [{"label": "命令", "icon": "⌨️"}, {"label": "下载", "icon": "☁️"}]}
  ],
  "sfx": [{"src_t": 200.0, "name": "chime", "gain": 0.3}],   // 额外手动音效；overlay/章节/快进已自动配音效
  "bgm": {"file": null, "mood": "calm-tech|upbeat|warm|tense", "chapter_db": {"c3": 3}},  // chapter_db: 章节相对音量(dB)
  "cta": {"text": "觉得有用？", "dur": 5, "extend": 1.5, "items": ["点赞", "关注", "评论区聊聊"], "icons": ["👍", "🔔", "💬"]}
}
```

## B-roll 各 kind 的参数
| kind | 参数 | 适用 |
|---|---|---|
| flow | `nodes:[{label,icon}]`(2-5 个) | 原理、数据流、步骤关系 |
| compare | `left:{title,items[]}` `right:{...}` | 错误 vs 正确、旧 vs 新 |
| stat | `value, suffix, prefix, decimals, label` | 数字冲击：速度、耗时、提升 |
| checklist | `items[]`(≤5) | 前置条件、总结清单 |
| mascot | `emoji, text` | 情绪点、小贴士、鼓励（可爱） |
| warning | `text, fix` | 坑点预警 |
| timeline | `steps[]`(3-6) | 路线图、全流程预览 |
| custom | `html, script` | 定制动画（见 03-broll-library.md） |

## 常见错误
- 章节被其他章节打断 → 校验器 ERROR。
- `src_t` 落在被剪掉的区域 → 自动吸附到下一保留点并 WARN。
- 同时间提示框与 B-roll 都在右侧 → 校验器 WARN，请错开或换 `pos`。
- 文案过长：callout.title ≤ 12 字，body ≤ 30 字；bignote.text ≤ 14 字。
