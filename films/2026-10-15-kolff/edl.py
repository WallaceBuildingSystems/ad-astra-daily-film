"""Edit list for Willem Kolff, the artificial kidney (15 October 2026), built from the Goddard model.

usage: SRC=src KIT=kit python3 films/2026-10-15-kolff/edl.py vo.segments.json vo.words.json out_edl.json

Every time comes from the voice: shots cut on phrase starts, headline words land on the spoken words.
"""
import json, os, re, sys

SRC = os.environ.get("SRC", "src")
seg_f, words_f, out_f = sys.argv[1:4]
P = json.load(open(seg_f))["segments"]
W = json.load(open(words_f))
assert len(P) == 16, f"expected 16 phrases, got {len(P)}"
S = [p["out_s"] for p in P]
E = [p["out_e"] for p in P]

SYN = {"ad": {"ad", "add"}, "one": {"1", "one"}, "fifteen": {"15", "fifteen"}, "seven": {"7", "seven"},
       "accelerate": {"accelerate"}, "sixtyseven": {"67", "sixtyseven"}, "thirtytwo": {"32", "thirtytwo"}}


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def words_in(k):
    lo, hi = S[k] - 0.4, E[k] + 0.2
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


def shot(name, kind, t0, t1, **kw):
    return dict(src=f"{SRC}/{name}", kind=kind, t0=round(t0, 3), t1=round(t1, 3), **kw)


def H(t0, t1, *lines):
    return dict(t0=round(t0, 3), t1=round(t1, 3), lines=[[dict(w=w, t=round(t, 3)) for w, t in line] for line in lines])


def sub(t0, t1, text):
    return dict(t0=round(t0, 3), t1=round(t1, 3), text=text)


card_t = round(E[15] + 0.22, 3)
dur = round(card_t + 2.1, 2)
pre = 0.04
blood_t = at(5, "the", 1)  # "the drum turned": the cut from blood to drum

edl = dict(duration=dur)
edl["shots"] = [
    shot("s01_casings.png", "image", 0.0, S[1], look="reel16", focus=[0.4, 0.5]),
    shot("s02_town.mp4", "video", S[1], S[2], look="reel16", src_in=0.0, speed=0.6),
    shot("s03_ward.png", "image", S[2], S[3], look="reel16", z=[1.0, 1.1]),
    shot("s04_doctor.png", "image", S[3], S[4], look="reel16", focus=[0.68, 0.5]),
    shot("s05_cellophane.png", "image", S[4], S[5], look="reel16", focus=[0.45, 0.6]),
    shot("s07_blood.mp4", "video", S[5], blood_t - 0.05, look="reel16", src_in=0.3),
    shot("s06_drum.mp4", "video", blood_t - 0.05, S[6], look="reel16", src_in=2.0, z=[1.04, 1.06]),
    shot("s08_tank.mp4", "video", S[6], S[7], look="reel16", src_in=0.3),
    shot("s09_bed.png", "image", S[7], S[8], look="reel16", z=[1.04, 1.14]),
    shot("s10_canal.mp4", "video", S[8], S[9], look="reel16", src_in=0.3),
    shot("s11_woman.png", "image", S[9], S[10], look="reel16", focus=[0.6, 0.5]),
    shot("s12_machine.mp4", "video", S[10], S[11], look="reel16", src_in=0.3),
    shot("s13_bench.png", "image", S[11], S[12], look="reel16", z=[1.04, 1.12]),
    shot("s14_clinic.png", "image", S[12], S[13], look="snap", z=[1.04, 1.14], focus=[0.62, 0.55]),
    shot("s15_dialyser.png", "image", S[13], S[14], look="snap", focus=[0.45, 0.55]),
    shot("s16_window.mp4", "video", S[14], card_t, look="reel16", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("A", at(0, "A")), ("kidney", at(0, "kidney")), ("machine", at(0, "machine"))],
      [("from", at(0, "from")), ("sausage", at(0, "sausage")), ("skins.", at(0, "skins"))]),
    H(S[1] + 0.02, S[2] - pre, [("1943.", at(1, "1943"))],
      [("Occupied", at(1, "occupied")), ("Netherlands.", at(1, "Netherlands"))]),
    H(S[2] + 0.02, S[3] - pre, [("Kidney", at(2, "kidney")), ("failure:", at(2, "failure"))],
      [("death", at(2, "death")), ("in", at(2, "within")), ("days.", at(2, "days"))]),
    H(S[3] + 0.02, S[4] - pre, [("Willem", at(3, "Willem")), ("Kolff,", at(3, "Kolff"))],
      [("aged", at(3, "aged")), ("32.", at(3, "32"))]),
    H(S[4] + 0.02, S[5] - pre, [("Sausage", at(4, "sausage")), ("casing", at(4, "casing"))],
      [("on", at(4, "around")), ("a", at(4, "a")), ("drum.", at(4, "drum"))]),
    H(S[5] + 0.02, S[6] - pre, [("Blood", at(5, "blood")), ("through", at(5, "through"))],
      [("the", at(5, "the")), ("casing.", at(5, "casing"))]),
    H(S[6] + 0.02, S[7] - pre, [("Waste", at(6, "waste")), ("out.", at(6, "out"))],
      [("Clean", at(6, "clean")), ("blood", at(6, "blood")), ("back.", at(6, "returned"))]),
    H(S[8] + 0.02, S[9] - pre, [("September", at(8, "September")), ("1945.", at(8, "1945"))],
      [("Patient", at(8, "patient")), ("17.", at(8, "17"))]),
    H(S[9] + 0.02, S[10] - pre, [("67", at(9, "67")), ("years", at(9, "year")), ("old,", at(9, "old"))],
      [("in", at(9, "in")), ("a", at(9, "a")), ("coma.", at(9, "coma"))]),
    H(S[10] + 0.02, S[11] - pre, [("She", at(10, "she")), ("woke.", at(10, "woke"))]),
    H(S[11] + 0.02, S[12] - pre, [("7", at(11, "seven")), ("more", at(11, "more")), ("years.", at(11, "years"))]),
    H(S[13] + 0.02, S[14] - pre, [("Still", at(13, "still")), ("his", at(13, "his")), ("idea.", at(13, "idea"))]),
]

