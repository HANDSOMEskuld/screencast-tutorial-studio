#!/usr/bin/env python3
"""
Step 3 · 粗剪决策 EDL：按 story_plan.segments 的顺序（含重排），再做口水词/停顿/口误的精剪。
关键点（录屏教程专用）：停顿 ≠ 废话。静音但画面在动 = 正在演示操作 → 保留并加速；静音且画面静止 = 死时间 → 删除。
输出 edl.json: entries[{src,dst,speed,kind,mute}] + removed[] 审计 + stats
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import load, save

PRESETS = {  # pause_max: 超过即处理的停顿; keep: 保留的气口; idle: 画面活动度阈值(0-100)
    "safe":    dict(pause_max=0.8,  keep=0.30, idle=0.25, action_free=3.0, max_speed=3.0),
    "natural": dict(pause_max=0.5,  keep=0.18, idle=0.30, action_free=2.0, max_speed=4.0),
    "tight":   dict(pause_max=0.35, keep=0.12, idle=0.40, action_free=1.6, max_speed=5.0),
}
ALWAYS = ["嗯", "呃", "额", "唔", "哼", "um", "uh", "er", "erm", "hmm", "mm", "mhm", "嗯嗯", "呃呃"]
SOFT_SINGLE = ["啊", "哦", "哎", "诶", "ah", "oh"]                     # 仅在孤立/拖长时删
SOFT_PHRASE = ["那个", "这个", "就是", "就是说", "然后呢", "对吧", "是吧", "你知道", "you know", "like", "so", "right", "basically", "kind of", "sort of"]
PRE, POST = 0.06, 0.10
CJK = lambda s: any("\u4e00" <= c <= "\u9fff" for c in s)
norm = lambda s: s.strip().strip(".,!?，。！？、…").lower()


def windows(tokens, text, maxlen=3):
    """在 tokens 上找拼起来等于 text 的 1..maxlen 个连续 token 窗口"""
    n = len(tokens)
    for i in range(n):
        acc = ""
        for j in range(i, min(n, i + maxlen + len(text))):
            acc += norm(tokens[j]["word"]) if not CJK(text) else norm(tokens[j]["word"])
            if acc == text.replace(" ", "") or (" " in text and acc == text.replace(" ", "")):
                yield i, j
                break
            if len(acc) >= len(text.replace(" ", "")):
                break


def mark_drops(words, extra=()):
    """返回 (drop集合索引, 原因dict)"""
    drop, why = set(), {}
    toks = [dict(w) for w in words]
    gap = lambda i, j: (toks[j]["start"] - toks[i]["end"]) if 0 <= i < len(toks) and 0 <= j < len(toks) else 9
    for ph in ALWAYS + list(extra):
        for i, j in windows(toks, ph):
            for k in range(i, j + 1): drop.add(k); why[k] = "filler"
    for ph in SOFT_SINGLE:
        for i, j in windows(toks, ph, 1):
            d = toks[i]["end"] - toks[i]["start"]
            if d >= 0.3 or gap(i - 1, i) >= 0.15 or gap(j, j + 1) >= 0.15:
                for k in range(i, j + 1): drop.add(k); why[k] = "filler"
    for ph in SOFT_PHRASE:
        for i, j in windows(toks, ph, 3):
            if gap(i - 1, i) >= 0.25 or gap(j, j + 1) >= 0.25:        # 紧贴停顿 = 思考型口水词
                for k in range(i, j + 1): drop.add(k); why[k] = "filler"
    for L in (3, 2, 1):                                               # 结巴/重复：保留后一个
        for i in range(len(toks) - 2 * L + 1):
            a = "".join(norm(t["word"]) for t in toks[i:i + L]); b = "".join(norm(t["word"]) for t in toks[i + L:i + 2 * L])
            if a and a == b and not (L == 1 and CJK(a) and len(a) == 1) and gap(i + L - 1, i + L) < 0.6:
                for k in range(i, i + L): drop.add(k); why[k] = "stutter"
    return drop, why


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workdir", required=True)
    ap.add_argument("--preset", default="natural", choices=PRESETS)
    ap.add_argument("--no-speedup", action="store_true", help="操作段不加速，仅保留")
    a = ap.parse_args()
    w = Path(a.workdir); P = PRESETS[a.preset]
    plan, tr = load(w / "story_plan.json"), load(w / "transcript.json")
    mot = load(w / "motion.json"); mfps, ms = mot["fps"], mot["scores"]
    extra = plan.get("meta", {}).get("fillers_extra", [])
    words = [x for s in tr["segments"] for x in s["words"]]

    def motion_mean(t0, t1):
        i0, i1 = int(t0 * mfps), max(int(t1 * mfps), int(t0 * mfps) + 1)
        sl = ms[i0:i1] or [0]
        return sum(sl) / len(sl)

    removed, stats = [], dict(filler=0, stutter=0, filler_time=0.0, dead_time=0.0, action_sped_time_saved=0.0)

    def build_range(A, B, seg_id, kind_default="speech", force_speed=None):
        ws = [x for x in words if x["start"] >= A - 0.02 and x["end"] <= B + 0.02]
        out = []
        if not ws:                                                     # 纯操作/无语音片段
            return classify_gap(A, B, seg_id, force_speed)
        drop, why = mark_drops(ws, extra)
        keep = [(i, x) for i, x in enumerate(ws) if i not in drop]
        for i in drop:
            stats[why[i]] += 1; stats["filler_time"] += ws[i]["end"] - ws[i]["start"]
            removed.append({"src": [ws[i]["start"], ws[i]["end"]], "kind": why[i], "text": ws[i]["word"].strip()})
        if not keep:
            return classify_gap(A, B, seg_id, force_speed)
        # 段首：开头的静音/等待
        first_s = keep[0][1]["start"]
        if first_s - A > P["pause_max"]:
            out += classify_gap(A, first_s, seg_id, force_speed, lead=True)
            cur_start = first_s - PRE
        else:
            cur_start = max(A, first_s - PRE)
        prev_i, prev = keep[0]
        for i, x in keep[1:]:
            forced = i - prev_i > 1                                   # 两词之间有被删除的口水词/重复 → 必须切掉
            g0, g1 = prev["end"] + POST, x["start"] - PRE
            if forced:
                d0, d1 = ws[prev_i + 1], ws[i - 1]
                g0 = max(prev["end"], min(g0, d0["start"] - 0.005)); g1 = min(x["start"], max(g1, d1["end"] + 0.005))
            dur = g1 - g0
            if dur > P["pause_max"]:
                m = motion_mean(prev["end"], x["start"])
                if dur <= 1.0 or m < P["idle"]:                        # 思考停顿/死时间 → 只留气口
                    k = P["keep"] / 2
                    out.append(dict(src=[cur_start, g0 + k], kind="speech", speed=1.0, mute=False, seg=seg_id))
                    stats["dead_time"] += max(0, dur - P["keep"]); removed.append({"src": [g0 + k, g1 - k], "kind": "pause", "motion": round(m, 2)})
                    cur_start = g1 - k
                elif dur <= P["action_free"] and not forced:           # 短操作：原速保留，不切
                    pass
                else:                                                  # 长操作：加速
                    out.append(dict(src=[cur_start, g0], kind="speech", speed=1.0, mute=False, seg=seg_id))
                    out += classify_gap(g0, g1, seg_id)
                    cur_start = g1
            elif forced:                                               # 只是切掉口水词，前后直接咬合
                out.append(dict(src=[cur_start, g0], kind="speech", speed=1.0, mute=False, seg=seg_id))
                cur_start = g1
            prev_i, prev = i, x
        end = min(B, prev["end"] + POST)
        if B - prev["end"] > P["pause_max"] + 0.2:
            out.append(dict(src=[cur_start, end], kind="speech", speed=1.0, mute=False, seg=seg_id))
            out += classify_gap(prev["end"] + POST, B, seg_id, force_speed, tail=True)
        else:
            out.append(dict(src=[cur_start, max(end, min(B, prev["end"] + 0.2))], kind="speech", speed=1.0, mute=False, seg=seg_id))
        return out

    def classify_gap(g0, g1, seg_id, force_speed=None, lead=False, tail=False):
        """无语音区间：按画面活动度切成「静止(删)」与「操作(保留/加速)」"""
        if g1 - g0 <= 0.05: return []
        step = 0.25; spans = []; t = g0
        while t < g1 - 1e-6:
            e = min(g1, t + step); act = motion_mean(t, e) >= P["idle"] or force_speed is not None
            if spans and spans[-1][2] == act: spans[-1][1] = e
            else: spans.append([t, e, act])
            t = e
        for i, sp_ in enumerate(spans):                                # 短于 0.8s 的静止夹在操作中间 → 视为操作
            if not sp_[2] and sp_[1] - sp_[0] < 0.8 and 0 < i < len(spans) - 1: sp_[2] = True
        merged_sp = []
        for sp_ in spans:
            if merged_sp and merged_sp[-1][2] == sp_[2]: merged_sp[-1][1] = sp_[1]
            else: merged_sp.append(sp_)
        res = []
        for x0, x1, act in merged_sp:
            dur = x1 - x0
            if not act:
                stats["dead_time"] += dur; removed.append({"src": [round(x0, 2), round(x1, 2)], "kind": "dead", "motion": 0}); continue
            if dur <= P["action_free"] and force_speed is None:
                res.append(dict(src=[x0, x1], kind="action", speed=1.0, mute=True, seg=seg_id)); continue
            sp = force_speed or (1.0 if a.no_speedup else min(P["max_speed"], max(1.5, dur / 1.8)))
            stats["action_sped_time_saved"] += dur - dur / sp
            res.append(dict(src=[x0, x1], kind="action", speed=round(sp, 2), mute=True, seg=seg_id))
        return res

    entries = []
    h = plan.get("hook", {}) or {}
    if h.get("teaser_src"):                                            # 冷开场预告片：取未来高光，限时
        t = build_range(*h["teaser_src"], "hook", force_speed=None)
        cap, acc = float(h.get("dur", 4.0)), 0.0
        for e in t:
            d = (e["src"][1] - e["src"][0]) / e["speed"]
            if acc + d > cap: e["src"][1] = e["src"][0] + (cap - acc) * e["speed"]; d = cap - acc
            e["kind"] = "teaser"; e["mute"] = False if e["speed"] == 1 else True
            entries.append(e); acc += d
            if acc >= cap: break
    for s in plan["segments"]:
        entries += build_range(s["src"][0], s["src"][1], s["id"], force_speed=s.get("speed"))

    # 合并相邻同类
    merged = []
    for e in entries:
        if merged and merged[-1]["kind"] == e["kind"] and merged[-1]["speed"] == e["speed"] and merged[-1]["mute"] == e["mute"] \
           and abs(merged[-1]["src"][1] - e["src"][0]) < 0.02 and merged[-1]["seg"] == e["seg"]:
            merged[-1]["src"][1] = e["src"][1]
        else:
            merged.append(e)
    t = 0.0
    for i, e in enumerate(merged):
        e["id"] = i + 1; e["src"] = [round(e["src"][0], 3), round(e["src"][1], 3)]
        d = (e["src"][1] - e["src"][0]) / e["speed"]
        e["dst"] = [round(t, 3), round(t + d, 3)]; t += d
    src_total = sum(s["src"][1] - s["src"][0] for s in plan["segments"])
    stats.update({k: round(v, 2) for k, v in stats.items() if isinstance(v, float)})
    save(w / "edl.json", {"preset": a.preset, "total": round(t, 3), "entries": merged, "removed": removed, "stats": stats})
    print(f"EDL: {len(merged)} 片段 | 计划保留 {src_total:.1f}s → 成片 {t:.1f}s ({t/60:.2f} min) | "
          f"口水词 {stats['filler']} / 重复 {stats['stutter']} | 死时间删除 {stats['dead_time']:.1f}s | 操作加速节省 {stats['action_sped_time_saved']:.1f}s")


if __name__ == "__main__":
    main()
