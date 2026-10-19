"""Edit list for Nils Bohlin, the three-point seat belt (20 October 2026), built from the Kolff model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-20-bohlin/edl.py vo.segments.json vo.words.json out_edl.json
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
SYN = {"ad": {"ad", "add"}, "accelerate": {"accelerate"}, "1959": {"1959"}, "2004": {"2004"}, "one": {"1", "one"}, "15": {"15"}, "eight": {"8", "eight"}, "germanys": {"germanys", "germany"}, "waist": {"waist", "waste"}, "it": {"it"}, "carmaker": {"carmaker", "car"}}


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
mid = round(at(12, "required") - 0.05, 3)
R = "reel16"

edl = dict(duration=dur)
edl["shots"] = [
    shot("b01_seat.png", "image", 0.0, S[1], look=R, z=[1.0, 1.1]),
    shot("b02_street.mp4", "video", S[1], S[2], look=R, src_in=0.3),
    shot("b03_saab.png", "image", S[2], S[3], look=R, z=[1.0, 1.1]),
    shot("b04_office.png", "image", S[3], S[4], look=R, z=[1.04, 1.12]),
    shot("b05_lap.png", "image", S[4], S[5], look=R, z=[1.0, 1.1]),
    shot("b06_unused.png", "image", S[5], S[6], look=R, z=[1.0, 1.1]),
    shot("b07_board.png", "image", S[6], S[7], look=R, z=[1.0, 1.1]),
    shot("b08_buckle.mp4", "video", S[7], S[8], look=R, src_in=0.3),
    shot("b09_pv544.mp4", "video", S[8], S[9], look=R, src_in=0.3),
    shot("b10_table.png", "image", S[9], S[10], look=R, z=[1.04, 1.12]),
    shot("b11_office.png", "image", S[10], S[11], look=R, z=[1.0, 1.1]),
    shot("b12_click.png", "image", S[11], S[12], look="snap", z=[1.0, 1.1]),
    shot("b13_rear.png", "image", S[12], mid, look="snap", z=[1.04, 1.12]),
    shot("b14_road.mp4", "video", mid, S[13], look="snap", src_in=0.3),
    shot("b15_stars.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("The", at(0, "The")), ("seat", at(0, "seat")), ("belt", at(0, "belt"))],
      [("began", at(0, "began")), ("with", at(0, "with")), ("an", at(0, "an")), ("ejection", at(0, "ejection")), ("seat", at(0, "seat", 1)), ("engineer.", at(0, "engineer"))]),
    H(S[1] + 0.02, S[2] - pre, [("Sweden,", at(1, "Sweden"))], [("1958.", at(1, "1958"))]),
    H(S[2] + 0.02, S[3] - pre, [("Nils", at(2, "Nils")), ("Bohlin", at(2, "Bohlin"))], [("ejection", at(2, "ejection")), ("seats", at(2, "seats")), ("at", at(2, "at")), ("Saab.", at(2, "Saab"))]),
    H(S[3] + 0.02, S[4] - pre, [("Volvo", at(3, "Volvo")), ("hired", at(3, "hired")), ("him.", at(3, "him"))]),
    H(S[4] + 0.02, S[5] - pre, [("Waist-only", at(4, "waist")), ("belts", at(4, "belts"))], [("hit", at(4, "hitting")), ("the", at(4, "the")), ("dash.", at(4, "dash"))]),
    H(S[5] + 0.02, S[6] - pre, [("Many", at(5, "Many")), ("did", at(5, "did")), ("not", at(5, "not"))], [("wear", at(5, "wear")), ("them.", at(5, "them"))]),
    H(S[6] + 0.02, S[7] - pre, [("Almost", at(6, "almost")), ("a", at(6, "a")), ("year.", at(6, "year"))], [("Chest", at(6, "chest")), ("and", at(6, "and")), ("hips.", at(6, "hips"))]),
    H(S[7] + 0.02, S[8] - pre, [("Easy", at(7, "easy")), ("to", at(7, "to")), ("fasten.", at(7, "fasten"))], [("Easy", at(7, "easy", 1)), ("to", at(7, "to", 1)), ("release.", at(7, "release"))]),
    H(S[8] + 0.02, S[9] - pre, [("1959,", at(8, "1959"))], [("first", at(8, "first")), ("Volvos", at(8, "Volvos")), ("sold.", at(8, "sold"))]),
    H(S[9] + 0.02, S[10] - pre, [("Free", at(9, "free")), ("for", at(9, "for")), ("every", at(9, "every"))], [("other", at(9, "other")), ("car", at(9, "carmaker")), ("maker.", at(9, "carmaker"))]),
    H(S[10] + 0.02, S[11] - pre, [("1", at(10, "one")), ("of", at(10, "of")), ("8", at(10, "eight"))], [("top", at(10, "most")), ("patents", at(10, "patents")), ("in", at(10, "in")), ("100", at(10, "100")), ("years.", at(10, "years"))]),
    H(S[11] + 0.02, S[12] - pre, [("15,000", at(11, "15")), ("lives", at(11, "lives"))], [("a", at(11, "a")), ("year.", at(11, "year"))]),
    H(S[12] + 0.02, S[13] - pre, [("2004,", at(12, "2004"))], [("every", at(12, "every")), ("seat.", at(12, "seat"))]),
]

edl["labels"] = [
    dict(t0=round(S[2] + 0.1, 3), t1=round(S[3] - pre, 3), text="Nils Bohlin, Saab ejection seats. Source: Automotive Hall of Fame"),
    dict(t0=round(S[3] + 0.1, 3), t1=round(S[4] - pre, 3), text="Joined Volvo 1958. Source: German Patent and Trade Mark Office"),
    dict(t0=round(S[9] + 0.1, 3), t1=round(S[10] - pre, 3), text="Volvo opened the design to other makers. Source: The Collector"),
    dict(t0=round(S[10] + 0.1, 3), t1=round(S[11] - pre, 3), text="1 of the 8 most important patents in its first 100 years. Source: Automotive Hall of Fame"),
    dict(t0=round(S[11] + 0.1, 3), t1=round(S[12] - pre, 3), text="About 15,000 lives a year, United States. Source: Wikipedia, citing the National Highway Traffic Safety Administration"),
    dict(t0=round(S[12] + 0.1, 3), t1=round(S[13] - pre, 3), text="Compulsory on all seats, Germany, 1 July 2004. Source: German Patent and Trade Mark Office"),
]

edl["counters"] = []
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "The seat belt that saves lives began with an ejection seat engineer."),
    sp(1, "Sweden, 1958."),
    sp(2, "Nils Bohlin built ejection seats for pilots at Saab."),
    sp(3, "Volvo hired him as a safety engineer."),
    sp(4, "Waist-only belts left heads hitting the dash and the wheel."),
    sp(5, "Many people still did not wear them."),
    sp(6, "He spent almost a year on a belt that held the chest and the hips."),
    sp(7, "It was easy to fasten and easy to release."),
    sp(8, "1959, the first Volvos were sold with it."),
    sp(9, "Volvo let every other car maker use the design for free."),
    sp(10, "Germany's patent office named it 1 of its 8 most important patents in 100 years."),
    sp(11, "In the United States it saves an estimated 15,000 lives a year."),
    sp(12, "2004, Germany required it on every seat."),
]
subs = edl["subtitles"]
for a, b in zip(subs, subs[1:]):
    a["t1"] = round(min(a["t1"], b["t0"] - 0.02), 3)

edl["glitches"] = [round(S[8], 3), round(S[13], 3)]
edl["end"] = dict(t0=round(S[13], 3),
                  words=[dict(w="Ad", t=at(13, "Ad")), dict(w="Astra.", t=at(13, "Astra", frac=0.5))],
                  slogan=[dict(w="Fucking", t=at(14, "Fucking")), dict(w="accelerate.", t=at(14, "accelerate", frac=0.45))],
                  card_t=card_t, emblem=os.path.join(os.environ.get("KIT", "kit"), "emblem.jpg"), url_line="Apply at joinadastra.com")
json.dump(edl, open(out_f, "w"), indent=1, ensure_ascii=False)
print("duration", dur, "glitch", round(S[8], 3), "card", card_t)
for s in edl["shots"]:
    print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['src'].split('/')[-1]}")
