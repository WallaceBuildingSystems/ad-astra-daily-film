"""Edit list for Clarence Birdseye, quick freezing (18 October 2026), built from the Kolff model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-18-birdseye/edl.py vo.segments.json vo.words.json out_edl.json
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
mid = round(at(12, "to") - 0.05, 3)

edl = dict(duration=dur)
edl["shots"] = [
    shot("s01_ice.png", "image", 0.0, S[1], look="reel16", z=[1.0, 1.1]),
    shot("s02_labrador.mp4", "video", S[1], S[2], look="reel16", src_in=0.3),
    shot("s03_fishermen.png", "image", S[2], S[3], look="reel16", z=[1.0, 1.1]),
    shot("s04_catch.png", "image", S[3], S[4], look="reel16", z=[1.04, 1.12]),
    shot("s05_pan.png", "image", S[4], S[5], look="reel16", z=[1.0, 1.1]),
    shot("s06_mush.png", "image", S[5], S[6], look="reel16", z=[1.0, 1.1]),
    shot("s07_crystals.png", "image", S[6], S[7], look="reel16", z=[1.0, 1.1]),
    shot("s08_wind.mp4", "video", S[7], S[8], look="reel16", src_in=0.3),
    shot("s09_freezer.mp4", "video", S[8], S[9], look="reel16", src_in=0.3),
    shot("s10_ledger.png", "image", S[9], S[10], look="reel16", z=[1.04, 1.12]),
    shot("s11_workbench.png", "image", S[10], S[11], look="reel16", z=[1.0, 1.1]),
    shot("s12_store.png", "image", S[11], S[12], look="reel16", z=[1.0, 1.1]),
    shot("s13_kitchen.png", "image", S[12], mid, look="snap", z=[1.04, 1.12]),
    shot("s14_peas.png", "image", mid, S[13], look="snap", z=[1.0, 1.1]),
    shot("s15_aurora.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("Frozen", at(0, "Frozen")), ("food", at(0, "food")), ("began", at(0, "began"))],
      [("with", at(0, "with")), ("a", at(0, "a")), ("fish", at(0, "fish")), ("on", at(0, "on")), ("the", at(0, "the")), ("ice.", at(0, "ice"))]),
    H(S[1] + 0.02, S[2] - pre, [("Labrador,", at(1, "Labrador"))], [("1912.", at(1, "1912"))]),
    H(S[2] + 0.02, S[3] - pre, [("Clarence", at(2, "Clarence")), ("Birdseye,", at(2, "Birdseye"))],
      [("watched", at(2, "watched")), ("Inuit", at(2, "Inuit")), ("fishermen", at(2, "fishermen"))]),
    H(S[3] + 0.02, S[4] - pre, [("It", at(3, "It")), ("froze", at(3, "froze"))], [("at", at(3, "at")), ("once.", at(3, "once"))]),
    H(S[4] + 0.02, S[5] - pre, [("Cooked", at(4, "Cooked")), ("later,", at(4, "later"))], [("it", at(4, "it")), ("tasted", at(4, "tasted")), ("fresh.", at(4, "fresh"))]),
    H(S[5] + 0.02, S[6] - pre, [("Shop", at(5, "shops")), ("frozen", at(5, "Frozen")), ("food", at(5, "food"))], [("tasted", at(5, "tasted")), ("like", at(5, "like")), ("mush.", at(5, "mush"))]),
    H(S[6] + 0.02, S[7] - pre, [("Slow", at(6, "slowly")), ("freezing", at(6, "froze"))], [("large", at(6, "large")), ("ice", at(6, "ice")), ("crystals.", at(6, "crystals"))]),
    H(S[7] + 0.02, S[8] - pre, [("Birdseye", at(7, "Birdseye")), ("copied", at(7, "copied"))], [("the", at(7, "the")), ("cold.", at(7, "cold"))]),
    H(S[8] + 0.02, S[9] - pre, [("A", at(8, "a")), ("freezer", at(8, "freezer"))], [("chilled", at(8, "chilled")), ("belts.", at(8, "belts"))]),
    H(S[9] + 0.02, S[10] - pre, [("Out", at(9, "out")), ("of", at(9, "of")), ("money.", at(9, "money"))]),
    H(S[10] + 0.02, S[11] - pre, [("He", at(10, "He")), ("kept", at(10, "kept"))], [("going.", at(10, "going"))]),
    H(S[11] + 0.02, S[12] - pre, [("1930,", at(11, "1930")), ("Springfield", at(11, "Springfield"))],
      [("frozen", at(11, "frozen")), ("food", at(11, "food")), ("in", at(11, "the")), ("shops.", at(11, "shops"))]),
    H(S[12] + 0.02, S[13] - pre, [("Refrigerators:", at(12, "refrigerators"))],
      [("under", at(12, "under")), ("10", at(12, "10")), ("percent", round(at(12, "10") + 0.18, 3)), ("to", at(12, "to")), ("over", at(12, "over")), ("50.", at(12, "50"))]),
]

edl["labels"] = [
    dict(t0=round(S[1] + 0.1, 3), t1=round(S[2] - pre, 3), text="Labrador, 1912. Source: History.com"),
    dict(t0=round(S[2] + 0.1, 3), t1=round(S[3] - pre, 3), text="Inuit ice fishing, catch frozen at once. Source: History.com"),
    dict(t0=round(S[6] + 0.1, 3), t1=round(S[7] - pre, 3), text="Slow freezing forms large ice crystals. Source: History.com"),
    dict(t0=round(S[8] + 0.1, 3), t1=round(S[9] - pre, 3), text="United States Patent 1,773,079, method of preparing food products. Source: Wikipedia"),
    dict(t0=round(S[11] + 0.1, 3), t1=round(S[12] - pre, 3), text="First retail frozen foods, Springfield, 1930. Source: National Inventors Hall of Fame"),
    dict(t0=round(S[12] + 0.1, 3), t1=round(S[13] - pre, 3), text="Home refrigerators, under 10 to over 50 percent. Source: History.com"),
]

edl["counters"] = []
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "Frozen food began with a fish on the ice."),
    sp(1, "Labrador, 1912."),
    sp(2, "Clarence Birdseye, a fur trader, watched Inuit fishermen leave their catch on the ice."),
    sp(3, "It froze at once."),
    sp(4, "Cooked later, it tasted fresh."),
    sp(5, "Frozen food in shops tasted like mush."),
    sp(6, "It froze slowly, in large ice crystals."),
    sp(7, "Birdseye copied the cold."),
    sp(8, "He built a freezer that pressed food between chilled belts."),
    sp(9, "His first company ran out of money."),
    sp(10, "He kept going."),
    sp(11, "1930, Springfield, Massachusetts, his frozen food reached the shops."),
    sp(12, "Home refrigerators rose from under 10 percent to over 50."),
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