edl["labels"] = [
    dict(t0=round(at(1, "1943") - 0.1, 3), t1=round(S[2] - pre, 3), text="Kampen, the Netherlands, 1943."),
    dict(t0=round(S[4] + 0.1, 3), t1=round(S[5] - pre, 3),
         text="Cellophane tubing made from sausage casing, wound on a drum. Source: Lasker Foundation"),
    dict(t0=round(S[8] + 0.1, 3), t1=round(S[9] - pre, 3), text="September 1945. Source: Lasker Foundation"),
    dict(t0=round(S[10] + 0.1, 3), t1=round(S[12] - pre, 3),
         text="Patient 17 woke after hours of dialysis and lived 7 more years. Source: Lasker Foundation"),
]

edl["counters"] = [
    dict(t0=round(S[7], 3), t1=round(S[8] - pre, 3), a=0, b=14, fmt="int", prefix="", unit=" of 15",
         tick=[round(at(7, "14") - 0.1, 3), round(S[8] - 0.45, 3)],
         src="Patients lost of the first 15 treated, 1943 to 1945. Source: Kolff, Lasker Foundation"),
    dict(t0=round(S[12], 3), t1=round(S[13] - pre, 3), a=0, b=1500000, fmt="int", prefix="", unit="",
         tick=[round(at(12, "1") - 0.15, 3), round(S[13] - 0.45, 3)],
         src="People on dialysis, 1943, then today. Source: Lasker Foundation"),
]
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "A kidney machine built from sausage skins."),
    sp(1, "1943, German-occupied Netherlands."),
    sp(2, "Kidney failure meant death within days."),
    sp(3, "Willem Kolff, doctor, aged 32."),
    sp(4, "He wound cellophane sausage casing around a rotating drum."),
    sp(5, "Blood ran through the casing.", t1=blood_t - 0.05), sp(5, "The drum turned in a tank of fluid.", t0=blood_t - 0.02),
    sp(6, "Waste passed out. Clean blood returned."),
    sp(7, "14 of his first 15 patients died."),
    sp(8, "September 1945, patient 17."),
    sp(9, "A 67-year-old woman, in a coma."),
    sp(10, "After hours on the machine, she woke."),
    sp(11, "She lived 7 more years."),
    sp(12, "Today, 1.5 million people are on dialysis."),
    sp(13, "Each treatment is still his idea."),
]
subs = edl["subtitles"]
for a, b in zip(subs, subs[1:]):
    a["t1"] = round(min(a["t1"], b["t0"] - 0.02), 3)

edl["glitches"] = [round(S[12], 3), round(S[14], 3)]
edl["end"] = dict(t0=round(S[14], 3),
                  words=[dict(w="Ad", t=at(14, "Ad")), dict(w="Astra.", t=at(14, "Astra", frac=0.5))],
                  slogan=[dict(w="Fucking", t=at(15, "Fucking")), dict(w="accelerate.", t=at(15, "accelerate", frac=0.45))],
                  card_t=card_t, emblem=os.path.join(os.environ.get("KIT", "kit"), "emblem.jpg"), url_line="Apply at joinadastra.com")
json.dump(edl, open(out_f, "w"), indent=1, ensure_ascii=False)
print("duration", dur, "drop", round(S[12], 3), "card", card_t)
for s in edl["shots"]:
    print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['src'].split('/')[-1]}")
