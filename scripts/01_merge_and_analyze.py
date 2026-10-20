#!/usr/bin/env python3
"""
Step 1 · 合并视频 + 高清音频 → 转录 → 生成「AI 分析包」
产出 (workdir/):
  master.mp4 / master_audio.wav   音画对齐后的母版（视频时间轴为准）
  sync_report.json                对齐偏移与置信度
  transcript.json / transcript.txt 字级转录
  silence.json / motion.json      静音区间 / 画面活动度(4fps)
  analysis_pack/sheets/*.jpg      带时间码的缩略图联系表，供 AI 视觉理解
  project.json                    工程元信息
"""
from __future__ import annotations
import argparse, glob, shutil, subprocess, sys, re
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from common import run, probe, save, need, fmt_ts


def pcm16k(src: str, dur: float = 180.0) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                        "-t", str(dur), "-f", "s16le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)


def sync_offset(video: str, ext: str, dur: float = 180.0) -> tuple[float, float]:
    """返回 (offset, confidence)。含义: video_t = ext_t + offset"""
    sr = 16000
    v, m = pcm16k(video, dur), pcm16k(ext, dur)
    if len(v) < sr or len(m) < sr:
        return 0.0, 0.0
    norm = lambda x: (x - x.mean()) / (x.std() + 1e-9)
    v, m = norm(v), norm(m)
    size = 1 << (len(v) + len(m)).bit_length()
    corr = np.fft.irfft(np.fft.rfft(v, size) * np.conj(np.fft.rfft(m, size)), size)
    k = int(np.argmax(corr))
    lag = k - size if k > size // 2 else k
    conf = float((corr[k] - corr.mean()) / (corr.std() + 1e-9))      # 峰值显著度(σ)，>5 可信
    return lag / sr, conf


