"""Edit list for Kary Mullis, the polymerase chain reaction (19 October 2026), built from the Kolff model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-19-mullis/edl.py vo.segments.json vo.words.json out_edl.json
"""
import json, os, re, sys

SRC = os.environ.get("SRC", "src")
CL = os.environ.get("CLIPS", "clips")
seg_f, words_f, out_f = sys.argv[1:4]
P = json.load(open(seg_f))["segments"]
W = json.load(open(words_f))
assert len(P) == 15, f"expected 15 phrases, got {len(P)}"
S = [p["out_s"] for p in P]
E = [p["out_e"] for p in P]
SYN = {"november": {"november"}, "29": {"29", "29th"}, "aged": {"aged", "age"}, "6": {"6", "six"}, "10": {"10", "ten"}, "thomas": {"thomas", "thomas'"}, "ad": {"ad", "add"}, "one": {"1", "one"}, "17th": {"17th", "17"}, "accelerate": {"accelerate"}, "heat-loving": {"loving", "heatloving"}, "1": {"1", "one"}, "thirty": {"thirty", "30"}, "billion": {"billion"}, "1985": {"1985"}}


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def words_in(k):
    lo, hi = S[k] - 0.4, E[k] + 0.2
    return [w for w in W if lo <= w["s"] <= hi]


def at(k, token, nth=0, frac=None):
    want = SYN.get(norm(token), {norm(token)})
    hits = [w["s"] for w in words_in(k) if norm(w["w"]) in want]
    if len(hits) > nth:
        return round(hits[nth], 3)
    f = 0.0 if frac is None else frac
    print(f"  note: '{token}' not found in phrase {k + 1}, placed at {f:.2f} of it")
    return round(S[k] + f * (E[k] - S[k]), 3)


def shot(name, kind, t0, t1, **kw):
    base = CL if kind == "video" else SRC
    return dict(src=f"{base}/{name}", kind=kind, t0=round(t0, 3), t1=round(t1, 3), **kw)


def H(t0, t1, *lines):
    return dict(t0=round(t0, 3), t1=round(t1, 3), lines=[[dict(w=w, t=round(t, 3)) for w, t in line] for line in lines])


def sub(t0, t1, text):
    return dict(t0=round(t0, 3), t1=round(t1, 3), text=text)


card_t = round(E[14] + 0.22, 3)
dur = round(card_t + 2.1, 2)
pre = 0.04
mid = round(at(12, "forensic") - 0.05, 3)
R = "reel16"

edl = dict(duration=dur)
edl["shots"] = [
    shot("m01_drive.png", "image", 0.0, S[1], look=R, z=[1.0, 1.1]),
    shot("m02_coast.mp4", "video", S[1], S[2], look=R, src_in=0.3),
    shot("m03_lab.png", "image", S[2], S[3], look=R, z=[1.0, 1.1]),
    shot("m04_heat.png", "image", S[3], S[4], look=R, z=[1.04, 1.12]),
    shot("m05_cool.png", "image", S[4], S[5], look=R, z=[1.0, 1.1]),
    shot("m06_enzyme.png", "image", S[5], S[6], look=R, z=[1.0, 1.1]),
    shot("m07_double.png", "image", S[6], S[7], look=R, z=[1.0, 1.1]),
    shot("m08_gel.png", "image", S[7], S[8], look=R, z=[1.04, 1.12]),
    shot("m09_baths.mp4", "video", S[8], S[9], look=R, src_in=0.3),
    shot("m10_spring.mp4", "video", S[9], S[10], look=R, src_in=0.3),
    shot("m11_journal.png", "image", S[10], S[11], look=R, z=[1.0, 1.1]),
    shot("m12_stockholm.png", "image", S[11], S[12], look=R, z=[1.0, 1.1]),
    shot("m13_swab.png", "image", S[12], mid, look="snap", z=[1.04, 1.12]),
    shot("m14_forensic.mp4", "video", mid, S[13], look="snap", src_in=0.3),
    shot("m15_stars.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("Copying", at(0, "Copying")), ("DNA", at(0, "DNA")), ("began", at(0, "began"))],
      [("on", at(0, "on")), ("a", at(0, "a")), ("night", at(0, "night")), ("drive.", at(0, "drive"))]),
    H(S[1] + 0.02, S[2] - pre, [("California,", at(1, "California"))], [("1983.", at(1, "1983"))]),
    H(S[2] + 0.02, S[3] - pre, [("Kary", at(2, "Kary")), ("Mullis,", at(2, "Mullis"))],
      [("a", at(2, "a")), ("chemist", at(2, "chemist")), ("at", at(2, "at")), ("Cetus", at(2, "Cetus"))]),
    H(S[3] + 0.02, S[4] - pre, [("Heat", at(3, "Heat")), ("splits", at(3, "splits"))], [("the", at(3, "the")), ("strands.", at(3, "strands"))]),
    H(S[4] + 0.02, S[5] - pre, [("Cool", at(4, "Cool")), ("it,", at(4, "it"))], [("starters", at(4, "starters")), ("attach.", at(4, "attach"))]),
    H(S[5] + 0.02, S[6] - pre, [("An", at(5, "An")), ("enzyme", at(5, "enzyme"))], [("builds", at(5, "builds")), ("halves.", at(5, "halves"))]),
    H(S[6] + 0.02, S[7] - pre, [("Repeat,", at(6, "Repeat"))], [("copies", at(6, "copies")), ("double.", at(6, "double"))]),
    H(S[7] + 0.02, S[8] - pre, [("Thirty", at(7, "Thirty")), ("rounds:", at(7, "rounds"))], [("over", at(7, "over")), ("1", at(7, "billion")), ("billion", at(7, "billion")), ("copies.", at(7, "copies"))]),
    H(S[8] + 0.02, S[9] - pre, [("Heat", at(8, "heat")), ("killed", at(8, "killed"))], [("the", at(8, "the")), ("enzyme.", at(8, "enzyme"))]),
    H(S[9] + 0.02, S[10] - pre, [("A", at(9, "A")), ("heat-loving", at(9, "heat")), ("bacterium", at(9, "bacterium's"))], [("machines", at(9, "machines")), ("ran", at(9, "ran")), ("it.", at(9, "alone"))]),
    H(S[10] + 0.02, S[11] - pre, [("1985,", at(10, "1985"))], [("published.", at(10, "published"))]),
    H(S[11] + 0.02, S[12] - pre, [("1993,", at(11, "1993"))], [("Nobel", at(11, "Nobel")), ("Prize.", at(11, "Prize"))]),
    H(S[12] + 0.02, S[13] - pre, [("Every", at(12, "Every")), ("virus", at(12, "virus")), ("test", at(12, "test"))],
      [("and", at(12, "and")), ("DNA", at(12, "DNA")), ("match.", at(12, "match"))]),
]

