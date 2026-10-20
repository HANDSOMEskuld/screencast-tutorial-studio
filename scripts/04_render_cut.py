#!/usr/bin/env python3
"""
Step 4 · 按 EDL 渲染粗剪成片：cut_video.mp4（无音轨，恒定帧率） + voice_master.wav（人声母带）
按计划片段分组渲染再无损拼接，避免超长 filter 图；每个切口 10ms 微淡入淡出，杜绝爆音。
"""
from __future__ import annotations
import argparse, sys
from concurrent.futures import ThreadPoolExecutor
from itertools import groupby
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load, run, h264_args, need

FADE = 0.010
VOICE_CHAIN = ("highpass=f=80,afftdn=nr=10:nf=-45,equalizer=f=200:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.5:g=2.5,"
               "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,"
               "loudnorm=I=-16:TP=-1.5:LRA=8")


def render_group(idx, seg, items, master, wav, fps, outdir, venc):
    A = min(e["src"][0] for e in items); B = max(e["src"][1] for e in items)
    vf, af, vn, an = [], [], [], []
    for i, e in enumerate(items):
        a, b = e["src"][0] - A, e["src"][1] - A; sp = e["speed"]; dur = (b - a) / sp
        vf.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)/{sp},fps={fps},format=yuv420p[v{i}]")
        if e["mute"]:
            af.append(f"aevalsrc=0:d={dur:.3f}:s=48000:c=stereo[a{i}]")
        else:
            t = f",atempo={sp}" if sp != 1 else ""
            af.append(f"[1:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS{t},aformat=channel_layouts=stereo,"
                      f"afade=t=in:d={FADE},afade=t=out:st={max(0, dur - FADE):.3f}:d={FADE}[a{i}]")
        vn.append(f"[v{i}]"); an.append(f"[a{i}]")
    n = len(items)
    g = ";".join(vf + af) + f";{''.join(vn)}concat=n={n}:v=1:a=0[V];{''.join(an)}concat=n={n}:v=0:a=1[A]"
    script = outdir / f"graph_{idx:03d}.txt"; script.write_text(g, encoding="utf-8")
    pv, pa = outdir / f"part_{idx:03d}.mp4", outdir / f"part_{idx:03d}.wav"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{A:.3f}", "-to", f"{B:.3f}", "-i", master, "-ss", f"{A:.3f}", "-to", f"{B:.3f}", "-i", wav,
         "-filter_complex_script", script, "-map", "[V]", *venc, "-pix_fmt", "yuv420p", "-an", pv,
         "-map", "[A]", "-c:a", "pcm_s24le", "-ar", "48000", pa])
    return pv, pa


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True)
    ap.add_argument("--fps", type=int, default=0, help="输出帧率，默认跟随素材(≥50→60, 否则30)")
    ap.add_argument("--crf", type=int, default=18); ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args(); need("ffmpeg")
    w = Path(a.workdir); edl, proj = load(w / "edl.json"), load(w / "project.json")
    fps = a.fps or (60 if proj["fps"] >= 50 else 30); venc = h264_args(a.crf)
    parts = w / "parts"; parts.mkdir(exist_ok=True)
    groups = [(k, list(g)) for k, g in groupby(edl["entries"], key=lambda e: (e["kind"] == "teaser", e["seg"]))]
    print(f"渲染 {len(groups)} 个片段组 → {fps}fps, 编码 {venc[1]}")
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda t: render_group(t[0], t[1][0], t[1][1], proj["master"], str(w / "master_audio.wav"), fps, parts, venc),
                          enumerate(groups)))
    lv, la = w / "parts_v.txt", w / "parts_a.txt"
    lv.write_text("".join(f"file '{v.resolve()}'\n" for v, _ in res)); la.write_text("".join(f"file '{x.resolve()}'\n" for _, x in res))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lv, "-c", "copy", w / "cut_video.mp4"])
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", la, "-c:a", "pcm_s24le", w / "voice_raw.wav"])
    print("人声母带: 去噪 → EQ → 压缩 → 响度 -16 LUFS")
    run(["ffmpeg", "-y", "-v", "error", "-i", w / "voice_raw.wav", "-af", VOICE_CHAIN, "-ar", "48000", "-c:a", "pcm_s24le", w / "voice_master.wav"])
    print(f"完成: cut_video.mp4 ({edl['total']:.1f}s) + voice_master.wav")


if __name__ == "__main__":
    main()
