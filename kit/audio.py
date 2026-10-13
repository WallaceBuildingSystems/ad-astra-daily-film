#!/usr/bin/env python3
"""Procedural score, sound design and final mix for the Ad Astra daily film.

usage: python3 audio.py edl.json vo.wav out_mix.wav [drop_t]

Builds a dark synth bed at 110 beats a minute in A minor, locked so a bar lands on the drop
(the turn into the results), with whooshes and glitch bursts on cuts, ticks under the counters,
an impact on the drop and a hit on the closing wordmark. Ducks the bed under the voice and
masters the mix to about minus 14 LUFS, true peak minus 1 dB.
"""
import json, subprocess, sys, math
import numpy as np

SR = 48000
rng = np.random.default_rng(11)

def load_mono(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def write(path, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    pcm = (x * 32767).astype(np.int16).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", path], input=pcm, check=True)

def onepole_lp(x, fc):
    """Time-varying one-pole low pass, block-wise with carried state; fc scalar or array."""
    from scipy.signal import lfilter
    fc = np.broadcast_to(np.asarray(fc, np.float32), x.shape)
    y = np.empty_like(x)
    zi = np.zeros(1)
    B = 256
    for i in range(0, len(x), B):
        a = float(np.exp(-2 * np.pi * float(fc[i]) / SR))
        yb, zi = lfilter([1 - a], [1, -a], x[i:i + B], zi=zi)
        y[i:i + B] = yb
    return y

def lp_fft(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X * H, len(x)).astype(np.float32)

def hp_fft(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    f[0] = 1e-3
    H = 1 / np.sqrt(1 + (fc / f) ** (2 * order))
    return np.fft.irfft(X * H, len(x)).astype(np.float32)

def bp_fft(x, lo, hi):
    return hp_fft(lp_fft(x, hi), lo)

def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    ph = (freq * (1 + detune) * t) % 1.0
    return (2 * ph - 1).astype(np.float32)

def sine(freq, n):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t).astype(np.float32)

def env_ad(n, a, d):
    na, nd = int(a * SR), int(d * SR)
    e = np.zeros(n, np.float32)
    na = max(1, min(na, n))
    e[:na] = np.linspace(0, 1, na)
    rest = n - na
    if rest > 0:
        e[na:] = np.exp(-np.arange(rest) / max(1, nd))
    return e

def place(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]; i = 0
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += x[:m] * gain

def reverb(x, secs=2.2, wet=0.3):
    n = int(secs * SR)
    ir = rng.normal(0, 1, n).astype(np.float32) * np.exp(-np.arange(n) / (SR * secs / 6.9))
    ir = lp_fft(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    N = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)].astype(np.float32)
    return x * (1 - wet) + y * wet

def kick(n=int(0.45 * SR)):
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 7.5)).astype(np.float32)

def boom(n=int(2.4 * SR)):
    t = np.arange(n) / SR
    f = 28 + 60 * np.exp(-t * 6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    b = np.sin(ph) * np.exp(-t * 1.6)
    noise = rng.normal(0, 1, n).astype(np.float32) * np.exp(-t * 3.5)
    return (b * 0.9 + lp_fft(noise, 2500) * 0.35).astype(np.float32)

def clap(n=int(0.2 * SR)):
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n).astype(np.float32)
    x = bp_fft(x, 900, 4000)
    e = np.exp(-t * 26) + 0.6 * np.exp(-np.maximum(0, t - 0.012) * 30) * (t > 0.012)
    return (x * e).astype(np.float32)

def hat(n=int(0.06 * SR), decay=55):
    t = np.arange(n) / SR
    x = hp_fft(rng.normal(0, 1, n).astype(np.float32), 7000)
    return (x * np.exp(-t * decay)).astype(np.float32)

def whoosh(dur=0.32):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = rng.normal(0, 1, n).astype(np.float32)
    x = bp_fft(x, 400, 6000)
    e = (t ** 2.2) * (1 - t) ** 0.3 * 3.2
    return (x * e).astype(np.float32)

def glitch(dur=0.09):
    n = int(dur * SR)
    x = rng.normal(0, 1, n).astype(np.float32)
    step = 24
    x = np.repeat(x[::step], step)[:n]  # sample-and-hold crunch
    x = np.sign(x) * (np.abs(x) ** 0.5)
    sq = np.sign(sine(rng.uniform(300, 1400), n))
    return ((x * 0.5 + sq * 0.25) * np.linspace(1, 0.2, n)).astype(np.float32)

def tick():
    n = int(0.012 * SR)
    return (sine(2600, n) * np.exp(-np.arange(n) / (SR * 0.0025))).astype(np.float32)

def buzz():
    n = int(0.09 * SR)
    return (np.sign(sine(165, n)) * 0.6 * np.linspace(1, 0, n)).astype(np.float32)

