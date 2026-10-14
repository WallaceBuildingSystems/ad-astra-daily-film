#!/usr/bin/env python3
"""Ad Astra daily film compositor, reference-clip style.

usage: python3 render.py edl.json 16x9|9x16 out_video_only.mp4

The edit decision list (edl.json) holds the timeline in seconds:
  duration, shots[{src, kind: video|image, t0, t1, focus:[x,y], z:[z0,z1], pan:[[x0,y0],[x1,y1]], src_in, speed}],
  headlines[{t0, t1, lines:[[{w, t}, ...], ...], size}], counters[{t0, t1, a, b, tick:[t0,t1], fmt, src}],
  labels[{t0, t1, text}], lists[{t0, t1, items:[...], tag, src}], subtitles[{t0, t1, text}],
  glitches[t...], end{t0, words:[{w,t}], slogan:[{w,t}], card_t, emblem, url}
Video only: mux the mix afterwards.
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

KIT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(KIT, "fonts")
FPS = 25

FORMATS = {
    "16x9": dict(W=1920, H=1080, head=148, head_maxw=0.84, head_y=0.46, sub=46, sub_y=0.925, sub_maxw=0.86,
                 counter=112, src=23, label=25, mark=330, slogan=104, rain_px=20, list_size=34),
    "9x16": dict(W=1080, H=1920, head=112, head_maxw=0.90, head_y=0.43, sub=50, sub_y=0.725, sub_maxw=0.88,
                 counter=84, src=21, label=24, mark=250, slogan=92, rain_px=20, list_size=30),
}

GREEN = np.array([0.24, 1.0, 0.62], np.float32)
PINK = np.array([1.0, 0.25, 0.75], np.float32)
CYAN = np.array([0.22, 0.9, 1.0], np.float32)
RED = (255, 72, 72)


# ---------- fonts and sprites ----------
_font_cache = {}

def font(name, size, weight=None):
    key = (name, size, weight)
    if key in _font_cache:
        return _font_cache[key]
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight is not None:
        try:
            axes = f.get_variation_axes()
            vals = []
            for ax in axes:
                n = ax["name"].decode() if isinstance(ax["name"], bytes) else ax["name"]
                if "eight" in n:
                    vals.append(weight)
                elif "ptical" in n:
                    vals.append(max(ax["minimum"], min(ax["maximum"], 32)))
                else:
                    vals.append(ax["default"])
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    _font_cache[key] = f
    return f

def head_font(size):
    return font("InterTight.ttf", size, 850)

def sub_font(size):
    return font("Inter.ttf", size, 700)

def mono_font(size):
    return font("IBMPlexMono-Bold.ttf", size)

def tracked_width(text, f, track):
    return sum(f.getlength(c) for c in text) + track * max(0, len(text) - 1)

def sprite(text, f, color=(255, 255, 255), glow=0.0, glow_r=0, shadow=0.0, track=0.0):
    """Render text to a premultiplied float32 RGBA array with optional glow and soft shadow.
    Returns (arr, ox, oy, w_text): arr origin is offset (ox, oy) from the text origin (left, top of em box)."""
    asc, desc = f.getmetrics()
    w = int(math.ceil(tracked_width(text, f, track))) if track else int(math.ceil(f.getlength(text)))
    h = asc + desc
    pad = int(max(glow_r * 3, 12 if shadow else 4))
    im = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    if track:
        x = pad
        for c in text:
            d.text((x, pad), c, font=f, fill=255)
            x += f.getlength(c) + track
    else:
        d.text((pad, pad), text, font=f, fill=255)
    a = np.asarray(im, np.float32) / 255.0
    col = np.array(color, np.float32) / 255.0
    rgb = a[..., None] * col
    alpha = a.copy()
    if shadow:
        s = cv2.GaussianBlur(a, (0, 0), max(2, pad / 3)) * shadow
        # shadow is dark: it only adds alpha, no colour
        alpha = alpha + s * (1 - alpha)
    if glow:
        g1 = cv2.GaussianBlur(a, (0, 0), max(1, glow_r)) * glow
        g2 = cv2.GaussianBlur(a, (0, 0), max(1, glow_r * 0.35)) * glow * 0.8
        g = np.clip(g1 + g2, 0, 1)
        rgb = rgb + g[..., None] * col * (1 - a[..., None])
        alpha = alpha + g * (1 - alpha)
    arr = np.dstack([rgb, np.clip(alpha, 0, 1)]).astype(np.float32)
    return arr, -pad, -pad, w

def blend(frame, spr, x, y, opacity=1.0, scale=1.0):
    """Composite premultiplied RGBA sprite onto float frame at top-left (x, y)."""
    if opacity <= 0.002:
        return
    if abs(scale - 1.0) > 1e-3:
        h0, w0 = spr.shape[:2]
        nw, nh = max(1, int(w0 * scale)), max(1, int(h0 * scale))
        x += (w0 - nw) / 2
        y += (h0 - nh) / 2
        spr = cv2.resize(spr, (nw, nh), interpolation=cv2.INTER_LINEAR)
    x, y = int(round(x)), int(round(y))
    H, W = frame.shape[:2]
    h, w = spr.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * opacity
    frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - a) + s[..., :3] * opacity

def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3

def ramp(t, t0, t1, fade_in=0.12, fade_out=0.10):
    if t < t0 or t > t1:
        return 0.0
    a = min(1.0, (t - t0) / fade_in) if fade_in > 0 else 1.0
    b = min(1.0, (t1 - t) / fade_out) if fade_out > 0 else 1.0
    return max(0.0, min(a, b))


# ---------- film looks (photoreal pass) ----------
# sat: colour kept, tone: print tint, soft: lens softness (px at 1080 lines), hal: red-orange halation,
# grain: grain strength, dust: specks a frame, scratch: chance of a scratch, flick: exposure flicker,
# weave: gate weave (px at 1080 lines), lift / crush: faded blacks and rolled-off whites
LOOKS = {
    "plate":    dict(sat=0.00, tone=(1.06, 0.99, 0.86), soft=1.3, hal=0.20, grain=0.060, dust=8, scratch=0.05, flick=0.045, weave=2.0, lift=0.055, crush=0.92),
    "archival": dict(sat=0.30, tone=(1.05, 0.99, 0.88), soft=1.1, hal=0.18, grain=0.055, dust=5, scratch=0.035, flick=0.035, weave=1.6, lift=0.045, crush=0.94),
    "early":    dict(sat=0.12, tone=(1.03, 1.00, 0.93), soft=0.9, hal=0.16, grain=0.050, dust=3, scratch=0.025, flick=0.030, weave=1.3, lift=0.040, crush=0.95),
    "reel16":   dict(sat=0.0, tone=(1.025, 1.00, 0.955), soft=1.5, hal=0.12, grain=0.095, dust=9, scratch=0.06, flick=0.05, weave=2.2, lift=0.05, crush=0.93, hand=1.0),
    "snap":     dict(sat=0.78, tone=(1.02, 1.00, 0.97), soft=1.0, hal=0.12, grain=0.058, dust=2, scratch=0.0, flick=0.012, weave=1.0, lift=0.04, crush=0.95, hand=0.7),
    "film":     dict(sat=0.88, tone=(1.03, 1.00, 0.95), soft=0.6, hal=0.14, grain=0.040, dust=0, scratch=0.0, flick=0.010, weave=0.5, lift=0.025, crush=0.97),
    "modern":   dict(sat=0.94, tone=(1.02, 1.00, 0.97), soft=0.45, hal=0.10, grain=0.032, dust=0, scratch=0.0, flick=0.0, weave=0.0, lift=0.018, crush=0.98),
}
HAL_TINT = np.array([1.0, 0.55, 0.32], np.float32)

def apply_look(frame, look, i, W, H):
    L = LOOKS.get(look, LOOKS["modern"])
    sc = H / 1080.0 if W > H else W / 1080.0
    lum = frame[..., 0] * 0.299 + frame[..., 1] * 0.587 + frame[..., 2] * 0.114
    if L["sat"] < 0.999:
        frame = lum[..., None] + (frame - lum[..., None]) * L["sat"]
    frame = frame * np.array(L["tone"], np.float32)
    if L["soft"] > 0.05:
        frame = cv2.GaussianBlur(frame, (0, 0), L["soft"] * sc)
    if L["hal"] > 0:
        small = cv2.resize(lum, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        hl = np.clip((small - 0.66) / 0.34, 0, 1) ** 1.5
        hl = cv2.GaussianBlur(hl, (0, 0), 5)
        hl = cv2.resize(hl, (W, H), interpolation=cv2.INTER_LINEAR)
        frame = frame + hl[..., None] * HAL_TINT * L["hal"]
    if L["flick"] > 0:
        r = np.random.default_rng(5000 + i)
        f = 1 + L["flick"] * (0.5 * math.sin(i * 2.3) + 0.3 * math.sin(i * 0.61 + 1.7) + 0.4 * r.uniform(-1, 1))
        frame = frame * f
    frame = L["lift"] + np.clip(frame, 0, 1.2) * (L["crush"] - L["lift"])
    if L["dust"] > 0 or L["scratch"] > 0:
        r = np.random.default_rng(9000 + i)
        mark = np.zeros((H, W), np.float32)
        for _ in range(r.poisson(L["dust"])):
            x, y = int(r.uniform(0, W)), int(r.uniform(0, H))
            rad = max(1, int(r.uniform(0.8, 3.2) * sc))
            if r.random() < 0.18:  # a hair or fibre
                pts = np.cumsum(r.normal(0, 3 * sc, (6, 2)), 0).astype(np.int32) + [x, y]
                cv2.polylines(mark, [pts], False, -0.55, max(1, int(sc)), cv2.LINE_AA)
            else:
                cv2.circle(mark, (x, y), rad, -0.7 if r.random() < 0.7 else 0.45, -1, cv2.LINE_AA)
        rs = np.random.default_rng(777 + i // 4)
        if rs.random() < L["scratch"] * 4:
            x = int(rs.uniform(0.05, 0.95) * W) + int(r.normal(0, 1.5))
            cv2.line(mark, (x, 0), (x + int(r.normal(0, 3)), H), 0.22 if rs.random() < 0.5 else -0.25, max(1, int(sc)), cv2.LINE_AA)
        mark = cv2.GaussianBlur(mark, (0, 0), 0.7 * sc)
        frame = frame + mark[..., None] * np.clip(frame + 0.25, 0, 1)
    return frame


# ---------- footage ----------
class Shot:
    def __init__(self, d, W, H):
        self.d, self.W, self.H = d, W, H
        self.kind = d.get("kind", "image")
        self.t0, self.t1 = d["t0"], d["t1"]
        self.focus = d.get("focus", [0.5, 0.5])
        self.z = d.get("z", [1.0, 1.06] if self.kind == "video" else [1.02, 1.12])
        self.pan = d.get("pan", [[0, 0], [0, 0]])
        self.look = d.get("look", "modern")
        self.weave = LOOKS.get(self.look, LOOKS["modern"])["weave"]
        self.hand = LOOKS.get(self.look, LOOKS["modern"]).get("hand", 0.0)
        if self.weave > 0:  # leave room for the gate weave
            self.z = [max(self.z[0], 1.035), max(self.z[1], 1.05)]
        if self.hand > 0:  # and for the handheld drift
            self.z = [max(self.z[0], 1.07), max(self.z[1], 1.08)]
        self.cap = None
        self.img = None
        self.last = None
        self.idx = -1

    def open(self):
        if self.kind == "video":
            self.cap = cv2.VideoCapture(self.d["src"])
            self.sfps = self.cap.get(cv2.CAP_PROP_FPS) or 24
            self.nframes = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            start = int(self.d.get("src_in", 0) * self.sfps)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, start)
            self.idx = start - 1
        else:
            im = cv2.imread(self.d["src"], cv2.IMREAD_COLOR)
            self.img = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    def close(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = None
        self.img = None
        self.last = None

    def source_frame(self, t):
        if self.kind != "video":
            return self.img
        st = self.d.get("src_in", 0) + (t - self.t0) * self.d.get("speed", 1.0)
        want = min(int(st * self.sfps), self.nframes - 1)
        while self.idx < want:
            ok, fr = self.cap.read()
            if not ok:
                break
            self.idx += 1
            self.last = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        if self.last is None:
            ok, fr = self.cap.read()
            self.last = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        return self.last

    def frame(self, t):
        src = self.source_frame(t)
        sh, sw = src.shape[:2]
        A = self.W / self.H
        if sw / sh > A:
            ch, cw = sh, sh * A
        else:
            cw, ch = sw, sw / A
        u = (t - self.t0) / max(1e-6, self.t1 - self.t0)
        z = self.z[0] + (self.z[1] - self.z[0]) * u
        px = self.pan[0][0] + (self.pan[1][0] - self.pan[0][0]) * u
        py = self.pan[0][1] + (self.pan[1][1] - self.pan[0][1]) * u
        cw, ch = cw / z, ch / z
        cx = self.focus[0] * sw + px * cw
        cy = self.focus[1] * sh + py * ch
        if self.weave > 0:
            i = int(round(t * FPS))
            r = np.random.default_rng(31337 + i)
            wpx = self.weave * (self.H / 1080.0 if self.W > self.H else self.W / 1080.0)
            dx = wpx * (0.55 * math.sin(i * 0.37) + 0.3 * math.sin(i * 1.13 + 2.0) + 0.25 * r.normal())
            dy = wpx * 0.7 * (0.5 * math.sin(i * 0.29 + 1.0) + 0.3 * math.sin(i * 0.97) + 0.25 * r.normal())
            cx += dx * cw / self.W
            cy += dy * ch / self.H
        if self.hand > 0:  # slow handheld sway, a few tenths of a per cent of the frame
            cx += self.hand * cw * (0.006 * math.sin(t * 1.3 + 0.4) + 0.004 * math.sin(t * 3.1 + 1.7))
            cy += self.hand * ch * (0.005 * math.sin(t * 1.1 + 2.1) + 0.004 * math.sin(t * 2.7))
        x0 = min(max(0, cx - cw / 2), sw - cw)
        y0 = min(max(0, cy - ch / 2), sh - ch)
        M = np.array([[self.W / cw, 0, -x0 * self.W / cw], [0, self.H / ch, -y0 * self.H / ch]], np.float32)
        interp = cv2.INTER_AREA if cw > self.W * 1.15 else cv2.INTER_LINEAR
        if interp == cv2.INTER_AREA:
            crop = src[int(y0):int(math.ceil(y0 + ch)), int(x0):int(math.ceil(x0 + cw))]
            out = cv2.resize(crop, (self.W, self.H), interpolation=cv2.INTER_AREA)
        else:
            out = cv2.warpAffine(src, M, (self.W, self.H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return out.astype(np.float32) / 255.0


# ---------- procedural layers ----------
def make_vignette(W, H):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (x / W - 0.5) * 2, (y / H - 0.5) * 2
    r = np.sqrt(nx ** 2 * 0.85 + ny ** 2 * 0.85)
    v = 1 - 0.62 * np.clip(r, 0, 1.6) ** 2.4
    return np.clip(v, 0.18, 1)[..., None].astype(np.float32)

def make_rain(W, H, px, seed):
    rng = np.random.default_rng(seed)
    f = mono_font(px)
    glyphs = "01ABCDEFabcdef{}[]()<>=+-*/;:#$%&_.,|\\^~アイウエオカキクケコサシスセソ"
    # fall back to ASCII if the mono font lacks katakana
    glyphs = "".join(c for c in glyphs if f.getbbox(c)[2] > 0) or "01"
    TH = H * 2
    im = Image.new("L", (W, TH), 0)
    d = ImageDraw.Draw(im)
    colw = int(px * 0.95)
    for x in range(0, W, colw):
        if rng.random() < 0.45:
            continue
        y = rng.integers(-TH, 0)
        while y < TH:
            n = rng.integers(6, 28)
            for k in range(n):
                b = int(255 * (0.25 + 0.75 * (k / n) ** 2))
                d.text((x, y + k * px), glyphs[rng.integers(len(glyphs))], font=f, fill=b)
            y += n * px + rng.integers(px * 4, px * 30)
    a = np.asarray(im, np.float32) / 255.0
    a = np.concatenate([a, a], 0)
    return a

def make_grid(W, H):
    im = np.zeros((H, W), np.float32)
    vy = int(H * 0.38)
    for k in range(-14, 15):
        x_bottom = W / 2 + k * W * 0.11
        cv2.line(im, (int(W / 2 + k * W * 0.02), vy), (int(x_bottom), H), 1.0, 2, cv2.LINE_AA)
    for k in range(14):
        y = vy + (H - vy) / (1 + 0.55 * k)
        cv2.line(im, (0, int(y)), (W, int(y)), 1.0, 2, cv2.LINE_AA)
    im[: vy] = 0
    for k in range(-8, 9):
        cv2.line(im, (int(W / 2 + k * W * 0.09), 0), (int(W / 2 + k * W * 0.12), vy), 0.6, 1, cv2.LINE_AA)
    im = cv2.GaussianBlur(im, (0, 0), 0.8)
    return im

def make_streak(length, thick, color):
    h = thick * 8
    im = np.zeros((h, length), np.float32)
    cv2.line(im, (thick * 2, h // 2), (length - thick * 2, h // 2), 1.0, thick, cv2.LINE_AA)
    im = cv2.GaussianBlur(im, (0, 0), sigmaX=thick * 2.5, sigmaY=thick * 0.9)
    prof = np.clip(np.sin(np.linspace(0, math.pi, length)) ** 0.6, 0, 1)
    im = im * prof[None, :]
    im = im / max(1e-6, im.max())
    rgb = im[..., None] * color
    return np.dstack([rgb, im * 0.9]).astype(np.float32)


# ---------- counters ----------
def fmt_value(v, fmt, unit="", prefix=""):
    """A counter's number as shown: prefix ("Over "), the number, then the unit ("%", " m")."""
    if fmt == "money":
        s = f"${v:,.0f}" if v >= 9.995 else f"${v:,.2f}"
    elif fmt == "dec1":
        s = f"{v:,.1f}" if v < 9.95 else f"{v:,.0f}"
    elif fmt == "int":
        s = f"{v:,.0f}"
    else:
        s = str(v)
    return f"{prefix}{s}{unit}"


