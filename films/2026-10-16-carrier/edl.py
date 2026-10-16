"""Edit list for Willis Carrier, air conditioning (16 October 2026), built from the Kolff model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-16-carrier/edl.py vo.segments.json vo.words.json out_edl.json
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
SYN = {"aged": {"aged", "age"}, "ad": {"ad", "add"}, "one": {"1", "one"}, "17th": {"17th", "17"}, "accelerate": {"accelerate"}}


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


# the 4.5 second wait between past and present is not used; the modern run starts on the "Today" phrase
card_t = round(E[14] + 0.22, 3)
dur = round(card_t + 2.1, 2)
pre = 0.04
mid = round(S[11] + 1.5, 3)
mid2 = round(S[12] + 0.75, 3)

edl = dict(duration=dur)
edl["shots"] = [
    shot("s01_press.png", "image", 0.0, S[1], look="early", focus=[0.4, 0.5]),
    shot("s02_brooklyn.mp4", "video", S[1], S[2], look="early", src_in=0.0, speed=0.6),
    shot("s03_paper.png", "image", S[2], S[3], look="early", z=[1.0, 1.1]),
    shot("s04_deadline.mp4", "video", S[3], S[4], look="early", src_in=0.3),
    shot("s05_engineer.png", "image", S[4], S[5], look="early", z=[1.0, 1.1]),
    shot("s06_target.mp4", "video", S[5], S[6], look="early", src_in=0.5),
    shot("s07_coils.mp4", "video", S[6], S[7], look="early", src_in=0.5),
    shot("s08_room.mp4", "video", S[7], S[8], look="early", src_in=0.3, speed=0.8),
    shot("s09_drawings.png", "image", S[8], S[9], look="early", focus=[0.55, 0.55], z=[1.04, 1.14]),
    shot("s10_patent.png", "image", S[9], S[10], look="early", focus=[0.6, 0.5]),
    shot("s11_factory.png", "image", S[10], S[11], look="early", z=[1.0, 1.1]),
    shot("s12_homes.png", "image", S[11], mid, look="snap", z=[1.04, 1.12], focus=[0.5, 0.55]),
    shot("s13_unit.png", "image", mid, S[12], look="snap", focus=[0.5, 0.5], z=[1.0, 1.1]),
    shot("s14_room.png", "image", S[12], mid2, look="snap", z=[1.04, 1.12], focus=[0.5, 0.4]),
    shot("s15_fins.mp4", "video", mid2, S[13], look="snap", src_in=0.5),
    shot("s16_stars.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("Air", at(0, "Air")), ("conditioning", at(0, "conditioning"))],
      [("a", at(0, "a", 1)), ("fix", at(0, "fix")), ("for", at(0, "for")), ("a", at(0, "a", 1)), ("press.", at(0, "press"))]),
    H(S[1] + 0.02, S[2] - pre, [("1902.", at(1, "1902"))], [("Brooklyn.", at(1, "Brooklyn"))]),
    H(S[2] + 0.02, S[3] - pre, [("Humid", at(2, "Humid")), ("air", at(2, "air"))],
      [("warped", at(2, "warped")), ("the", at(2, "the")), ("paper.", at(2, "paper"))]),
    H(S[3] + 0.02, S[4] - pre, [("Magazine", at(3, "magazine")), ("deadline", at(3, "deadline"))],
      [("at", at(3, "at")), ("risk.", at(3, "risk"))]),
    H(S[4] + 0.02, S[5] - pre, [("Willis", at(4, "Willis")), ("Carrier,", at(4, "Carrier"))],
      [("aged", at(4, "aged")), ("25.", at(4, "25"))]),
    H(S[5] + 0.02, S[6] - pre, [("One", at(5, "one")), ("target:", at(5, "target"))], [("humidity.", at(5, "humidity"))]),
    H(S[6] + 0.02, S[7] - pre, [("Chilled", at(6, "chilled")), ("coils", at(6, "coils"))],
      [("and", at(6, "and")), ("fans.", at(6, "fans"))]),
    H(S[7] + 0.02, S[8] - pre, [("55", at(7, "55")), ("percent", at(7, "percent")), ("humidity", at(7, "humidity"))],
      [("all", at(7, "All")), ("year.", at(7, "year"))]),
    H(S[8] + 0.02, S[9] - pre, [("July", at(8, "July")), ("17,", at(8, "17th"))], [("1902.", at(8, "1902"))]),
    H(S[9] + 0.02, S[10] - pre, [("Patent", at(9, "patent")), ("granted,", at(9, "granted"))], [("1906.", at(9, "1906"))]),
    H(S[10] + 0.02, S[11] - pre, [("By", at(10, "By")), ("1915,", at(10, "1915"))],
      [("his", at(10, "his")), ("own", at(10, "own")), ("company.", at(10, "company"))]),
    H(S[12] + 0.02, S[13] - pre, [("The", at(12, "the")), ("method", at(12, "method"))],
      [("is", at(12, "is")), ("still", at(12, "still")), ("his.", at(12, "his"))]),
]

edl["labels"] = [
    dict(t0=round(at(1, "1902") - 0.1, 3), t1=round(S[2] - pre, 3), text="Brooklyn, New York, 1902."),
    dict(t0=round(S[7] + 0.1, 3), t1=round(S[8] - pre, 3),
         text="Humidity held at 55 percent, 21 degrees in winter, 27 in summer. Source: Carrier Corporation"),
    dict(t0=round(S[8] + 0.1, 3), t1=round(S[9] - pre, 3), text="17 July 1902. Source: Hagley Museum and Library"),
    dict(t0=round(S[9] + 0.1, 3), t1=round(S[10] - pre, 3), text="US patent granted, 1906. Source: Hagley Museum and Library"),
]

edl["counters"] = [
    dict(t0=round(S[11], 3), t1=round(S[12] - pre, 3), a=0, b=88, fmt="int", prefix="", unit="%",
         tick=[round(at(11, "88") - 0.1, 3), round(S[12] - 0.45, 3)],
         src="United States homes with air conditioning, today. Source: Energy Information Administration"),
]
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "Air conditioning started as a fix for a printing press."),
    sp(1, "1902, Brooklyn."),
    sp(2, "Humid air warped the paper, and the colours never lined up."),
    sp(3, "A magazine deadline was at risk."),
    sp(4, "Willis Carrier, engineer, aged 25."),
    sp(5, "He set one target: humidity."),
    sp(6, "Chilled coils and fans ran through the plant."),
    sp(7, "All year, 55 percent humidity, 21 degrees in winter and 27 in summer."),
    sp(8, "17 July 1902, his drawings."),
    sp(9, "Patent granted, 1906."),
    sp(10, "By 1915 he had his own company."),
    sp(11, "Today, 88 percent of United States homes have it."),
    sp(12, "The method is still his."),
]
subs = edl["subtitles"]
for a, b in zip(subs, subs[1:]):
    a["t1"] = round(min(a["t1"], b["t0"] - 0.02), 3)

edl["glitches"] = [round(S[11], 3), round(S[13], 3)]
edl["end"] = dict(t0=round(S[13], 3),
                  words=[dict(w="Ad", t=at(13, "Ad")), dict(w="Astra.", t=at(13, "Astra", frac=0.5))],
                  slogan=[dict(w="Fucking", t=at(14, "Fucking")), dict(w="accelerate.", t=at(14, "accelerate", frac=0.45))],
                  card_t=card_t, emblem=os.path.join(os.environ.get("KIT", "kit"), "emblem.jpg"), url_line="Apply at joinadastra.com")
json.dump(edl, open(out_f, "w"), indent=1, ensure_ascii=False)
print("duration", dur, "drop", round(S[11], 3), "card", card_t)
for s in edl["shots"]:
    print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['src'].split('/')[-1]}")