NOTE = lambda m: 440.0 * 2 ** ((m - 69) / 12)

def build(edl, vo, drop_t):
    dur = edl["duration"]
    n = int(dur * SR) + SR
    beat = 60 / 110
    end_t = edl["end"]["t0"] if edl.get("end") else dur
    cuts = sorted(set([s["t0"] for s in edl["shots"] if s["t0"] > 0.05] + edl.get("glitches", [])))
    music = np.zeros((n, 2), np.float32)
    t = np.arange(n) / SR

    # --- pad drone, A minor, filter opens toward the drop ---
    pad = np.zeros(n, np.float32)
    for m, g in [(45, 0.5), (52, 0.35), (57, 0.3), (60, 0.18), (64, 0.14)]:
        pad += (saw(NOTE(m), n, -0.004) + saw(NOTE(m), n, 0.005)) * g * 0.5
    cutoff = np.where(t < drop_t, 380 + 2200 * (t / drop_t) ** 2.2, 1600)
    cutoff = np.where(t >= end_t, 2400, cutoff)
    pad = onepole_lp(onepole_lp(pad, cutoff), cutoff)
    swell = np.clip(t / 2.0, 0, 1) * np.where(t < drop_t, 0.55 + 0.45 * (t / drop_t), 0.45)
    swell = np.where(t >= end_t, np.clip(1 - (t - end_t - 2.6) / 2.0, 0, 1) * 0.9, swell)
    pad *= swell
    music[:, 0] += pad * 0.30
    music[:, 1] += np.roll(pad, int(0.011 * SR)) * 0.30

    # beat grid locked to the drop
    k0 = -int(drop_t / beat) - 1
    beats = [drop_t + k * beat for k in range(k0, int((dur - drop_t) / beat) + 2)]
    beats = [b for b in beats if 0 <= b < dur]

    # --- pre-drop: pulsing sub on eighths and ticking hats ---
    sub_hit = (sine(NOTE(33), int(0.24 * SR)) * env_ad(int(0.24 * SR), 0.004, 0.09)).astype(np.float32)
    for b in beats:
        if b >= drop_t - 0.05:
            break
        for e in (0, beat / 2):
            g = 0.55 + 0.35 * (b / drop_t)
            place(music[:, 0], sub_hit, b + e, g * 0.55); place(music[:, 1], sub_hit, b + e, g * 0.55)
        for s16 in range(4):
            g = (0.12 if s16 else 0.2) * (0.4 + 0.6 * b / drop_t)
            h = hat(decay=90)
            place(music[:, 0], h, b + s16 * beat / 4, g); place(music[:, 1], h, b + s16 * beat / 4 + 0.003, g)
    # riser into the drop, then a breath of silence
    r_len = 3.2
    rn = int(r_len * SR)
    rt = np.linspace(0, 1, rn)
    noise = rng.normal(0, 1, rn).astype(np.float32)
    riser = bp_fft(noise, 600, 9000) * (rt ** 2.5) * 0.5
    ph = 2 * np.pi * np.cumsum(220 + 900 * rt ** 2) / SR
    riser += np.sin(ph).astype(np.float32) * (rt ** 2) * 0.25
    gap = 0.12
    place(music[:, 0], riser, drop_t - gap - r_len); place(music[:, 1], riser, drop_t - gap - r_len)
    i0, i1 = int((drop_t - gap) * SR), int(drop_t * SR)
    music[i0:i1] *= np.linspace(1, 0.05, i1 - i0)[:, None]

    # --- drop: kick, clap, bass, arp, hats ---
    bn = int(beat / 2 * SR)
    bass_notes = [33, 33, 33, 36, 33, 33, 31, 28]
    arp_notes = [69, 72, 76, 79, 81, 79, 76, 72]
    k = 0
    for bi, b in enumerate([x for x in beats if drop_t - 0.01 <= x < end_t]):
        place(music[:, 0], kick(), b, 0.9); place(music[:, 1], kick(), b, 0.9)
        if bi % 2 == 1:
            c = clap()
            place(music[:, 0], c, b, 0.32); place(music[:, 1], c, b + 0.004, 0.32)
        for e in range(2):
            m = bass_notes[(bi * 2 + e) % len(bass_notes)]
            x = (saw(NOTE(m), bn) * 0.6 + saw(NOTE(m), bn, 0.006) * 0.4)
            x = lp_fft(x, 420) * env_ad(bn, 0.003, 0.16)
            place(music[:, 0], x, b + e * beat / 2, 0.42); place(music[:, 1], x, b + e * beat / 2, 0.42)
            h = hat(int(0.12 * SR), 22)
            if e == 1:
                place(music[:, 0], h, b + beat / 2, 0.12); place(music[:, 1], h, b + beat / 2 + 0.002, 0.12)
        for s16 in range(4):
            m = arp_notes[k % len(arp_notes)]; k += 1
            an = int(beat / 4 * SR)
            sq = np.sign(sine(NOTE(m), an)) * 0.5 + saw(NOTE(m), an) * 0.5
            sq = lp_fft(sq.astype(np.float32), 3200) * env_ad(an, 0.002, 0.05)
            pan = 0.35 if s16 % 2 else -0.35
            place(music[:, 0], sq, b + s16 * beat / 4, 0.07 * (1 - pan)); place(music[:, 1], sq, b + s16 * beat / 4, 0.07 * (1 + pan))
    # drop impact
    bm = boom()
    place(music[:, 0], bm, drop_t, 0.8); place(music[:, 1], bm, drop_t, 0.8)

    # --- ending: big hit on the wordmark, chord bloom ---
    if edl.get("end"):
        hit = boom(int(3.5 * SR))
        place(music[:, 0], hit, end_t, 1.0); place(music[:, 1], hit, end_t, 1.0)
        cn = int((dur - end_t + 0.5) * SR)
        chord = sum(saw(NOTE(m), cn, d) for m, d in [(57, -0.003), (60, 0.004), (64, -0.002), (69, 0.003), (76, 0.0)])
        chord = lp_fft(chord.astype(np.float32), 1800) * np.minimum(1, np.arange(cn) / (0.6 * SR)) * np.clip(1 - (np.arange(cn) / SR - 2.6) / 1.8, 0, 1)
        place(music[:, 0], chord, end_t, 0.1); place(music[:, 1], np.roll(chord, 500), end_t, 0.1)

    music[:, 0] = reverb(music[:, 0], 2.0, 0.22)
    music[:, 1] = reverb(music[:, 1], 2.1, 0.22)

    # --- sound design ---
    sfx = np.zeros((n, 2), np.float32)
    for c in cuts:
        w = whoosh()
        place(sfx[:, 0], w, c - 0.28, 0.32); place(sfx[:, 1], w, c - 0.27, 0.32)
        g = glitch()
        place(sfx[:, 0], g, c - 0.02, 0.22); place(sfx[:, 1], g, c - 0.015, 0.22)
    for ctr in edl.get("counters", []):
        g = glitch(0.07)
        place(sfx[:, 0], g, ctr["t0"], 0.2); place(sfx[:, 1], g, ctr["t0"], 0.2)
        if "tick" in ctr:
            a, b = ctr["tick"]
            tt = a
            while tt < b:
                place(sfx[:, 0], tick(), tt, 0.16); place(sfx[:, 1], tick(), tt, 0.16)
                tt += 0.08
    for L in edl.get("lists", []):
        for it in L["items"]:
            place(sfx[:, 0], tick(), it["t"], 0.25); place(sfx[:, 1], tick(), it["t"], 0.25)
            place(sfx[:, 0], buzz(), it["t"] + 0.12, 0.08); place(sfx[:, 1], buzz(), it["t"] + 0.12, 0.08)

    # --- voice: gentle compression, normalise, duck the bed ---
    v = np.zeros(n, np.float32)
    v[:len(vo)] = vo[:n]
    env = np.sqrt(np.convolve(v ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), mode="same"))
    env = np.convolve(env, np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
    duck = 1 - 0.62 * np.clip(env / (np.percentile(env[env > 1e-4], 70) + 1e-9), 0, 1)
    mix = music * duck[:, None] * 0.55 + sfx * 0.55 + v[:, None] * 1.0
    return mix[:int(dur * SR)]

def main():
    edl = json.load(open(sys.argv[1]))
    vo_path, out = sys.argv[2], sys.argv[3]
    drop_t = float(sys.argv[4]) if len(sys.argv) > 4 else edl.get("drop", 0)
    vo = load_mono(vo_path)
    # normalise the voice to about -16 LUFS before mixing
    tmp = out + ".vo16.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vo_path, "-af",
                    "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,loudnorm=I=-16:TP=-2:LRA=9",
                    "-ar", str(SR), "-ac", "1", tmp], check=True)
    vo = load_mono(tmp)
    mix = build(edl, vo, drop_t)
    pre = out + ".pre.wav"
    write(pre, mix / max(1.0, np.abs(mix).max()))
    # master: two-pass loudnorm to -14 LUFS, true peak -1
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    js = json.loads(meas[meas.rfind("{"):meas.rfind("}") + 1])
    flt = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
           f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", flt, "-ar", str(SR), out], check=True)
    chk = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "loudnorm=print_format=summary", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    print([l.strip() for l in chk.splitlines() if "Input Integrated" in l or "Input True Peak" in l])

if __name__ == "__main__":
    main()
