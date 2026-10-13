"""Example edit list: the Hall pilot, story cut (13 October 2026), the model for each day's list.
Copy it, change the shots, words, counters, labels, lists and subtitles for the day's script, keep the method.

Edit list for the Hall pilot, third cut (13 October 2026): James asked for a more compelling story of what
Hall did to make aluminium cheap and abundant, in metric, read by Wallace Jax Meridian.

usage: python3 edl_hall_v3.py vo.segments.json vo.words.json out_edl.json

Every time comes from the voice: shots cut on phrase starts, headline words land on the spoken words.
"""
import json, re, sys

import os
SRC = os.environ.get("SRC", "src")  # the folder of downloaded pictures and clips
seg_f, words_f, out_f = sys.argv[1:4]
P = json.load(open(seg_f))["segments"]
W = json.load(open(words_f))
assert len(P) == 18, f"expected 18 phrases, got {len(P)}"
S = [p["out_s"] for p in P]
E = [p["out_e"] for p in P]

SYN = {"four": {"4", "four"}, "ad": {"ad", "add"}, "aluminium": {"aluminium", "aluminum"},
       "twentytwo": {"22", "twentytwo"}}


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def words_in(k):
    lo, hi = S[k] - 0.2, E[k] + 0.2
    return [w for w in W if lo <= w["s"] <= hi]


def at(k, token, nth=0, frac=None):
    """Start time of the spoken token inside phrase k (nth match), else a fraction of the phrase."""
    want = SYN.get(norm(token), {norm(token)})
    hits = [w["s"] for w in words_in(k) if norm(w["w"]) in want]
    if len(hits) > nth:
        return round(hits[nth], 3)
    f = 0.0 if frac is None else frac
    print(f"  note: '{token}' not found in phrase {k + 1}, placed at {f:.2f} of it")
    return round(S[k] + f * (E[k] - S[k]), 3)


def end_of(k, token, nth=0):
    want = SYN.get(norm(token), {norm(token)})
    hits = [w["e"] for w in words_in(k) if norm(w["w"]) in want]
    return round(hits[nth], 3) if len(hits) > nth else E[k]


def shot(name, kind, t0, t1, **kw):
    return dict(src=f"{SRC}/{name}", kind=kind, t0=round(t0, 3), t1=round(t1, 3), **kw)


def H(t0, t1, *lines):
    return dict(t0=round(t0, 3), t1=round(t1, 3), lines=[[dict(w=w, t=t) for w, t in line] for line in lines])


def sub(t0, t1, text):
    return dict(t0=round(t0, 3), t1=round(t1, 3), text=text)


card_t = round(E[17] + 0.22, 3)
dur = round(card_t + 2.1, 2)
pre = 0.04  # leave a hair before the next cut

edl = dict(duration=dur)
edl["shots"] = [
    shot("s01_banquet.mp4", "video", 0.0, S[1], look="archival", focus=[0.5, 0.60], speed=0.7),
    shot("s02_silver.png", "image", S[1], S[2], look="archival", focus=[0.5, 0.55]),
    shot("s03_scale.png", "image", S[2], S[3], look="archival"),
    shot("s05_exhibit.png", "image", S[3], S[4], look="archival"),
    shot("s06_woodshed.mp4", "video", S[4], S[5], look="archival", focus=[0.5, 0.55]),
    shot("s04_sodium.mp4", "video", S[5], S[6], look="archival"),
    shot("s07_bench.png", "image", S[6], S[7], look="archival"),
    shot("s08_electrolysis.mp4", "video", S[7], S[8], look="archival", src_in=0.6, z=[1.0, 1.03]),
    shot("s09_failed.png", "image", S[8], S[9], look="archival"),
    shot("s10_cryolite.mp4", "video", S[9], S[10], look="archival", speed=0.68),
    shot("s11_beads.mp4", "video", S[10], S[12], look="archival", src_in=0.3),
    shot("s12_smelter1900.mp4", "video", S[12], S[13], look="early", speed=0.72),
    shot("s13_potline.mp4", "video", S[13], S[14], look="modern", z=[1.0, 1.03]),
    shot("s14_cans.mp4", "video", S[14], S[15], look="modern"),
    shot("s15_foil.mp4", "video", S[15], S[16], look="modern"),
    shot("s16_sky.mp4", "video", S[16], card_t, look="film"),
]

