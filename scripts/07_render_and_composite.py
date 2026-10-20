#!/usr/bin/env python3
"""
Step 7 · 渲染透明叠层(HyperFrames→WebM alpha) → 与粗剪视频合成（含真实背景毛玻璃） → video_composited.mp4
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load, run, h264_args, need


def hf_render(proj: Path, out: Path, fps: int, quality: str):
    cmd = ["npx", "-y", "hyperframes", "render", str(proj), "--format", "webm", "--fps", str(fps), "--quality", quality, "-o", str(out)]
    r = subprocess.run(cmd, text=True)
    if r.returncode != 0 or not out.exists():
        sys.exit("HyperFrames 渲染失败：先运行 `npx hyperframes browser ensure` 和 `npx hyperframes check`")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True)
    ap.add_argument("--fps", type=int, default=30, help="叠层帧率(UI 动效 30fps 足够，底片仍为原帧率)")
    ap.add_argument("--quality", default="looks", choices=["draft", "looks", "delivery"])
    ap.add_argument("--crf", type=int, default=18); ap.add_argument("--blur", type=float, default=22.0, help="毛玻璃模糊强度")
    ap.add_argument("--skip-render", action="store_true", help="复用已渲染的 overlay.webm / mask.webm")
    a = ap.parse_args(); need("ffmpeg")
    w = Path(a.workdir); tl, proj, om = load(w / "timeline.json"), load(w / "project.json"), load(w / "overlay_meta.json")
    ov, mk = w / "overlay.webm", w / "mask.webm"
    if not a.skip_render:
        hf_render(w / "overlay_project", ov, a.fps, a.quality)
        if om["glass"] == "real": hf_render(w / "mask_project", mk, a.fps, a.quality)
    cut = w / "cut_video.mp4"; info = load(w / "project.json")
    W, H = info["width"], info["height"]; ext = max(0.0, tl["duration"] - tl["base_duration"])
    base = f"[0:v]scale={W}:{H},setsar=1" + (f",tpad=stop_mode=clone:stop_duration={ext:.2f}" if ext else "") + "[base]"
    ovs = f"[1:v]scale={W}:{H},format=yuva420p[ov]"
    if om["glass"] == "real":
        sig = a.blur / 4
        g = (f"{base};[base]split=2[b1][b2];[b2]scale={W//4}:{H//4},gblur=sigma={sig:.1f}:steps=2,scale={W}:{H}:flags=bicubic,"
             f"eq=saturation=1.45:brightness=0.02:contrast=1.04[blur];[2:v]scale={W}:{H},format=yuva420p,alphaextract[m];"
             f"[blur][m]alphamerge[glassbg];[b1][glassbg]overlay=format=auto[t1];{ovs};[t1][ov]overlay=format=auto,format=yuv420p[v]")
    else:
        g = f"{base};{ovs};[base][ov]overlay=format=auto,format=yuv420p[v]"
    # 必须用 libvpx-vp9 解码器(写在对应 -i 之前)才能读到 alpha 通道
    inputs = ["-i", str(cut)] + ["-c:v", "libvpx-vp9", "-i", str(ov)] + (["-c:v", "libvpx-vp9", "-i", str(mk)] if om["glass"] == "real" else [])
    out = w / "video_composited.mp4"
    print("合成中（真实毛玻璃需要较长时间）...")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", g, "-map", "[v]", *h264_args(a.crf), "-pix_fmt", "yuv420p", "-an", out], quiet=False)
    print(f"完成: {out}")


if __name__ == "__main__":
    main()
