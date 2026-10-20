#!/usr/bin/env python3
"""无版权风险的程序化 BGM 兜底（numpy 合成）。有真实音乐时优先用真实音乐。
用法: gen_bgm.py out.wav --dur 180 --mood calm-tech|upbeat|warm|tense"""
import argparse, wave
import numpy as np

SR = 44100
MOODS = {  # bpm, 和弦根音(MIDI), 和弦类型序列, 琶音密度, 底鼓
    "calm-tech": dict(bpm=84, roots=[57, 53, 48, 55], minor=[1, 0, 0, 0], arp=2, kick=False),
    "upbeat":    dict(bpm=112, roots=[48, 55, 57, 53], minor=[0, 0, 1, 0], arp=4, kick=True),
    "warm":      dict(bpm=72, roots=[60, 55, 57, 53], minor=[0, 0, 1, 0], arp=2, kick=False),
    "tense":     dict(bpm=96, roots=[45, 45, 41, 43], minor=[1, 1, 0, 0], arp=4, kick=True),
}
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def tone(f, n, harm=(1, .5, .25, .12)):
    t = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * (i + 1) * t + 0.3 * i) for i, a in enumerate(harm))


def make(dur, mood):
    c = MOODS[mood]; beat = 60 / c["bpm"]; bar = beat * 4; n = int(dur * SR); out = np.zeros((n, 2), np.float32)
    rnd = np.random.default_rng(3)
    for b in range(int(dur / bar) + 1):
        i = b % 4; root = c["roots"][i]; third = 3 if c["minor"][i] else 4
        notes = [root, root + third, root + 7]; s0 = int(b * bar * SR); L = int(bar * SR)
        if s0 >= n: break
        env = np.minimum(1, np.arange(L) / (0.35 * SR)) * np.minimum(1, (L - np.arange(L)) / (0.5 * SR))
        pad = sum(tone(mtof(m + 12 * k), L, (1, .35, .1)) for m in notes for k in (0, 1)) * env * 0.05
        seg = min(L, n - s0); out[s0:s0 + seg, 0] += pad[:seg]; out[s0:s0 + seg, 1] += pad[:seg] * 0.92
        out[s0:s0 + seg, 0] += (tone(mtof(root - 12), L, (1, .3)) * env * 0.09)[:seg]; out[s0:s0 + seg, 1] += (tone(mtof(root - 12), L, (1, .3)) * env * 0.09)[:seg]
        step = beat / (c["arp"] / 2) / 1.0 if c["arp"] else beat
        k = 0
        while k * step < bar:
            m = notes[[0, 1, 2, 1][k % 4]] + 12 * (1 + (k % 8 == 7)); ps = s0 + int(k * step * SR); pl = int(0.6 * SR)
            if ps >= n: break
            e = np.exp(-np.arange(pl) / (0.14 * SR)); w = tone(mtof(m), pl, (1, .4, .15)) * e * 0.07
            seg = min(pl, n - ps); pan = 0.5 + 0.35 * np.sin(k)
            out[ps:ps + seg, 0] += w[:seg] * (1 - pan); out[ps:ps + seg, 1] += w[:seg] * pan; k += 1
        if c["kick"]:
            for q in range(4):
                ks = s0 + int(q * beat * SR); kl = int(0.25 * SR)
                if ks >= n: break
                tt = np.arange(kl) / SR; kk = np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 28)) * tt) * np.exp(-tt * 11) * 0.28
                seg = min(kl, n - ks); out[ks:ks + seg] += kk[:seg, None]
    d = int(0.28 * SR); echo = np.zeros_like(out)               # 简易空间感
    for r, g in ((d, .35), (d * 2, .2), (d * 3, .1)): echo[r:] += out[:-r] * g
    out += echo; out /= max(1e-6, np.abs(out).max()) / 0.7
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--dur", type=float, default=120); ap.add_argument("--mood", default="calm-tech", choices=MOODS)
    a = ap.parse_args(); x = make(a.dur, a.mood)
    with wave.open(a.out, "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes((x * 32767).astype(np.int16).tobytes())
    print("BGM ->", a.out)