priced = at(2, "priced", frac=0.55)
edl["headlines"] = [
    H(0.05, S[1] - pre, [("Napoleon's", at(0, "Napoleon")), ("best", at(0, "best")), ("guests:", at(0, "guests"))],
      [("aluminium.", at(0, "aluminium"))]),
    H(S[1] + 0.02, S[2] - pre, [("The", at(1, "The")), ("rest", at(1, "rest")), ("got", at(1, "got")), ("silver.", at(1, "silver"))]),
    H(S[2] + 0.02, priced - 0.05, [("Earth's", at(2, "Earth's")), ("most", at(2, "most")), ("common", at(2, "common")),
                                   ("metal.", at(2, "metal"))]),
    H(at(3, "make") - 0.1, S[4] - pre, [("Make", at(3, "make")), ("it", at(3, "it")), ("cheap,", at(3, "cheap"))],
      [("make", at(3, "make", 1, 0.7)), ("a", at(3, "a", 1, 0.8)), ("fortune.", at(3, "fortune", frac=0.85))]),
    H(S[4] + 0.02, S[5] - pre, [("Charles", at(4, "His")), ("Martin", at(4, "student")), ("Hall,", at(4, "student") + 0.25),
                                ("22.", at(4, "22", frac=0.35))]),
    H(S[5] + 0.02, S[6] - pre, [("Chemists", at(5, "Chemists")), ("used", at(5, "used")), ("sodium.", at(5, "sodium"))]),
    H(S[6] + 0.02, S[7] - pre, [("He", at(6, "He")), ("used", at(6, "used")), ("electricity.", at(6, "electricity"))]),
    H(S[7] + 0.02, at(7, "let", frac=0.4) - 0.05, [("Dissolve", at(7, "Dissolve")), ("the", at(7, "the")), ("ore.", at(7, "ore"))]),
    H(at(7, "let", frac=0.4), S[8] - pre, [("Let", at(7, "let", frac=0.4)), ("current", at(7, "current", frac=0.5))],
      [("pull", at(7, "pull", frac=0.65)), ("the", at(7, "the", 1, 0.75)), ("metal", at(7, "metal", frac=0.8)),
       ("out.", at(7, "out", frac=0.9))]),
    H(S[9] + 0.02, S[10] - pre, [("Then,", at(9, "Then")), ("molten", at(9, "molten")), ("cryolite.", at(9, "cryolite", frac=0.6))]),
    H(S[10] + 0.02, S[11] - pre, [("February", at(10, "February")), ("1886.", at(10, "1886", frac=0.5))]),
    H(S[11] + 0.02, S[12] - pre, [("Beads", at(11, "Beads")), ("of", at(11, "of")), ("aluminium.", at(11, "aluminium"))]),
    H(S[15] + 0.02, S[16] - pre, [("Napoleon's", at(15, "Napoleon's")), ("treasure.", at(15, "treasure"))],
      [("Your", at(15, "your", frac=0.6)), ("leftovers.", at(15, "leftovers", frac=0.75))]),
]

edl["labels"] = [
    dict(t0=round(at(3, "make") - 0.1, 3), t1=round(S[4] - pre, 3), text="Professor Frank Jewett, Oberlin College."),
    dict(t0=round(at(4, "woodshed", frac=0.7) - 0.2, 3), t1=round(S[5] - pre, 3), text="A woodshed behind the family home. Oberlin, Ohio."),
    dict(t0=round(at(9, "cryolite", frac=0.6), 3), t1=round(S[10] - pre, 3),
         text="Cryolite melts at 1,000 degrees Celsius. Source: Science History Institute"),
    dict(t0=round(S[10] + 0.3, 3), t1=round(S[11] - pre, 3), text="23 February 1886. The first metal."),
]

