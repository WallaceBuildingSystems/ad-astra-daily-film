"""Edit list for Charles Parsons, the steam turbine (21 October 2026), built from the Otis model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-21-parsons/edl.py vo.segments.json vo.words.json out_edl.json
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
SYN = {"eighteen": {"18"}, "seven": {"7"}, "ninety": {"90"}, "thirtyfour": {"34"}, "twentyseven": {"27"}, "1884": {"1884"}, "add": {"add", "ad"}, "five": {"5", "five"}, "ad": {"ad", "add"}, "accelerate": {"accelerate"}, "1965": {"1965"}, "fibre": {"fiber", "fibre"}, "tyres": {"tires", "tyres"}, "armour": {"armor", "armour"}, "3000": {"3", "000"}, "ninety": {"90"}}


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def words_in(k):
    lo, hi = S[k] - 0.5, E[k] + 0.2
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
A = "archival"

edl = dict(duration=dur)
edl["shots"] = [
    shot("p01.png", "image", 0.0, S[1], look="modern", z=[1.0, 1.1]),
    shot("p02.png", "image", S[1], S[2], look=A, z=[1.0, 1.1]),
    shot("p03.png", "image", S[2], S[3], look=A, z=[1.0, 1.1]),
    shot("p04_shop.mp4", "video", S[3], S[4], look=A, src_in=0.3),
    shot("p05.png", "image", S[4], S[5], look=A, z=[1.04, 1.12]),
    shot("p06.png", "image", S[5], S[6], look=A, z=[1.0, 1.1]),
    shot("p07.png", "image", S[6], S[7], look=A, z=[1.04, 1.12]),
    shot("p08_launch.mp4", "video", S[7], S[8], look=A, src_in=0.3),
    shot("p09.png", "image", S[8], S[9], look=A, z=[1.0, 1.1]),
    shot("p10.png", "image", S[9], S[10], look=A, z=[1.04, 1.12]),
    shot("p11_fast.mp4", "video", S[10], S[11], look=A, src_in=0.0, speed=0.8),
    shot("p12.png", "image", S[11], S[12], look=A, z=[1.0, 1.1]),
    shot("p13.png", "image", S[12], S[13], look="snap", z=[1.0, 1.1]),
    shot("p14_sky.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("Most", at(0, "Most")), ("of", at(0, "of")), ("the", at(0, "the")), ("world's", at(0, "worlds")), ("electricity.", at(0, "electricity"))], [("One", at(0, "invented")), ("machine,", at(0, "machine")), ("1884.", at(0, "1884"))]),
    H(S[1] + 0.02, S[2] - pre, [("Newcastle,", at(1, "Newcastle"))], [("1884.", at(1, "1884"))]),
    H(S[2] + 0.02, S[3] - pre, [("Charles", at(2, "Charles")), ("Parsons.", at(2, "Parsons"))], [("An", at(2, "an")), ("earl's", at(2, "earls")), ("son.", at(2, "son"))]),
    H(S[3] + 0.02, S[4] - pre, [("Rival", at(3, "Rival")), ("turbines", at(3, "turbines"))], [("had", at(3, "limited")), ("limits.", at(3, "forces"))]),
    H(S[4] + 0.02, S[5] - pre, [("Split", at(4, "split")), ("the", at(4, "the")), ("steam's", at(4, "steams")), ("fall.", at(4, "fall"))]),
    H(S[5] + 0.02, S[6] - pre, [("18,000", at(5, "18"))], [("turns", at(5, "turned")), ("a", at(5, "a")), ("minute.", at(5, "minute"))]),
    H(S[6] + 0.02, S[7] - pre, [("7.5", at(6, "7")), ("kilowatts.", at(6, "kilowatts"))], [("1.6%", at(6, "1")), ("efficient.", at(6, "efficient"))]),
    H(S[7] + 0.02, S[8] - pre, [("1894.", at(7, "1894"))], [("A", at(7, "a")), ("boat", at(7, "boat")), ("to", at(7, "to")), ("prove", at(7, "prove")), ("it.", at(7, "it"))]),
    H(S[8] + 0.02, S[9] - pre, [("One", at(8, "one")), ("propeller.", at(8, "propeller"))], [("Disappointing.", at(8, "disappointing"))]),
    H(S[9] + 0.02, S[10] - pre, [("3", at(9, "three")), ("shafts.", at(9, "shafts"))], [("9", at(9, "nine")), ("propellers.", at(9, "propellers"))]),
    H(S[10] + 0.02, S[11] - pre, [("34", at(10, "34")), ("knots", at(10, "knots"))], [("against", at(10, "against")), ("27.", at(10, "27"))]),
    H(S[11] + 0.02, S[12] - pre, [("1905.", at(11, "1905"))], [("Admiralty", at(11, "Admiralty")), ("chooses", at(11, "chose")), ("turbines.", at(11, "turbines"))]),
    H(S[12] + 0.02, S[13] - pre, [("Over", at(12, "over")), ("90%", at(12, "90"))], [("of", at(12, "of")), ("the", at(12, "the")), ("world's", at(12, "worlds")), ("electricity.", at(12, "electricity"))]),
]

edl["labels"] = [
    dict(t0=round(S[0] + 0.1, 3), t1=round(S[1] - pre, 3), text="Over 90% of world electricity, as of today. Source: Historic UK"),
    dict(t0=round(S[2] + 0.1, 3), t1=round(S[3] - pre, 3), text="Youngest son of the 3rd Earl of Rosse. Source: Wikipedia"),
    dict(t0=round(S[5] + 0.1, 3), t1=round(S[6] - pre, 3), text="First turbine, 1884: 18,000 rpm. Source: Wikipedia"),
    dict(t0=round(S[6] + 0.1, 3), t1=round(S[7] - pre, 3), text="7.5 kW, 1.6% efficient. Source: Wikipedia"),
    dict(t0=round(S[7] + 0.1, 3), t1=round(S[8] - pre, 3), text="Turbinia launched 2 August 1894. Source: Wikipedia"),
    dict(t0=round(S[9] + 0.1, 3), t1=round(S[10] - pre, 3), text="3 shafts, 9 propellers. Source: Wikipedia"),
    dict(t0=round(S[10] + 0.1, 3), t1=round(S[11] - pre, 3), text="Spithead, 26 June 1897. Source: Wikipedia, Encyclopaedia Britannica"),
    dict(t0=round(S[11] + 0.1, 3), t1=round(S[12] - pre, 3), text="Admiralty decision, 1905. Source: Wikipedia"),
]

edl["counters"] = []
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "Most of the world's electricity comes from a machine invented in 1884."),
    sp(1, "Newcastle, 1884."),
    sp(2, "Charles Parsons, an earl's son, had trained as an engineer."),
    sp(3, "Rival turbines were limited by the forces on their spinning parts."),
    sp(4, "His idea was to split the steam's fall into many small steps."),
    sp(5, "His first turbine turned 18,000 times a minute."),
    sp(6, "It made 7.5 kilowatts, and was 1.6 per cent efficient."),
    sp(7, "In 1894 he built a boat to prove it."),
    sp(8, "The first trials, with one propeller, were disappointing."),
    sp(9, "So he fitted three shafts and nine propellers."),
    sp(10, "At Spithead in 1897 it reached 34 knots, against 27 for the Navy's fastest."),
    sp(11, "In 1905 the Admiralty chose turbines for all future ships."),
    sp(12, "Today, over 90 per cent of the world's electricity comes from steam turbines."),
]
subs = edl["subtitles"]
for a, b in zip(subs, subs[1:]):
    a["t1"] = round(min(a["t1"], b["t0"] - 0.02), 3)

edl["glitches"] = [round(S[9], 3), round(S[13], 3)]
edl["end"] = dict(t0=round(S[13], 3),
                  words=[dict(w="Ad", t=at(13, "Ad")), dict(w="Astra.", t=at(13, "Astra", frac=0.5))],
                  slogan=[dict(w="Fucking", t=at(14, "Fucking")), dict(w="accelerate.", t=at(14, "accelerate", frac=0.45))],
                  card_t=card_t, emblem=os.path.join(os.environ.get("KIT", "kit"), "emblem.jpg"), url_line="Apply at joinadastra.com")
json.dump(edl, open(out_f, "w"), indent=1, ensure_ascii=False)
print("duration", dur, "glitch", round(S[9], 3), "card", card_t)
for s in edl["shots"]:
    print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['src'].split('/')[-1]}")
