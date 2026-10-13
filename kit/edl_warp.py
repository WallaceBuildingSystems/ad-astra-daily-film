"""Re-time an edit list onto a new voice take of the same script (a new voice, a re-read line).

usage: python3 edl_warp.py old_edl.json old.segments.json new.segments.json new.words.json out_edl.json

Every time in the edit list (shots, headlines, labels, counters, lists, subtitles, glitches, end) is
mapped piecewise-linearly from the old voice's phrase boundaries to the new voice's, so every word
keeps its place inside its phrase. The phrases must match one
to one (same count, same order); the script prints both lists so a mismatch is obvious.
"""
import bisect, json, re, sys

old_edl, old_seg, new_seg, new_words, out = sys.argv[1:6]
E = json.load(open(old_edl))
A = json.load(open(old_seg))["segments"]
B = json.load(open(new_seg))["segments"]
W = json.load(open(new_words))
assert len(A) == len(B), f"old has {len(A)} phrases, new has {len(B)}"
for a, b in zip(A, B):
    print(f"{a['out_s']:6.2f} {a['text'][:34]:<36} -> {b['out_s']:6.2f} {b['text'][:40]}")

old_end, new_end = A[-1]["out_e"], B[-1]["out_e"]
tail = E["duration"] - old_end  # end card length after the last word stays the same
xs, ys = [0.0], [0.0]
for a, b in zip(A, B):
    for x, y in ((a["out_s"], b["out_s"]), (a["out_e"], b["out_e"])):
        if x > xs[-1] and y > ys[-1]:
            xs.append(x); ys.append(y)
xs.append(E["duration"]); ys.append(new_end + tail)


def warp(t):
    if t <= 0:
        return t
    i = min(max(bisect.bisect_right(xs, t) - 1, 0), len(xs) - 2)
    x0, x1, y0, y1 = xs[i], xs[i + 1], ys[i], ys[i + 1]
    return round(y0 + (t - x0) * (y1 - y0) / (x1 - x0), 3)


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def snap(word, t, enabled=False):
    """Move a word time to the same word in the new transcript, if one is close. Off by default:
    the pilot's headline words were placed by hand around the spoken words, and the warp keeps that."""
    if not enabled:
        return t
    k = norm(word)
    best = None
    for w in W:
        if norm(w["w"]) == k and abs(w["s"] - t) < 0.8:
            if best is None or abs(w["s"] - t) < abs(best - t):
                best = w["s"]
    return round(best, 3) if best is not None else t


E["duration"] = round(new_end + tail, 2)
for s in E["shots"]:
    s["t0"], s["t1"] = warp(s["t0"]), warp(s["t1"])
for h in E["headlines"]:
    h["t0"], h["t1"] = warp(h["t0"]), warp(h["t1"])
    for line in h["lines"]:
        for w in line:
            w["t"] = snap(w["w"], warp(w["t"]))
for l in E.get("labels", []):
    l["t0"], l["t1"] = warp(l["t0"]), warp(l["t1"])
for c in E.get("counters", []):
    c["t0"], c["t1"] = warp(c["t0"]), warp(c["t1"])
    if "tick" in c:
        c["tick"] = [warp(t) for t in c["tick"]]
for L in E.get("lists", []):
    L["t0"], L["t1"] = warp(L["t0"]), warp(L["t1"])
    for it in L["items"]:
        it["t"] = warp(it["t"])
for s in E.get("subtitles", []):
    s["t0"], s["t1"] = warp(s["t0"]), warp(s["t1"])
E["glitches"] = [warp(t) for t in E.get("glitches", [])]
end = E["end"]
end["t0"], end["card_t"] = warp(end["t0"]), warp(end["card_t"])
for key in ("words", "slogan"):
    for w in end[key]:
        w["t"] = snap(w["w"], warp(w["t"]))

json.dump(E, open(out, "w"), indent=1)
print("duration", E["duration"], "(pass the old drop time through warp for audio.py)")