edl["counters"] = [
    dict(t0=round(priced, 3), t1=round(S[3] - pre, 3), a=37, b=37, fmt="money",
         src="Price of one kilogram of aluminium, 1859, about the price of silver. Source: Science History Institute, converted to kilograms"),
    dict(t0=round(S[12], 3), t1=round(S[13] - pre, 3), a=37, b=0.66, tick=[round(S[12] + 0.07, 3), round(S[13] - 0.4, 3)], fmt="money",
         src="Price of one kilogram of aluminium, 1859, then after Hall's process. Source: Science History Institute, converted to kilograms"),
    dict(t0=round(S[13], 3), t1=round(S[14] - pre, 3), a=3.6, b=73800000, tick=[round(S[13] + 0.08, 3), round(S[14] - 0.45, 3)], fmt="dec1",
         src="World aluminium production, tonnes a year, 1884 to 2025. Sources: Science History Institute, International Aluminium Institute"),
    dict(t0=round(S[14], 3), t1=round(S[15] - pre, 3), a=0, b=420000000000, tick=[round(S[14] + 0.05, 3), round(S[15] - 0.4, 3)], fmt="int",
         src="Aluminium drink cans used in a year, 1884 to 2020. Every kilo of new aluminium is still made by Hall's process. Source: International Aluminium Institute"),
]

span = E[8] - S[8]
salts = ["Fluorspar", "Potassium fluoride", "Sodium fluoride", "Magnesium fluoride", "Aluminium fluoride"]
edl["lists"] = [dict(t0=round(S[8], 3), t1=round(S[9] - pre, 3), tag="FAILED", src="Source: Science History Institute",
                     items=[dict(text=s, t=round(S[8] + 0.05 + i * span / 5.5, 3)) for i, s in enumerate(salts)])]


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "Napoleon the Third served", t1=at(0, "his", frac=0.4)), sp(0, "his best guests with aluminium.", t0=at(0, "his", frac=0.4)),
    sp(1, "The rest got silver."),
    sp(2, "Earth's most common metal,", t1=priced), sp(2, "priced like silver.", t0=priced),
    sp(3, "A professor said:", t1=at(3, "make") - 0.02), sp(3, "make it cheap, make a fortune.", t0=at(3, "make") - 0.02),
    sp(4, "His student, 22,", t1=at(4, "went", frac=0.45)), sp(4, "went home to the woodshed.", t0=at(4, "went", frac=0.45)),
    sp(5, "Chemists used sodium."), sp(6, "He used electricity."),
    sp(7, "Dissolve the ore,", t1=at(7, "let", frac=0.4)), sp(7, "let current pull the metal out.", t0=at(7, "let", frac=0.4)),
    sp(8, "Five salts failed."), sp(9, "Then, molten cryolite."), sp(10, "February 1886."), sp(11, "Beads of aluminium."),
    sp(12, "Soon, 66 cents a kilo."), sp(13, "Under 4 tonnes a year became 74 million."), sp(14, "Still made his way today."),
    sp(15, "Napoleon's treasure now wraps your leftovers."),
]
# keep subtitles from overlapping the next one
subs = edl["subtitles"]
for a, b in zip(subs, subs[1:]):
    a["t1"] = round(min(a["t1"], b["t0"] - 0.02), 3)

edl["glitches"] = [round(S[12], 3), round(S[16], 3)]
edl["end"] = dict(t0=round(S[16], 3),
                  words=[dict(w="Ad", t=at(16, "Ad")), dict(w="Astra.", t=at(16, "Astra", frac=0.5))],
                  slogan=[dict(w="Fucking", t=at(17, "Fucking")), dict(w="accelerate.", t=at(17, "accelerate", frac=0.45))],
                  card_t=card_t, emblem=os.path.join(os.environ.get("KIT", "kit"), "emblem.jpg"), url_line="Apply at joinadastra.com")
json.dump(edl, open(out_f, "w"), indent=1)
print("duration", dur, "drop", round(S[12], 3), "card", card_t)
for s in edl["shots"]:
    print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['src'].split('/')[-1]}")
