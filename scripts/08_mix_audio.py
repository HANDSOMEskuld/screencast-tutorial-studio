#!/usr/bin/env python3
"""
Step 8 · 声音设计：人声 + BGM(侧链闪避 + 按章节情绪起伏) + 音效 → 两遍 loudnorm 母带 → final_audio.m4a
"""
from __future__ import annotations
import argparse, json, subprocess, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load, run, SFX_DIR, need

db = lambda x: 10 ** (x / 20)


def bgm_envelope(tl, base_db):
    """按章节 gain_db 生成线性插值的音量表达式（bgm.chapter_db: {章节id: 相对dB}）。默认：hook 偏高→中段压低→结尾抬高"""
    ch = tl["chapters"]; cfg = (tl.get("bgm") or {}).get("chapter_db", {})
    pts = [(0.0, base_db + 3)]
    for i, c in enumerate(ch):
        off = cfg.get(c["id"], 0 if 0 < i < len(ch) - 1 else (2 if i else 0))
        pts += [(c["start"] + 0.8, base_db + off), (c["end"] - 0.8, base_db + off)]
    pts.append((tl["duration"], base_db + 2))
    pts = sorted(set((round(t, 2), g) for t, g in pts))
    expr = f"{db(pts[-1][1]):.4f}"
    for (t0, g0), (t1, g1) in reversed(list(zip(pts, pts[1:]))):
        a, b = db(g0), db(g1)
        expr = f"if(lt(t,{t1}),{a:.4f}+({b - a:.4f})*(t-{t0})/{max(0.01, t1 - t0):.2f},{expr})"
    return expr


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True)
    ap.add_argument("--bgm", default="auto", help="BGM 文件路径 | auto(程序化生成) | none")
    ap.add_argument("--mood", default=None); ap.add_argument("--bgm-db", type=float, default=-23.0, help="BGM 基准电平(相对满幅)")
    ap.add_argument("--lufs", type=float, default=-15.0); ap.add_argument("--no-sfx", action="store_true")
    a = ap.parse_args(); need("ffmpeg")
    w = Path(a.workdir); tl = load(w / "timeline.json"); D = tl["duration"]
    voice = w / "voice_master.wav"; ins = ["-i", str(voice)]; fc = [f"[0:a]aformat=channel_layouts=stereo:sample_rates=48000,apad=whole_dur={D:.3f},atrim=0:{D:.3f},asplit=2[vo][vsc]"]
    mix = ["[vo]"]; n = 1
    bgm = a.bgm
    if bgm == "auto" and (tl.get("bgm") or {}).get("file"): bgm = tl["bgm"]["file"]     # 计划里指定的 BGM 文件优先
    mood = a.mood or (tl.get("bgm") or {}).get("mood") or "calm-tech"
    if bgm == "auto":
        bgm = str(w / f"bgm_{mood}.wav"); run([sys.executable, str(Path(__file__).parent / "gen_bgm.py"), bgm, "--dur", f"{min(D, 200):.0f}", "--mood", mood])
    if bgm != "none" and Path(bgm).exists():
        ins += ["-stream_loop", "-1", "-i", bgm]
        env = bgm_envelope(tl, a.bgm_db)
        fc.append(f"[{n}:a]aformat=channel_layouts=stereo:sample_rates=48000,atrim=0:{D:.3f},asetpts=PTS-STARTPTS,highpass=f=90,lowpass=f=9000,"
                  f"volume='{env}':eval=frame,afade=t=in:d=1.5,afade=t=out:st={max(0, D - 4):.2f}:d=4[bg0]")
        fc.append("[bg0][vsc]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=420:makeup=1[bg]"); mix.append("[bg]"); n += 1
    else:
        fc.append("[vsc]anullsink")
    if not a.no_sfx:
        for s in tl["sfx"]:
            p = Path(s["name"]) if "/" in s["name"] else SFX_DIR / f"{s['name']}.mp3"
            if not p.exists(): print("WARN 音效缺失:", s["name"]); continue
            ms = max(0, int(s["t"] * 1000)); ins += ["-i", str(p)]
            fc.append(f"[{n}:a]aformat=channel_layouts=stereo:sample_rates=48000,volume={s.get('gain', .3):.2f},adelay={ms}|{ms}[s{n}]"); mix.append(f"[s{n}]"); n += 1
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0:dropout_transition=0,alimiter=limit=0.89[pre]")
    graph = w / "mix_graph.txt"; graph.write_text(";".join(fc), encoding="utf-8")
    pre = w / "mix_pre.wav"
    run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex_script", graph, "-map", "[pre]", "-t", f"{D:.3f}", "-c:a", "pcm_s24le", pre])
    # 两遍 loudnorm
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    ln = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-v", "error", "-i", pre, "-af", ln, "-ar", "48000", "-c:a", "aac", "-b:a", "256k", w / "final_audio.m4a"])
    print(f"音频完成: BGM={'有' if len(mix) > 1 and bgm != 'none' else '无'} SFX={len(tl['sfx']) if not a.no_sfx else 0} 目标 {a.lufs} LUFS → final_audio.m4a")


if __name__ == "__main__":
    main()
