#!/usr/bin/env python3
"""校验 AI 写的 story_plan.json：结构、时间范围、Hook/章节/CTA/节奏规则。有 ERROR 则退出码 1。"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load

OV_TYPES = {"callout", "step", "bignote", "broll", "ring"}
BROLL_KINDS = {"flow", "compare", "stat", "checklist", "mascot", "warning", "timeline", "custom"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True); a = ap.parse_args()
    w = Path(a.workdir); plan = load(w / "story_plan.json"); proj = load(w / "project.json")
    D = proj["duration"]; E, W = [], []
    err = lambda m: E.append(m); warn = lambda m: W.append(m)

    chapters = {c["id"]: c for c in plan.get("chapters", [])}
    if not 3 <= len(chapters) <= 9: warn(f"章节数 {len(chapters)}：建议 4-7 个，每章 ≥ 25s")
    segs = plan.get("segments", [])
    if not segs: err("segments 为空")
    ids = set()
    for s in segs:
        if s["id"] in ids: err(f"重复 segment id {s['id']}")
        ids.add(s["id"])
        a0, b0 = s["src"]
        if not (0 <= a0 < b0 <= D + 0.5): err(f"{s['id']} src 超出素材范围 0-{D:.1f}: {s['src']}")
        if s.get("chapter") not in chapters: err(f"{s['id']} chapter 未定义")
        if not s.get("why"): warn(f"{s['id']} 缺少 why（每个剪辑决策都要有理由）")
    # 章节必须连续出现（章节不能被打散）
    seen, last = [], None
    for s in segs:
        if s["chapter"] != last:
            if s["chapter"] in seen: err(f"章节 {s['chapter']} 在 segments 中被打断，章节需连续")
            seen.append(s["chapter"]); last = s["chapter"]
    for c in chapters:
        if c not in seen: warn(f"章节 {c} 没有任何 segment")
    # 重叠检测（同一源区间被重复使用需是有意为之）
    spans = sorted((s["src"][0], s["src"][1], s["id"]) for s in segs)
    for x, y in zip(spans, spans[1:]):
        if y[0] < x[1] - 0.05: warn(f"{x[2]} 与 {y[2]} 源区间重叠 {x[1]-y[0]:.1f}s（确认不是重复内容）")
    # Hook
    h = plan.get("hook") or {}
    if not h.get("headline"): err("缺少 hook.headline（前 3-5 秒必须有钩子）")
    elif len(h["headline"]) > 28: warn("hook.headline 太长，建议 ≤ 22 个字")
    if h.get("teaser_src") and not (0 <= h["teaser_src"][0] < h["teaser_src"][1] <= D + .5): err("hook.teaser_src 越界")
    if not 2.5 <= h.get("dur", 4) <= 6: warn("hook.dur 建议 3-5 秒")
    # 情绪曲线
    ec = plan.get("emotion_curve", {})
    if not ec.get("beats"): warn("缺少 emotion_curve.beats（宏观情绪曲线）")
    # Overlays
    ovs = plan.get("overlays", [])
    for i, o in enumerate(ovs):
        t = o.get("type")
        if t not in OV_TYPES: err(f"overlays[{i}] 未知 type {t}"); continue
        if not (0 <= o.get("src_t", -1) <= D): err(f"overlays[{i}] src_t 越界")
        if not 0.8 <= o.get("dur", 3) <= 9: warn(f"overlays[{i}] dur {o.get('dur')} 不在 0.8–9s 内")
        if t == "broll" and o.get("kind") not in BROLL_KINDS: err(f"overlays[{i}] broll.kind 无效: {o.get('kind')}")
        if t == "callout" and not (o.get("title") or o.get("body")): err(f"overlays[{i}] callout 缺少文字")
    n_broll = sum(1 for o in ovs if o["type"] == "broll"); n_call = sum(1 for o in ovs if o["type"] in ("callout", "ring", "step"))
    est = sum(s["src"][1] - s["src"][0] for s in segs) / 60
    if est > 1 and n_broll / est < 0.6: warn(f"B-roll 偏少：{n_broll} 个 / {est:.1f} 分钟，建议每分钟 ≥ 1 个")
    if est > 1 and n_call / est < 2: warn(f"提示框偏少：{n_call} 个 / {est:.1f} 分钟，建议每分钟 2-4 个")
    if not plan.get("cta"): warn("缺少 cta（结尾互动引导）")
    for k, s in enumerate(ovs):
        for o2 in ovs[k + 1:]:
            if s["type"] == o2["type"] == "broll" and abs(s["src_t"] - o2["src_t"]) < 2: warn("两个 B-roll 间隔 <2s，节奏过密")
    zone = [o for o in ovs if o["type"] in ("callout", "broll") and not o.get("at") and (o.get("pos") or "auto") in ("auto", "right")]
    for i, x in enumerate(zone):
        for y in zone[i + 1:]:
            if x["src_t"] < y["src_t"] + y.get("dur", 3) and y["src_t"] < x["src_t"] + x.get("dur", 3):
                warn(f"提示框/B-roll 同时占用右侧区域 ({x['src_t']:.0f}s 与 {y['src_t']:.0f}s)：错开时间，或把其一设为 pos:'left'/'right-low'")
    print(f"素材 {D:.1f}s | 章节 {len(chapters)} | segments {len(segs)} | overlays {len(ovs)} (B-roll {n_broll})")
    for m in W: print("WARN ", m)
    for m in E: print("ERROR", m)
    sys.exit(1 if E else 0)


if __name__ == "__main__":
    main()
