#!/usr/bin/env python3
"""
Step 5 · 把计划里的「源时间锚点」映射到成片时间轴 → timeline.json；并生成字幕初稿 captions_draft.json
timeline.json 含: duration / chapters / overlays / hook / cta / sfx(含自动音效) / speed_zones
captions_draft.json 由 AI 审校后另存为 captions.json（改错字、术语、断句；保持时间轴）
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load, save, TimeMap

PUNCT = "，。？！；,.?!;"
AUTO_SFX = {"callout": ("pop", 0.30), "step": ("click-soft", 0.30), "ring": ("ping", 0.22), "broll": ("whoosh-short", 0.30)}
TONE_SFX = {"warn": ("error", 0.22), "success": ("chime", 0.30), "info": ("ping", 0.26)}


def caption_draft(edl, tr, maxc_cjk=16, maxc_lat=44):
    toks = []
    words = [w for s in tr["segments"] for w in s["words"]]
    for e in edl["entries"]:
        if e["mute"] or e["speed"] != 1: continue
        for w in words:
            mid = (w["start"] + w["end"]) / 2
            if e["src"][0] <= mid < e["src"][1]:
                d0 = e["dst"][0] + (w["start"] - e["src"][0]); d1 = e["dst"][0] + (w["end"] - e["src"][0])
                toks.append({"t": w["word"], "s": max(e["dst"][0], d0), "e": min(e["dst"][1], d1)})
    # 去掉已被 EDL 删除的词（不在任何 entry 内）——上面已天然过滤
    cues, cur = [], []
    def flush():
        if not cur: return
        txt = "".join(x["t"] for x in cur).strip()
        if re.search(r"[A-Za-z]{2,}", txt) and " " in txt: txt = re.sub(r"\s+", " ", txt)
        cues.append({"start": round(cur[0]["s"], 2), "end": round(cur[-1]["e"], 2), "text": txt}); cur.clear()
    for k, x in enumerate(toks):
        if cur and x["s"] - cur[-1]["e"] > 0.55: flush()
        cur.append(x)
        n = len("".join(y["t"] for y in cur).strip())
        cjk = bool(re.search(r"[\u4e00-\u9fff]", cur[0]["t"]))
        if x["t"].strip()[-1:] in PUNCT or n >= (maxc_cjk if cjk else maxc_lat): flush()
    flush()
    for i, c in enumerate(cues):                       # 最短显示 0.9s，不与下一条重叠
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else 1e9
        c["end"] = round(min(max(c["end"], c["start"] + 0.9), nxt - 0.02), 2)
        c["id"] = i + 1; c["text"] = re.sub(r"[，。,.]$", "", c["text"])
    return cues


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True); a = ap.parse_args()
    w = Path(a.workdir)
    plan, edl, tr = load(w / "story_plan.json"), load(w / "edl.json"), load(w / "transcript.json")
    tm = TimeMap(edl["entries"]); total = edl["total"]; warns = []
    teaser_end = max([e["dst"][1] for e in edl["entries"] if e["kind"] == "teaser"] or [0.0])

    # 章节：以首个 segment 起点到下一章起点（连续）
    ch_info = {c["id"]: dict(c, start=None, end=None) for c in plan["chapters"]}
    for s in plan["segments"]:
        ents = [e for e in edl["entries"] if e["seg"] == s["id"]]
        if not ents: continue
        st, en = ents[0]["dst"][0], ents[-1]["dst"][1]; c = ch_info[s["chapter"]]
        c["start"] = st if c["start"] is None else min(c["start"], st); c["end"] = en if c["end"] is None else max(c["end"], en)
    chapters = sorted([c for c in ch_info.values() if c["start"] is not None], key=lambda c: c["start"])
    for i, c in enumerate(chapters):                   # 无缝衔接
        c["end"] = chapters[i + 1]["start"] if i + 1 < len(chapters) else total
        c["start"], c["end"] = round(c["start"], 2), round(c["end"], 2)
    if chapters: chapters[0]["start"] = round(teaser_end, 2)

    overlays = []
    for i, o in enumerate(plan.get("overlays", [])):
        t0 = tm.to_dst(o["src_t"], "next")
        if t0 is None: warns.append(f"overlay[{i}] 无法映射(源 {o['src_t']}s)"); continue
        if tm.to_dst(o["src_t"], None) is None: warns.append(f"overlay[{i}] src_t={o['src_t']} 落在被剪除区域，已吸附到 {t0:.1f}s")
        d = min(o.get("dur", 3.0), max(0.8, total - t0))
        overlays.append(dict(o, start=round(t0, 2), dur=round(d, 2), idx=i))
    overlays.sort(key=lambda o: o["start"])

    sfx = []
    for o in overlays:
        if o["type"] == "bignote": nm, g = TONE_SFX.get(o.get("tone", "info"), TONE_SFX["info"])
        else: nm, g = AUTO_SFX.get(o["type"], ("pop", 0.25))
        if o.get("sfx") is False: continue
        sfx.append({"t": o["start"], "name": o.get("sfx") if isinstance(o.get("sfx"), str) else nm, "gain": g, "why": f"overlay:{o['type']}"})
    for c in chapters[1:]: sfx.append({"t": c["start"] - 0.05, "name": "whoosh", "gain": 0.34, "why": "chapter"})
    for e in edl["entries"]:
        if e["kind"] == "action" and e["speed"] >= 2: sfx.append({"t": e["dst"][0], "name": "whoosh-short", "gain": 0.22, "why": "fast-forward"})
    if plan.get("hook"): sfx.append({"t": 0.0, "name": plan["hook"].get("sfx", "impact-bass-1"), "gain": 0.30, "why": "hook"})
    for s in plan.get("sfx", []):
        t = tm.to_dst(s["src_t"], "next")
        if t is not None: sfx.append({"t": round(t, 2), "name": s["name"], "gain": s.get("gain", 0.3), "why": "plan"})
    sfx.sort(key=lambda x: x["t"]); dedup = []
    for s in sfx:                                      # 同类 0.4s 内去重，整体密度 ≤ 1 个/1.2s
        if dedup and s["t"] - dedup[-1]["t"] < 0.4: continue
        dedup.append(s)
    cta = plan.get("cta"); extend = float(cta.get("extend", 0)) if cta else 0.0
    cta_out = dict(cta, start=round(total + extend - cta.get("dur", 5), 2), dur=cta.get("dur", 5), extend=extend) if cta else None
    hook = dict(plan.get("hook", {}), start=0.0, dur=float(plan.get("hook", {}).get("dur", 4)))
    if not (plan.get("hook") or {}).get("teaser_src"): hook["start"] = 0.2
    zones = [{"start": e["dst"][0], "end": e["dst"][1], "speed": e["speed"]} for e in edl["entries"] if e["kind"] == "action" and e["speed"] > 1]

    save(w / "timeline.json", {"duration": round(total + extend, 2), "base_duration": total, "meta": plan.get("meta", {}), "chapters": chapters,
                               "overlays": overlays, "hook": hook, "cta": cta_out, "sfx": dedup, "speed_zones": zones, "bgm": plan.get("bgm", {})})
    cues = caption_draft(edl, tr); save(w / "captions_draft.json", cues)
    print(f"timeline: {total:.1f}s | 章节 {len(chapters)} | overlays {len(overlays)} | sfx {len(dedup)} | 字幕初稿 {len(cues)} 条")
    for m in warns: print("WARN", m)
    print("下一步：AI 审校 captions_draft.json → 另存 captions.json（见 references/05-captions-chapters.md）")


if __name__ == "__main__":
    main()