edl["labels"] = [
    dict(t0=round(S[1] + 0.1, 3), t1=round(S[2] - pre, 3), text="Cetus Corporation, California, 1983. Source: Embryo Project, Arizona State University"),
    dict(t0=round(S[6] + 0.1, 3), t1=round(S[7] - pre, 3), text="Each round doubles the DNA. Source: Embryo Project"),
    dict(t0=round(S[7] + 0.1, 3), t1=round(S[8] - pre, 3), text="2 to the power 30 = 1,073,741,824. Source: Wikipedia"),
    dict(t0=round(S[9] + 0.1, 3), t1=round(S[10] - pre, 3), text="Heat-tolerant enzyme from Thermus aquaticus. Source: Embryo Project"),
    dict(t0=round(S[11] + 0.1, 3), t1=round(S[12] - pre, 3), text="Nobel Prize in Chemistry 1993, shared with Michael Smith. Source: nobelprize.org"),
]

edl["counters"] = []
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "Copying DNA began on a night drive."),
    sp(1, "California, 1983."),
    sp(2, "Kary Mullis, a chemist at Cetus, saw how to copy one piece of DNA."),
    sp(3, "Heat splits the two strands."),
    sp(4, "Cool it, and short starters attach."),
    sp(5, "An enzyme builds the missing halves."),
    sp(6, "Repeat, and the copies double."),
    sp(7, "Thirty rounds make over 1 billion copies."),
    sp(8, "Early on, the heat killed the enzyme, so it was added fresh each round."),
    sp(9, "A heat-loving bacterium's enzyme survived, and machines ran the rounds alone."),
    sp(10, "1985, the method was published."),
    sp(11, "1993, Mullis shared the Nobel Prize in Chemistry."),
    sp(12, "Every virus test and forensic DNA match starts with it."),
]
subs = edl["subtitles"]
for a, b in zip(subs, subs[1:]):
    a["t1"] = round(min(a["t1"], b["t0"] - 0.02), 3)

edl["glitches"] = [round(S[10], 3), round(S[13], 3)]
edl["end"] = dict(t0=round(S[13], 3),
                  words=[dict(w="Ad", t=at(13, "Ad")), dict(w="Astra.", t=at(13, "Astra", frac=0.5))],
                  slogan=[dict(w="Fucking", t=at(14, "Fucking")), dict(w="accelerate.", t=at(14, "accelerate", frac=0.45))],
                  card_t=card_t, emblem=os.path.join(os.environ.get("KIT", "kit"), "emblem.jpg"), url_line="Apply at joinadastra.com")
json.dump(edl, open(out_f, "w"), indent=1, ensure_ascii=False)
print("duration", dur, "glitch", round(S[10], 3), "card", card_t)
for s in edl["shots"]:
    print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['src'].split('/')[-1]}")
