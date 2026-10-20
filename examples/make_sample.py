#!/usr/bin/env python3
"""生成干净回归样例：60s 合成录屏 + 偏移 0.5s 的麦克风音频 + 词级 transcript.json + story_plan.json。
用法: ~/.venvs/studio/bin/python examples/make_sample.py /tmp/sample   然后依次跑 01(--skip-transcribe)→09。"""
import json, subprocess, sys
from pathlib import Path

W = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/sample"); W.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=60", "-f", "lavfi",
                "-i", "anoisesrc=d=60:c=pink:r=48000:a=0.2:seed=7", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(W / "screen.mp4")], check=True)
# 麦克风音频：与录屏内置音轨同源宽带信号，整体延后 0.5s（用于验证对齐）
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=60:c=pink:r=48000:a=0.2:seed=7,adelay=500|500",
                "-t", "60", str(W / "mic.wav")], check=True)
SENT = ["嗯 大家好 今天 我们 来 讲 怎么 部署 项目", "那个 先 打开 终端 输入 命令", "然后 点击 新建 项目 按钮",
        "这里 选择 你的 仓库", "嗯 等待 构建 完成", "构建 成功 之后 就是 这样", "最后 我们 打开 域名 看看 效果", "好了 这就是 全部 内容"]
FILL = {"嗯", "那个", "然后"}
segs, t = [], 2.0
for i, s in enumerate(SENT):
    words, ws = [], s.split(); st = t
    for w in ws:
        words.append({"start": round(t, 3), "end": round(t + 0.32, 3), "word": w, "prob": 0.95}); t += 0.42
    segs.append({"id": i, "start": st, "end": round(t - 0.1, 3), "text": "".join(ws), "words": words}); t += 6.0
(W / "transcript.json").write_text(json.dumps({"language": "zh", "duration": 60, "segments": segs}, ensure_ascii=False))
plan = {"meta": {"title": "部署示例", "language": "zh", "platform": "bilibili", "style": "dark"},
 "diagnosis": {"macro": [], "micro": []},
 "emotion_curve": {"shape": "man_in_hole", "beats": [{"chapter": "c1", "energy": .9, "valence": .3}, {"chapter": "c2", "energy": .6, "valence": .5}, {"chapter": "c3", "energy": .9, "valence": .9}]},
 "hook": {"headline": "3 分钟部署上线", "sub": "跟着做一遍就会", "dur": 4.0, "sfx": "impact-bass-1"},
 "chapters": [{"id": "c1", "title": "准备"}, {"id": "c2", "title": "部署"}, {"id": "c3", "title": "验收"}],
 "segments": [{"id": "s1", "src": [2, 20], "chapter": "c1", "role": "setup", "why": "开场与准备"},
              {"id": "s2", "src": [20, 40], "chapter": "c2", "role": "step", "why": "核心操作"},
              {"id": "s3", "src": [40, 58], "chapter": "c3", "role": "payoff", "why": "结果展示"}],
 "overlays": [
  {"type": "callout", "src_t": 9, "dur": 3.5, "title": "先打开终端", "body": "按 ⌘+空格 搜索 Terminal", "icon": "💻", "tone": "info", "pos": "right", "ring": {"x": .2, "y": .3, "w": .15, "h": .1}},
  {"type": "broll", "src_t": 14, "dur": 4, "kind": "flow", "mode": "pip", "title": "原理", "nodes": [{"label": "命令", "icon": "⌨️"}, {"label": "构建", "icon": "🔨"}, {"label": "上线", "icon": "🚀"}]},
  {"type": "step", "src_t": 21, "dur": 3, "num": 1, "text": "新建项目"},
  {"type": "bignote", "src_t": 30, "dur": 2.5, "text": "这一步最容易出错", "sub": "注意选对仓库", "tone": "warn"},
  {"type": "broll", "src_t": 36, "dur": 4, "kind": "mascot", "mode": "pip", "pos": "left", "emoji": "🤔", "text": "别急 马上好"},
  {"type": "broll", "src_t": 42, "dur": 4, "kind": "stat", "mode": "pip", "value": 40, "suffix": "秒", "label": "从 40 分钟到 40 秒"},
  {"type": "broll", "src_t": 49, "dur": 4, "kind": "checklist", "mode": "pip", "title": "回顾", "items": ["打开终端", "新建项目", "选仓库"]}],
 "cta": {"text": "觉得有用？", "dur": 5, "extend": 1.5, "items": ["点赞", "关注", "评论区聊聊"], "icons": ["👍", "🔔", "💬"]}}
(W / "story_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
print("样例已生成:", W)
