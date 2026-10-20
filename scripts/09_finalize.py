#!/usr/bin/env python3
"""
Step 9 · 合成成片 + 交付物 + 质检
产出: Final_<slug>.mp4 / captions.srt / chapters.txt / qa/ (关键帧联系表) / qa_report.md
质检含：响度、章节时长、B-roll/提示框密度、「静态空窗」检测(完播率关键：>8s 无任何视觉/听觉事件)
"""
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load, run, fmt_ts, probe


def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True); ap.add_argument("--slug", default="video")
    a = ap.parse_args(); w = Path(a.workdir); tl = load(w / "timeline.json"); edl = load(w / "edl.json")
    out = w / f"Final_{a.slug}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", w / "video_composited.mp4", "-i", w / "final_audio.m4a", "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out])
    caps = load(w / "captions.json") if (w / "captions.json").exists() else load(w / "captions_draft.json")
    (w / "captions.srt").write_text("\n".join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{re.sub(r'[*]{2}', '', c['text'])}\n" for i, c in enumerate(caps, 1)), encoding="utf-8")
    ch = tl["chapters"]; lines = ["00:00 开场"] + [f"{fmt_ts(c['start'])} {c['title']}" for c in ch if c["start"] >= 5]
    if ch and ch[0]["start"] < 5: lines = [f"00:00 {ch[0]['title']}"] + [f"{fmt_ts(c['start'])} {c['title']}" for c in ch[1:]]
    (w / "chapters.txt").write_text("\n".join(lines), encoding="utf-8")

    # ---- QA ----
    D = tl["duration"]; rep = [f"# 质检报告 · Final_{a.slug}.mp4", f"- 时长 {D:.1f}s ({D/60:.2f} min) | 实测 {probe(str(out))['duration']:.1f}s"]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    li = re.findall(r"I:\s+(-?[\d.]+) LUFS", r); tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    if li: rep.append(f"- 响度 {li[-1]} LUFS（目标 -14~-16）| True Peak {tp[-1] if tp else '?'} dBFS（需 ≤ -1.0）")
    ev = sorted([0.0, D] + [e["dst"][0] for e in edl["entries"][1:]] + [o["start"] for o in tl["overlays"]] + [s["t"] for s in tl["sfx"]] + [c["start"] for c in ch])
    gaps = [(x, y) for x, y in zip(ev, ev[1:]) if y - x > 8]
    rep.append(f"- 章节: " + " | ".join(f"{c['title']} {c['end']-c['start']:.0f}s" for c in ch))
    nb = sum(1 for o in tl["overlays"] if o["type"] == "broll"); nc = sum(1 for o in tl["overlays"] if o["type"] != "broll")
    rep.append(f"- B-roll {nb} 个 ({nb/(D/60):.1f}/分钟) | 提示框/步骤/大字报 {nc} 个 ({nc/(D/60):.1f}/分钟) | 音效 {len(tl['sfx'])} 个")
    rep.append("- ✅ 无超过 8s 的静态空窗" if not gaps else "- ⚠ 静态空窗(>8s 无剪辑点/浮层/音效，需补情绪点或 B-roll): " + ", ".join(f"{fmt_ts(x)}–{fmt_ts(y)}" for x, y in gaps))
    if D > 0 and tl["hook"].get("headline"): rep.append(f"- Hook: 「{tl['hook']['headline']}」 0–{tl['hook']['dur']:.1f}s")
    if not tl.get("cta"): rep.append("- ⚠ 缺少结尾 CTA")
    # 关键帧抽样供视觉检查
    qa = w / "qa"; qa.mkdir(exist_ok=True)
    pts = [min(D - 0.1, tl["hook"]["start"] + 1.2)] + [min(D - .1, o["start"] + min(o["dur"] * 0.6, 2.2)) for o in tl["overlays"][:30]] + [c["start"] + 1.5 for c in ch] + [max(0, D - 2)]
    for i, t in enumerate(sorted(set(round(p, 1) for p in pts if 0 <= p < D))):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(out), "-frames:v", "1", "-vf", "scale=960:-1", str(qa / f"qa_{i:02d}_{t:07.1f}s.jpg")])
    rep.append(f"- 关键帧已导出 {len(list(qa.glob('*.jpg')))} 张 → {qa}（请用图片查看逐张检查：遮挡、错字、溢出、字幕与浮层是否冲突）")
    (w / "qa_report.md").write_text("\n".join(rep), encoding="utf-8"); print("\n".join(rep))
    print(f"\n成片: {out}\n字幕: {w/'captions.srt'}\n章节: {w/'chapters.txt'}")


if __name__ == "__main__":
    main()
