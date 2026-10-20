"""共享工具：ffmpeg 调用、探测、JSON、时间映射。所有脚本 import 本模块。"""
from __future__ import annotations
import json, subprocess, shutil, sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SFX_DIR = SKILL_DIR / "assets" / "sfx"


def need(binary: str):
    if not shutil.which(binary):
        sys.exit(f"缺少 {binary}，先运行 scripts/setup_env.sh")


def run(cmd: list[str], quiet: bool = True, **kw) -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    r = subprocess.run(cmd, stdout=subprocess.PIPE if quiet else None,
                       stderr=subprocess.PIPE if quiet else None, text=True, **kw)
    if r.returncode != 0:
        tail = (r.stderr or "")[-1800:]
        sys.exit(f"命令失败: {' '.join(cmd[:6])} ...\n{tail}")
    return r


def probe(path: str) -> dict:
    need("ffprobe")
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    info = {"duration": float(j["format"].get("duration", 0)), "has_audio": a is not None}
    if v:
        num, den = (v.get("avg_frame_rate") or "30/1").split("/")
        info.update(width=int(v["width"]), height=int(v["height"]),
                    fps=round(float(num) / float(den or 1), 3) if float(den or 1) else 30.0)
    return info


def load(p) -> dict | list:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def h264_args(crf: int = 18, preset: str = "fast") -> list[str]:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if "h264_nvenc" in out and shutil.which("nvidia-smi"):
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", str(crf), "-b:v", "0"]
    return ["-c:v", "libx264", "-crf", str(crf), "-preset", preset]


def fmt_ts(t: float) -> str:
    t = max(0, t); m, s = divmod(int(t), 60)
    return f"{m:02d}:{s:02d}"


class TimeMap:
    """源时间 -> 成片时间 的分段线性映射。edl: [{src:[a,b], dst:[c,d], speed}]"""
    def __init__(self, edl: list[dict]):
        self.e = [c for c in edl if c.get("kind") != "teaser"]   # 预告片是源素材的复制，不参与锚点映射

    def to_dst(self, t: float, snap: str = "next") -> float | None:
        """snap='next': 落在被删区间时，吸附到下一个保留片段起点；'prev' 反之；None 不吸附"""
        for c in self.e:
            a, b = c["src"]
            if a <= t <= b:
                return c["dst"][0] + (t - a) / c.get("speed", 1.0)
        if snap == "next":
            for c in self.e:
                if c["src"][0] > t:
                    return c["dst"][0]
        if snap == "prev":
            for c in reversed(self.e):
                if c["src"][1] < t:
                    return c["dst"][1]
        return None
