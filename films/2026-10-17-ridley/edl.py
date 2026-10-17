"""Edit list for Harold Ridley, the intraocular lens (17 October 2026), built from the Kolff model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-17-ridley/edl.py vo.segments.json vo.words.json out_edl.json
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
SYN = {"november": {"november"}, "29": {"29", "29th"}, "aged": {"aged", "age"}, "6": {"6", "six"}, "10": {"10", "ten"}, "thomas": {"thomas", "thomas'"}, "ad": {"ad", "add"}, "one": {"1", "one"}, "17th": {"17th", "17"}, "accelerate": {"accelerate"}}


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
mid = round(S[11] + 1.6, 3)

edl = dict(duration=dur)
edl["shots"] = [
    shot("s01_canopy.png", "image", 0.0, S[1], look="reel16", z=[1.0, 1.1]),
    shot("s02_airfield.mp4", "video", S[1], S[2], look="reel16", src_in=0.3, speed=0.6),
    shot("s03_ward.png", "image", S[2], S[3], look="reel16", z=[1.0, 1.1]),
    shot("s04_splinters.png", "image", S[3], S[4], look="reel16", z=[1.04, 1.12]),
    shot("s05_glasses.png", "image", S[4], S[5], look="reel16", z=[1.0, 1.1]),
    shot("s06_theatre.png", "image", S[5], S[6], look="reel16", z=[1.0, 1.1]),
    shot("s07_surgeon.png", "image", S[6], S[7], look="reel16", z=[1.0, 1.1]),
    shot("s08_workshop.mp4", "video", S[7], S[8], look="reel16", src_in=0.5),
    shot("s09_hospital.png", "image", S[8], S[9], look="reel16", z=[1.0, 1.1]),
    shot("s10_lenses.png", "image", S[9], S[10], look="reel16", z=[1.04, 1.12]),
    shot("s11_room.png", "image", S[10], S[11], look="reel16", z=[1.0, 1.1]),
    shot("s12_waiting.png", "image", S[11], mid, look="snap", z=[1.04, 1.12]),
    shot("s14_garden.mp4", "video", mid, S[12], look="snap", src_in=0.5),
    shot("s13_reading.png", "image", S[12], S[13], look="snap", z=[1.04, 1.12]),
    shot("s15_stars.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("The", at(0, "The")), ("first", at(0, "first")), ("lens", at(0, "lens"))],
      [("came", at(0, "came")), ("from", at(0, "from")), ("a", at(0, "a")), ("fighter", at(0, "fighter")), ("plane.", at(0, "plane"))]),
    H(S[1] + 0.02, S[2] - pre, [("1940,", at(1, "1940"))], [("Battle", at(1, "Battle")), ("of", at(1, "of")), ("Britain.", at(1, "Britain"))]),
    H(S[2] + 0.02, S[3] - pre, [("Pilots", at(2, "Pilots")), ("came", at(2, "came")), ("in", at(2, "in"))],
      [("with", at(2, "with")), ("splinters.", at(2, "splinters"))]),
    H(S[3] + 0.02, S[4] - pre, [("The", at(3, "The")), ("plastic", at(3, "plastic"))], [("did", at(3, "did")), ("no", at(3, "no")), ("harm.", at(3, "harm"))]),
    H(S[4] + 0.02, S[5] - pre, [("Cataract", at(4, "Cataract")), ("surgery", at(4, "surgery"))],
      [("thick", at(4, "thick")), ("glasses.", at(4, "glasses"))]),
    H(S[5] + 0.02, S[6] - pre, [("A", at(5, "A")), ("student", at(5, "student")), ("asked,", at(5, "asked"))],
      [("put", at(5, "put")), ("one", at(5, "one")), ("back?", at(5, "back"))]),
    H(S[6] + 0.02, S[7] - pre, [("Harold", at(6, "Harold")), ("Ridley,", at(6, "Ridley"))], [("aged", at(6, "aged")), ("43.", at(6, "43"))]),
    H(S[7] + 0.02, S[8] - pre, [("A", at(7, "a")), ("lens", at(7, "lens")), ("cut", at(7, "cut"))],
      [("from", at(7, "from")), ("the", at(7, "the")), ("same", at(7, "same")), ("plastic.", at(7, "plastic"))]),
    H(S[8] + 0.02, S[9] - pre, [("November", at(8, "November")), ("29,", at(8, "29")), ("1949.", at(8, "1949"))],
      [("St", at(8, "St")), ("Thomas'", at(8, "Thomas")), ("Hospital.", at(8, "Hospital"))]),
    H(S[9] + 0.02, S[10] - pre, [("Too", at(9, "too")), ("thick.", at(9, "thick"))], [("He", at(9, "He")), ("thinned", at(9, "thinned")), ("it.", at(9, "it"))]),
    H(S[10] + 0.02, S[11] - pre, [("His", at(10, "His")), ("peers", at(10, "peers"))], [("called", at(10, "called")), ("it", at(10, "it")), ("reckless.", at(10, "reckless"))]),
    H(S[11] + 0.02, S[12] - pre, [("6", at(11, "6")), ("to", at(11, "to")), ("10", at(11, "10")), ("million", at(11, "million"))],
      [("cataract", at(11, "cataract")), ("operations", at(11, "operations")), ("a", at(11, "a")), ("year.", at(11, "year"))]),
    H(S[12] + 0.02, S[13] - pre, [("The", at(12, "The")), ("idea", at(12, "idea"))], [("is", at(12, "is")), ("still", at(12, "still")), ("his.", at(12, "his"))]),
]

edl["labels"] = [
    dict(t0=round(S[1] + 0.1, 3), t1=round(S[2] - pre, 3), text="Battle of Britain, 1940. Source: Ridley Eye Foundation"),
    dict(t0=round(S[6] + 0.1, 3), t1=round(S[7] - pre, 3), text="Born 10 July 1906, aged 43 in 1949. Source: Royal College of Surgeons"),
    dict(t0=round(S[8] + 0.1, 3), t1=round(S[9] - pre, 3), text="First operation 29 November 1949. Source: Royal College of Surgeons"),
    dict(t0=round(S[9] + 0.1, 3), t1=round(S[10] - pre, 3), text="First lens too thick, later recalculated. Source: Rayner, David J. Apple"),
    dict(t0=round(S[11] + 0.1, 3), t1=round(S[12] - pre, 3), text="Cataract operations a year, worldwide. Source: PubMed Central review"),
]

edl["counters"] = []
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "The first lens implant came from a fighter plane."),
    sp(1, "1940, Battle of Britain."),
    sp(2, "Pilots came in with splinters in their eyes."),
    sp(3, "The plastic did no harm."),
    sp(4, "Cataract surgery left patients in thick glasses."),
    sp(5, "A student asked, why not put one back?"),
    sp(6, "Harold Ridley, eye surgeon, aged 43."),
    sp(7, "He had a lens cut from the same plastic."),
    sp(8, "November 29, 1949, St Thomas' Hospital, London."),
    sp(9, "The first lens was too thick. He thinned it."),
    sp(10, "His peers called it reckless."),
    sp(11, "Today, 6 to 10 million cataract operations a year."),
    sp(12, "The idea is still his."),
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
