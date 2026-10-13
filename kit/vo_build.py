"""Tighten the pauses in a voice take and speed it up, without overlapping any voice segment.

usage: python3 vo_build.py take.wav take.words.json gaps.json out.wav [tempo]

gaps.json: list of target pauses in seconds, one per phrase boundary (phrases are split
where whisper words are more than 0.35 s apart, or by PHRASE_WORDS, a JSON list of words per phrase). Writes out.wav (48 kHz mono) and
out.segments.json (source and output ranges of every phrase, checked for overlap).
"""
import json, os, subprocess, sys
import numpy as np

SR = 48000

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def phrases(words, split=0.35):
    out, cur = [], [words[0]]
    for a, b in zip(words, words[1:]):
        if b["s"] - a["e"] > split:
            out.append(cur); cur = [b]
        else:
            cur.append(b)
    out.append(cur)
    return [{"text": " ".join(w["w"] for w in p), "s": p[0]["s"], "e": p[-1]["e"]} for p in out]

def main():
    take, wordsf, gapsf, outp = sys.argv[1:5]
    tempo = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    a = load(take)
    words = json.load(open(wordsf))
    counts = os.environ.get("PHRASE_WORDS")  # optional: JSON list of words per phrase, to split where the script says
    if counts:
        counts, ph, i = json.loads(counts), [], 0
        assert sum(counts) == len(words), f"PHRASE_WORDS adds up to {sum(counts)}, the take has {len(words)} words"
        for n in counts:
            p = words[i:i + n]; i += n
            ph.append({"text": " ".join(w["w"] for w in p), "s": p[0]["s"], "e": p[-1]["e"]})
    else:
        ph = phrases(words)
    gaps = json.load(open(gapsf))
    assert len(gaps) == len(ph) - 1, f"{len(ph)} phrases need {len(ph)-1} gaps, got {len(gaps)}"
    hop = int(0.01 * SR)
    env = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(a), hop)])
    db = 20 * np.log10(env)
    thr = float(os.environ.get("VO_THR", -42.0))  # loudness floor in dB; lower keeps soft consonants such as f and s
    lead = float(os.environ.get("VO_LEAD", 0.04))  # seconds kept before a phrase's first loud frame
    def first_loud(t0, t1):
        i0, i1 = int(t0 * 100), int(t1 * 100)
        for i in range(max(i0, 0), min(i1, len(db))):
            if db[i] > thr:
                return i / 100
        return t0
    thr_end = float(os.environ.get("VO_THR_END", -42.0))  # loudness floor for phrase ends
    def last_loud(t0, t1):
        i0, i1 = int(t0 * 100), int(t1 * 100)
        for i in range(min(i1, len(db)) - 1, max(i0, 0) - 1, -1):
            if db[i] > thr_end:
                return (i + 1) / 100
        return t1
    # refine each phrase to its audible edges, never crossing into a neighbour
    segs = []
    for k, p in enumerate(ph):
        lo = 0.0 if k == 0 else (ph[k - 1]["e"] + p["s"]) / 2
        hi = len(a) / SR if k == len(ph) - 1 else (p["e"] + ph[k + 1]["s"]) / 2
        s = max(lo, first_loud(max(lo, p["s"] - 0.3), p["s"] + 0.3) - lead)
        e = min(hi, last_loud(p["e"] - 0.3, min(hi, p["e"] + 0.35)) + 0.07)
        segs.append({"text": p["text"], "src_s": round(s, 3), "src_e": round(e, 3)})
    for x, y in zip(segs, segs[1:]):
        assert x["src_e"] <= y["src_s"], f"overlap: {x} {y}"
    fade = int(0.008 * SR)
    pieces, t = [], 0.0
    for k, sgm in enumerate(segs):
        chunk = a[int(sgm["src_s"] * SR):int(sgm["src_e"] * SR)].copy()
        chunk[:fade] *= np.linspace(0, 1, fade)
        chunk[-fade:] *= np.linspace(1, 0, fade)
        sgm["asm_s"] = round(t, 3)
        pieces.append(chunk); t += len(chunk) / SR
        sgm["asm_e"] = round(t, 3)
        if k < len(gaps):
            g = max(0.0, gaps[k])
            pieces.append(np.zeros(int(g * SR), dtype=np.float32)); t += g
    y = np.concatenate(pieces)
    tmp = outp + ".asm.wav"
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", tmp], input=pcm, check=True)
    flt = f"rubberband=tempo={tempo}:pitchq=quality:transients=crisp" if abs(tempo - 1) > 1e-3 else "anull"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", flt, "-ar", str(SR), "-ac", "1", outp])
    if r.returncode != 0 and flt.startswith("rubberband"):  # an ffmpeg built without rubberband: atempo keeps the pitch too
        print("rubberband missing, using atempo")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"atempo={tempo}", "-ar", str(SR), "-ac", "1", outp], check=True)
    elif r.returncode != 0:
        raise SystemExit("ffmpeg failed on the assembled voice")
    for sgm in segs:
        sgm["out_s"] = round(sgm["asm_s"] / tempo, 3)
        sgm["out_e"] = round(sgm["asm_e"] / tempo, 3)
    json.dump({"tempo": tempo, "segments": segs}, open(outp.rsplit(".", 1)[0] + ".segments.json", "w"), indent=1)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", outp],
                               capture_output=True, text=True).stdout)
    print(f"{len(segs)} phrases, assembled {t:.2f} s, final {dur:.2f} s at tempo {tempo}")
    for sgm in segs:
        print(f"  {sgm['out_s']:6.2f}-{sgm['out_e']:6.2f}  {sgm['text']}")

if __name__ == "__main__":
    main()
