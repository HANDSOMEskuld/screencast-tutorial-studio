#!/usr/bin/env python3
"""
Step 6 · 由 timeline.json + captions.json 生成两个 HyperFrames 工程：
  overlay_project/  透明叠层（字幕/章节进度条/提示框/B-roll/CTA）
  mask_project/     同一时间轴的「玻璃区域遮罩」，用于 ffmpeg 做真正的背景毛玻璃模糊（--glass real）
"""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load, SKILL_DIR

FILL = {("real", "dark"): "rgba(32,34,44,0.42)", ("real", "light"): "rgba(255,255,255,0.46)",
        ("fake", "dark"): "rgba(26,28,38,0.86)", ("fake", "light"): "rgba(250,250,252,0.90)"}


def build(out: Path, tpl: str, data: dict, W: int, H: int, dur: float, mask: bool, glass: str, style: str, accent: str):
    out.mkdir(parents=True, exist_ok=True)
    k = W / 1920
    html = (tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__W__", str(W)).replace("__H__", str(H)).replace("__K__", f"{k:.5f}").replace("__DH__", f"{H / k:.2f}")
            .replace("__DUR__", f"{dur:.3f}").replace("__ACCENT__", accent).replace("__FILL__", FILL[(glass, style)])
            .replace("__BODYCLASS__", "mask" if mask else "").replace("__STAGECLASS__", style))
    (out / "index.html").write_text(html, encoding="utf-8")
    shutil.copy(SKILL_DIR / "templates" / "gsap.min.js", out / "gsap.min.js")
    (out / "hyperframes.json").write_text(json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}, "media": {"autoProxy": True}}, indent=2))
    (out / "meta.json").write_text(json.dumps({"id": out.name, "name": out.name}))
    (out / "package.json").write_text(json.dumps({"name": out.name, "private": True, "type": "module"}))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True)
    ap.add_argument("--glass", choices=["real", "fake"], default="real", help="real=真实背景模糊(需 mask 渲染,慢一倍) fake=纯半透明填充(快,预览用)")
    ap.add_argument("--style", choices=["dark", "light"], default=None); ap.add_argument("--accent", default=None)
    ap.add_argument("--ov-width", type=int, default=1920, help="叠层渲染宽度(默认1920，合成时自动放大到成片分辨率)")
    ap.add_argument("--mask-scale", type=float, default=0.5, help="遮罩渲染分辨率相对叠层的比例(遮罩只是形状，半分辨率即可，渲染省约一半时间)")
    a = ap.parse_args()
    w = Path(a.workdir); tl, proj = load(w / "timeline.json"), load(w / "project.json")
    cap_p = w / "captions.json"
    if not cap_p.exists():
        print("WARN: 未找到 captions.json（AI 审校稿），临时使用 captions_draft.json"); cap_p = w / "captions_draft.json"
    caps = load(cap_p)
    meta = tl.get("meta", {}); style = a.style or ("light" if "light" in meta.get("style", "dark") else "dark"); accent = a.accent or meta.get("accent", "#0A84FF")
    ow = a.ov_width if a.ov_width < proj["width"] else proj["width"]; oh = round(proj["height"] * ow / proj["width"] / 2) * 2
    data = dict(duration=tl["duration"], chapters=tl["chapters"], overlays=tl["overlays"], hook=tl["hook"], cta=tl["cta"],
                speed_zones=tl["speed_zones"], captions=caps)
    tpl = (SKILL_DIR / "templates" / "overlay.html").read_text(encoding="utf-8")
    build(w / "overlay_project", tpl, data, ow, oh, tl["duration"], False, a.glass, style, accent)
    mw = max(320, round(ow * a.mask_scale / 2) * 2); mh = round(oh * mw / ow / 2) * 2
    if a.glass == "real": build(w / "mask_project", tpl, data, mw, mh, tl["duration"], True, a.glass, style, accent)
    (w / "overlay_meta.json").write_text(json.dumps({"glass": a.glass, "ow": ow, "oh": oh, "mw": mw, "mh": mh}))
    print(f"叠层工程已生成 ({ow}x{oh}, glass={a.glass}, style={style}) → {w/'overlay_project'}")
    print("检查: cd overlay_project && npx hyperframes check   预览: npx hyperframes preview")


if __name__ == "__main__":
    main()