def counter_text(c, v):
    """Text for value v of counter c: a_label or b_label replace the start or end value when given."""
    if v == float(c["b"]) and c.get("b_label"):
        return c["b_label"]
    if v == float(c["a"]) and c.get("a_label"):
        return c["a_label"]
    return fmt_value(v, c["fmt"], c.get("unit", ""), c.get("prefix", ""))

def counter_value(c, t):
    a, b = float(c["a"]), float(c["b"])
    t0, t1 = c.get("tick", [c["t0"], c["t0"]])
    if t <= t0 or t1 <= t0:
        return a
    u = ease_out((t - t0) / (t1 - t0))
    if u >= 1:
        return b
    lo = max(a, 1.0) if a <= 0 else a
    if b > 0 and lo > 0 and (b / lo > 50 or lo / b > 50 or a <= 0):
        v = math.exp(math.log(lo) + (math.log(b) - math.log(lo)) * u)
        return v if a > 0 or u > 0.02 else 0.0
    return a + (b - a) * u


# ---------- main render ----------
def render(edl, fmt, out):
    P = FORMATS[fmt]
    W, H = P["W"], P["H"]
    dur = edl["duration"]
    n = int(round(dur * FPS))
    vign = make_vignette(W, H)
    grade = np.array([1.045, 1.0, 0.93], np.float32)
    rng = np.random.default_rng(7)
    grains = [rng.normal(0, 0.032, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
    grains = [cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] for g in grains]
    rain1 = make_rain(W, H, P["rain_px"], 1)
    rain2 = make_rain(W, H, int(P["rain_px"] * 0.75), 2)
    grid = make_grid(W, H)
    streaks = [make_streak(int(W * L), th, col) for L, th, col in
               [(0.55, 6, PINK), (0.4, 4, CYAN), (0.7, 3, PINK), (0.35, 8, CYAN), (0.6, 5, PINK), (0.5, 3, CYAN)]]

    shots = [Shot(s, W, H) for s in edl["shots"]]
    cuts = sorted(set([s["t0"] for s in edl["shots"] if s["t0"] > 0.05] + edl.get("glitches", [])))

    # --- prepare headline sprites ---
    hf = head_font(P["head"])
    space = hf.getlength(" ")
    heads = []
    for h in edl.get("headlines", []):
        size = int(P["head"] * h.get("scale", 1.0))
        maxw = W * P["head_maxw"]
        # shrink until every given line fits on one row (down to 72 per cent), then wrap if still needed
        while size > P["head"] * 0.72:
            f = head_font(size)
            sp = f.getlength(" ")
            if all(sum(f.getlength(wd["w"]) for wd in line) + sp * (len(line) - 1) <= maxw for line in h["lines"]):
                break
            size -= 4
        f = head_font(size)
        sp = f.getlength(" ")
        # wrap: each given line may wrap further
        lines = []
        for line in h["lines"]:
            cur, curw = [], 0
            for wd in line:
                ww = f.getlength(wd["w"])
                if cur and curw + sp + ww > maxw:
                    lines.append(cur); cur, curw = [], 0
                cur.append(dict(wd, ww=ww)); curw += (sp if len(cur) > 1 else 0) + ww
            if cur:
                lines.append(cur)
        lh = size * 1.0
        total_h = lh * len(lines)
        y0 = H * P["head_y"] - total_h / 2 + h.get("dy", 0) * H
        items = []
        for li, line in enumerate(lines):
            lw = sum(w["ww"] for w in line) + sp * (len(line) - 1)
            x = W / 2 - lw / 2
            y = y0 + li * lh
            for wd in line:
                arr, ox, oy, _ = sprite(wd["w"], f, glow=0.55, glow_r=size * 0.16, shadow=0.55)
                items.append(dict(t=wd["t"], arr=arr, x=x + ox, y=y + oy - size * 0.12))
                x += wd["ww"] + sp
        heads.append(dict(t0=h["t0"], t1=h["t1"], items=items, bottom=y0 + total_h))

    # --- subtitles ---
    sf = sub_font(P["sub"])
    subs = []
    for s in edl.get("subtitles", []):
        text = s["text"]
        # wrap to two lines if needed
        words = text.split()
        lines, cur = [], ""
        for wd in words:
            test = (cur + " " + wd).strip()
            if sf.getlength(test) > W * P["sub_maxw"] and cur:
                lines.append(cur); cur = wd
            else:
                cur = test
        lines.append(cur)
        sprs = []
        for li, ln in enumerate(lines):
            arr, ox, oy, w = sprite(ln, sf, glow=0.15, glow_r=6, shadow=0.85)
            sprs.append((arr, W / 2 - w / 2 + ox, H * P["sub_y"] - (len(lines) - li) * P["sub"] * 1.18 + oy))
        subs.append(dict(t0=s["t0"], t1=s["t1"], sprs=sprs))

    # --- labels (mono caps) ---
    labels = []
    for l in edl.get("labels", []):
        text = l["text"].upper()
        size = P["label"]
        maxw = W * 0.9
        # a long label breaks onto 2 lines at its last full stop ("... . SOURCE: ..."), "\n" forces a break
        parts = text.split("\n")
        if len(parts) == 1 and (tracked_width(text, mono_font(size), size * 0.08) > maxw or (fmt == "9x16" and len(text) > 48)):
            cut = text.rfind(". ", 0, len(text) - 2)
            if cut > 0:
                parts = [text[:cut + 1], text[cut + 2:]]
        while size > 12 and max(tracked_width(p, mono_font(size), size * 0.08) for p in parts) > maxw:
            size -= 1
        f2 = mono_font(size)
        y = H * (P["head_y"] + l.get("dy", 0.11))
        for h in heads:  # keep clear of any headline on screen at the same time
            if h["t0"] < l["t1"] and l["t0"] < h["t1"]:
                y = max(y, h["bottom"] + H * 0.03)
        sprs = []
        for k, ptxt in enumerate(parts):
            arr, ox, oy, w = sprite(ptxt, f2, color=(235, 235, 235), glow=0.25, glow_r=5, shadow=0.7, track=size * 0.08)
            sprs.append((arr, W / 2 - w / 2 + ox, y + k * size * 1.5 + oy))
        labels.append(dict(t0=l["t0"], t1=l["t1"], sprs=sprs))

    # --- counters ---
    cf_size = P["counter"]
    counters = []
    for c in edl.get("counters", []):
        a_str = c.get("a_label") or fmt_value(float(c["a"]), c["fmt"], c.get("unit", ""), c.get("prefix", ""))
        b_final = counter_text(c, float(c["b"]))
        full = b_final if float(c["a"]) == float(c["b"]) else f"{a_str} → {b_final}"  # a fixed value shows alone
        size = cf_size
        while mono_font(size).getlength(full) > W * 0.88 and size > 30:
            size -= 2
        f = mono_font(size)
        x_left = W / 2 - f.getlength(full) / 2
        y = H * P["head_y"] - size * 0.62
        src_text = c["src"].upper()
        sfz = P["src"]
        # a long source line breaks onto 2 lines at its last full stop first, then shrinks to fit
        src_lines = [src_text]
        if tracked_width(src_text, mono_font(sfz), sfz * 0.06) > W * 0.9 or (fmt == "9x16" and len(src_text) > 48):
            cut = src_text.rfind(". ", 0, len(src_text) - 2)
            if cut > 0:
                src_lines = [src_text[:cut + 1], src_text[cut + 2:]]
        while max(tracked_width(ln, mono_font(sfz), sfz * 0.06) for ln in src_lines) > W * 0.9 and sfz > 12:
            sfz -= 1
        src_sprs = []
        for k, ln in enumerate(src_lines):
            arr, ox, oy, w = sprite(ln, mono_font(sfz), color=(225, 225, 225), glow=0.2, glow_r=4, shadow=0.7, track=sfz * 0.06)
            src_sprs.append((arr, W / 2 - w / 2 + ox, y + size * 1.32 + k * sfz * 1.5 + oy))
        counters.append(dict(c=c, f=f, size=size, x=x_left, y=y, a_str=a_str, src=src_sprs, cache={}))

    # --- lists ---
    lists = []
    for L in edl.get("lists", []):
        f = mono_font(P["list_size"])
        rows = []
        lh = P["list_size"] * 1.45
        y0 = H * P["head_y"] - lh * len(L["items"]) / 2
        tag = L.get("tag", "FAILED")
        namew = max(f.getlength(it["text"].upper()) for it in L["items"])
        blockw = namew + f.getlength("   " + tag)
        x = W / 2 - blockw / 2
        for k, it in enumerate(L["items"]):
            text = it["text"].upper()
            a1, ox, oy, w1 = sprite(text, f, glow=0.25, glow_r=5, shadow=0.7)
            a2, ox2, oy2, _ = sprite(tag, f, color=RED, glow=0.5, glow_r=7, shadow=0.7)
            rows.append(dict(t=it["t"], a1=a1, x1=x + ox, a2=a2, x2=x + namew + f.getlength("   ") + ox2, y=y0 + k * lh + oy))
        src = None
        if L.get("src"):
            arr, ox, oy, w = sprite(L["src"].upper(), mono_font(P["src"]), color=(225, 225, 225), shadow=0.7, track=P["src"] * 0.06)
            src = (arr, W / 2 - w / 2 + ox, y0 + lh * len(L["items"]) + P["src"] + oy)
        lists.append(dict(t0=L["t0"], t1=L["t1"], rows=rows, src=src))

    # --- end ---
    end = edl.get("end")
    if end:
        msize = P["mark"]
        words = end["words"]
        while True:
            mf = head_font(msize)
            widths = [mf.getlength(w["w"]) for w in words]
            sp = mf.getlength(" ")
            tw = sum(widths) + sp * (len(words) - 1)
            if tw <= W * 0.86 or msize < 60:
                break
            msize -= 6
        P = dict(P, mark=msize)
        x = W / 2 - tw / 2
        my = H * (0.40 if fmt == "16x9" else 0.40) - P["mark"] * 0.55
        mark = []
        for w, ww in zip(words, widths):
            arr, ox, oy, _ = sprite(w["w"], mf, glow=0.75, glow_r=P["mark"] * 0.14, shadow=0.4)
            mark.append(dict(t=w["t"], arr=arr, x=x + ox, y=my + oy))
            x += ww + sp
        sfont = head_font(P["slogan"])
        sw = [sfont.getlength(w["w"]) for w in end["slogan"]]
        ssp = sfont.getlength(" ")
        stw = sum(sw) + ssp * (len(sw) - 1)
        x = W / 2 - stw / 2
        sy = my + P["mark"] * 1.15
        slogan = []
        for w, ww in zip(end["slogan"], sw):
            arr, ox, oy, _ = sprite(w["w"], sfont, glow=0.6, glow_r=P["slogan"] * 0.15, shadow=0.4)
            slogan.append(dict(t=w["t"], arr=arr, x=x + ox, y=sy + oy))
            x += ww + ssp
        # end card
        card = []
        if end.get("emblem") and os.path.exists(end["emblem"]):
            em = cv2.cvtColor(cv2.imread(end["emblem"]), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            es = int(min(W, H) * (0.30 if fmt == "16x9" else 0.40))
            em = cv2.resize(em, (es, es), interpolation=cv2.INTER_AREA)
            em = np.clip((em - 0.07) / 0.93, 0, 1)  # crush the jpeg's near-black box to true black
            lum = em.max(axis=2, keepdims=True)
            card.append(("emblem", np.dstack([em, lum]).astype(np.float32), W / 2 - es / 2, H * (0.36 if fmt == "16x9" else 0.37) - es / 2))
            base_y = H * (0.36 if fmt == "16x9" else 0.37) + es * 0.52
        else:
            base_y = H * 0.48
        wm_size = int(P["mark"] * 0.24)
        wmf = font("InterTight.ttf", wm_size, 500)
        arr, ox, oy, w = sprite("AD ASTRA", wmf, glow=0.35, glow_r=8, track=wm_size * 0.42)
        card.append(("wordmark", arr, W / 2 - w / 2 + ox, base_y + oy))
        uf = mono_font(int(P["src"] * 1.25))
        utext = end.get("url_line", "APPLY AT JOINADASTRA.COM").upper()
        arr, ox, oy, w = sprite(utext, uf, color=(225, 225, 225), glow=0.2, glow_r=4, track=P["src"] * 0.12)
        card.append(("url", arr, W / 2 - w / 2 + ox, base_y + wm_size * 1.9 + oy))
        end_d = dict(t0=end["t0"], mark=mark, slogan=slogan, card_t=end["card_t"], card=card)
    else:
        end_d = None

    # --- ffmpeg sink ---
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "14M", "-bufsize", "28M",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    preview = [float(x) for x in os.environ.get("PREVIEW", "").split(",") if x.strip()]
    sink = None if preview else subprocess.Popen(cmd, stdin=subprocess.PIPE)
    want = set(int(round(x * FPS)) for x in preview)

    cur = None
    for i in range(n):
        t = i / FPS
        if preview and i not in want:
            continue
        # footage
        active = None
        for s in shots:
            if s.t0 <= t < s.t1 + 1e-6:
                active = s
        if end_d and t >= end_d["card_t"]:
            frame = np.zeros((H, W, 3), np.float32)
        elif active is None:
            frame = np.zeros((H, W, 3), np.float32)
        else:
            if cur is not active:
                if cur is not None:
                    cur.close()
                active.open()
                cur = active
            frame = active.frame(t)
            frame = np.clip((frame - 0.5) * 1.05 + 0.5, 0, 1)
            frame = apply_look(frame, active.look, i, W, H)
            frame *= vign

        # overlay activity -> dim the picture under text
        k_dim = 0.0
        for h in heads:
            k_dim = max(k_dim, ramp(t, h["t0"], h["t1"]) * 0.42)
        for c in counters:
            k_dim = max(k_dim, ramp(t, c["c"]["t0"], c["c"]["t1"]) * 0.55)
        for L in lists:
            k_dim = max(k_dim, ramp(t, L["t0"], L["t1"]) * 0.6)
        if end_d and t >= end_d["t0"]:
            k_dim = max(k_dim, min(1.0, (t - end_d["t0"]) / 0.25) * 0.78)
        if k_dim > 0:
            frame *= 1 - k_dim

        # code rain and grid
        rain_k = 0.0
        for c in counters:
            rain_k = max(rain_k, ramp(t, c["c"]["t0"], c["c"]["t1"], 0.2, 0.2))
        for L in lists:
            rain_k = max(rain_k, 0.6 * ramp(t, L["t0"], L["t1"], 0.2, 0.2))
        for tc in cuts:
            if abs(t - tc) < 0.3:
                rain_k = max(rain_k, 0.55 * (1 - abs(t - tc) / 0.3))
        if end_d and t >= end_d["t0"] and t < end_d["card_t"]:
            rain_k = max(rain_k, 0.75)
        if rain_k > 0.01:
            o1 = int((t * H * 0.45) % (H * 2))
            o2 = int((t * H * 0.28 + H * 0.7) % (H * 2))
            r = rain1[o1:o1 + H] * 0.42 + rain2[o2:o2 + H] * 0.25
            # keep the centre clearer for text
            frame += (r[..., None] * GREEN) * rain_k * 0.7
        grid_k = 0.0
        for c in counters:
            grid_k = max(grid_k, ramp(t, c["c"]["t0"], c["c"]["t1"], 0.25, 0.2))
        if grid_k > 0.01:
            frame += grid[..., None] * (GREEN * 0.55) * 0.22 * grid_k

        # light streaks at cuts and during counters
        sk = 0.0
        for tc in cuts:
            if abs(t - tc) < 0.16:
                sk = max(sk, 1 - abs(t - tc) / 0.16)
        for c in counters:
            sk = max(sk, 0.35 * ramp(t, c["c"]["t0"], c["c"]["t1"]))
        if sk > 0.02:
            rs = np.random.default_rng(i // 2)
            for _ in range(3 if sk > 0.5 else 2):
                st = streaks[rs.integers(len(streaks))]
                yy = rs.uniform(0.05, 0.95) * H
                xx = rs.uniform(-0.3, 0.8) * W
                blend(frame, st, xx, yy, opacity=0.85 * sk)

        # headlines
        for h in heads:
            if not (h["t0"] - 0.01 <= t <= h["t1"]):
                continue
            fade_out = ramp(t, h["t0"] - 1, h["t1"], 0.001, 0.12)
            for it in h["items"]:
                if t < it["t"]:
                    continue
                u = (t - it["t"]) / 0.14
                op = min(1.0, u) * fade_out
                sc = 1.0 + 0.06 * (1 - ease_out(u))
                blend(frame, it["arr"], it["x"], it["y"], op, sc)

        # labels
        for l in labels:
            op = ramp(t, l["t0"], l["t1"], 0.15, 0.12)
            if op > 0:
                for arr, x, y in l["sprs"]:
                    blend(frame, arr, x, y, op)

        # counters
        for c in counters:
            op = ramp(t, c["c"]["t0"], c["c"]["t1"], 0.08, 0.1)
            if op <= 0:
                continue
            v = counter_value(c["c"], t)
            b_str = counter_text(c["c"], v) if v == float(c["c"]["b"]) else \
                fmt_value(v, c["c"]["fmt"], c["c"].get("unit", ""), c["c"].get("prefix", ""))
            key = b_str
            if key not in c["cache"]:
                txt = b_str if float(c["c"]["a"]) == float(c["c"]["b"]) else f"{c['a_str']} → {b_str}"
                arr, ox, oy, w = sprite(txt, c["f"], glow=0.5, glow_r=c["size"] * 0.14, shadow=0.5)
                c["cache"][key] = (arr, ox, oy)
                if len(c["cache"]) > 64:
                    c["cache"].pop(next(iter(c["cache"])))
            arr, ox, oy = c["cache"][key]
            blend(frame, arr, c["x"] + ox, c["y"] + oy, op)
            for arr2, x2, y2 in c["src"]:
                blend(frame, arr2, x2, y2, op)

        # lists
        for L in lists:
            op = ramp(t, L["t0"], L["t1"], 0.08, 0.1)
            if op <= 0:
                continue
            for r in L["rows"]:
                if t >= r["t"]:
                    blend(frame, r["a1"], r["x1"], r["y"], op)
                    if t >= r["t"] + 0.12:
                        blend(frame, r["a2"], r["x2"], r["y"], op)
            if L["src"]:
                blend(frame, L["src"][0], L["src"][1], L["src"][2], op)

        # end
        if end_d and t >= end_d["t0"]:
            if t < end_d["card_t"]:
                for it in end_d["mark"] + end_d["slogan"]:
                    if t >= it["t"]:
                        u = (t - it["t"]) / 0.16
                        blend(frame, it["arr"], it["x"], it["y"], min(1.0, u), 1.0 + 0.08 * (1 - ease_out(u)))
            else:
                u = (t - end_d["card_t"]) / 0.45
                for kind, arr, x, y in end_d["card"]:
                    blend(frame, arr, x, y, min(1.0, max(0.0, u)))

        # subtitles
        for s in subs:
            op = ramp(t, s["t0"], s["t1"], 0.06, 0.06)
            if op > 0:
                for arr, x, y in s["sprs"]:
                    blend(frame, arr, x, y, op)

        # glitch around cuts
        g = 0.0
        for tc in cuts:
            if abs(t - tc) < 0.13:
                g = max(g, 1 - abs(t - tc) / 0.13)
        if g > 0.05:
            rs = np.random.default_rng(1000 + i)
            dx = int(16 * g * W / 1920) + 1
            frame[..., 0] = np.roll(frame[..., 0], dx, axis=1)
            frame[..., 2] = np.roll(frame[..., 2], -dx, axis=1)
            for _ in range(int(4 + 8 * g)):
                y0 = int(rs.uniform(0, H - 8))
                hh = int(rs.uniform(4, H * 0.06))
                sh = int(rs.uniform(-1, 1) * 90 * g * W / 1920)
                frame[y0:y0 + hh] = np.roll(frame[y0:y0 + hh], sh, axis=1)
            if g > 0.5:
                frame[::3] *= 0.86

        # grain
        gk = LOOKS.get(active.look, LOOKS["modern"])["grain"] / 0.032 if active is not None else 1.0
        if end_d and t >= end_d["card_t"]:
            gk = 0.4
        frame += grains[i % len(grains)] * gk * 0.85
        out8 = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
        if preview:
            Image.fromarray(out8).save(out.rsplit(".", 1)[0] + f"_{t:05.2f}.png")
            continue
        sink.stdin.write(out8.tobytes())
        if i % 100 == 0:
            print(f"  {fmt} frame {i}/{n}", flush=True)
    if cur is not None:
        cur.close()
    if sink:
        sink.stdin.close()
        sink.wait()
    print("wrote", out)


if __name__ == "__main__":
    edl = json.load(open(sys.argv[1]))
    render(edl, sys.argv[2], sys.argv[3])