def merge(videos: list[str], ext: str | None, work: Path) -> dict:
    video = videos[0]
    if len(videos) > 1:
        lst = work / "videos.txt"
        lst.write_text("".join(f"file '{Path(v).resolve()}'\n" for v in videos), encoding="utf-8")
        video = str(work / "video_concat.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    vi = probe(video)
    rep = {"video": str(Path(video).resolve()), "ext_audio": ext, "offset_sec": 0.0, "confidence": None, **vi}
    master, wav = work / "master.mp4", work / "master_audio.wav"
    if ext:
        off, conf = sync_offset(video, ext) if vi["has_audio"] else (0.0, 0.0)
        rep.update(offset_sec=round(off, 4), confidence=round(conf, 2))
        print(f"  对齐: video_t = ext_t + {off:+.4f}s  (峰值显著度 {conf:.1f}σ{' ⚠ 偏低,请人工核对' if vi['has_audio'] and conf < 5 else ''})")
        if off >= 0:
            chain = f"[1:a]adelay={int(off*1000)}|{int(off*1000)},aresample=48000,apad[a]"
        else:
            chain = f"[1:a]atrim=start={-off:.4f},asetpts=PTS-STARTPTS,aresample=48000,apad[a]"
        run(["ffmpeg", "-y", "-i", video, "-i", ext, "-filter_complex", chain + ";[a]asplit[a1][a2]",
             "-map", "0:v", "-map", "[a1]", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-t", f"{vi['duration']:.3f}", master,
             "-map", "[a2]", "-c:a", "pcm_s24le", "-t", f"{vi['duration']:.3f}", wav])
    else:
        if not vi["has_audio"]:
            sys.exit("视频没有音轨且未提供音频文件")
        shutil.copy(video, master)
        run(["ffmpeg", "-y", "-i", video, "-vn", "-ar", "48000", "-c:a", "pcm_s24le", wav])
    save(work / "sync_report.json", rep)
    return rep


def transcribe(work: Path, lang: str | None, model: str | None, prompt: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("缺少 faster-whisper：运行 scripts/setup_env.sh 并用 ~/.venvs/studio/bin/python 执行")
    try:
        m = WhisperModel(model or "large-v3", device="cuda", compute_type="float16")
    except Exception:
        m = WhisperModel(model or "small", device="cpu", compute_type="int8")
    wav16 = work / "audio_16k.wav"
    run(["ffmpeg", "-y", "-i", work / "master_audio.wav", "-ac", "1", "-ar", "16000", wav16])
    segs, info = m.transcribe(str(wav16), language=lang, word_timestamps=True, vad_filter=True,
                              beam_size=5, initial_prompt=prompt or None, condition_on_previous_text=False)
    out, lines = [], []
    for s in segs:
        words = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word, "prob": round(w.probability, 3)}
                 for w in (s.words or [])]
        out.append({"id": s.id, "start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(), "words": words})
        lines.append(f"[{s.start:7.1f}s | {fmt_ts(s.start)}] {s.text.strip()}")
    save(work / "transcript.json", {"language": info.language, "duration": info.duration, "segments": out})
    (work / "transcript.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"  转录: {len(out)} 句, 语言 {info.language}")


def silence(work: Path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", work / "master_audio.wav", "-af",
                        "silencedetect=noise=-38dB:d=0.3", "-f", "null", "-"], capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    save(work / "silence.json", [[a, b] for a, b in zip(st, en)])


def motion(work: Path, fps: int = 4):
    """画面活动度：相邻帧平均绝对差 (0-100)。用于区分『在操作』与『纯等待』。"""
    W, H = 160, 90
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(work / "master.mp4"), "-an",
                          "-vf", f"fps={fps},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE)
    prev, scores = None, []
    while True:
        buf = p.stdout.read(W * H)
        if len(buf) < W * H:
            break
        cur = np.frombuffer(buf, dtype=np.uint8).astype(np.float32)
        scores.append(0.0 if prev is None else float(np.abs(cur - prev).mean() / 255 * 100))
        prev = cur
    save(work / "motion.json", {"fps": fps, "scores": [round(s, 3) for s in scores]})


def sheets(work: Path, duration: float, every: float | None):
    pack = work / "analysis_pack" / "sheets"
    shutil.rmtree(pack, ignore_errors=True); pack.mkdir(parents=True)
    every = every or max(4.0, min(15.0, duration / 96))
    font = next((f for f in glob.glob("/usr/share/fonts/**/*.ttf", recursive=True) + glob.glob("/usr/share/fonts/**/*.ttc", recursive=True)
                 if "DejaVuSans." in f or "NotoSans" in f), None)
    stamp = (f",drawtext=fontfile={font}:text='%{{pts\\:hms}}':x=6:y=h-th-6:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6"
             if font else "")
    vf = f"fps=1/{every},scale=480:-1{stamp},tile=4x3"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", work / "master.mp4", "-an", "-vf", vf,
                        "-q:v", "4", str(pack / "sheet_%02d.jpg")], capture_output=True, text=True)
    if r.returncode != 0 and stamp:           # drawtext 不可用时降级
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", work / "master.mp4", "-an",
                        "-vf", f"fps=1/{every},scale=480:-1,tile=4x3", "-q:v", "4", str(pack / "sheet_%02d.jpg")])
    save(work / "analysis_pack" / "sheets.json", {"every_sec": every, "tiles_per_sheet": 12, "note": "sheet_N 第 i 格时间 = ((N-1)*12+i)*every_sec"})
    print(f"  联系表: 每 {every:.1f}s 一格 → {len(list(pack.glob('*.jpg')))} 张")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", nargs="+", required=True, help="录屏文件(多个则按顺序拼接)")
    ap.add_argument("--audio", default=None, help="高清外置音频(DJI Mic 等)，可省略")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--lang", default=None, help="zh / en；默认自动检测")
    ap.add_argument("--model", default=None, help="faster-whisper 模型，默认 GPU:large-v3 / CPU:small")
    ap.add_argument("--prompt", default="", help="术语表/产品名，提升专有名词识别，如 'Cursor, Claude Code, Railway'")
    ap.add_argument("--frame-every", type=float, default=None)
    ap.add_argument("--skip-transcribe", action="store_true")
    a = ap.parse_args()
    need("ffmpeg"); work = Path(a.workdir); work.mkdir(parents=True, exist_ok=True)
    print("[1/5] 合并/对齐音画"); rep = merge(a.video, a.audio, work)
    print("[2/5] 转录(字级时间戳)")
    if not a.skip_transcribe: transcribe(work, a.lang, a.model, a.prompt)
    print("[3/5] 静音检测"); silence(work)
    print("[4/5] 画面活动度"); motion(work)
    print("[5/5] 视觉联系表"); sheets(work, rep["duration"], a.frame_every)
    save(work / "project.json", {"master": str(work / "master.mp4"), "duration": rep["duration"],
                                 "width": rep["width"], "height": rep["height"], "fps": rep["fps"]})
    print("完成。下一步：AI 阅读 transcript.txt + analysis_pack/sheets/*.jpg → 写 story_plan.json（见 SKILL.md 阶段 2）")


if __name__ == "__main__":
    main()
