"""Edit list for Stephanie Kwolek, Kevlar (21 October 2026), built from the Otis model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-21-kwolek/edl.py vo.segments.json vo.words.json out_edl.json
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
SYN = {"five": {"5", "five"}, "ad": {"ad", "add"}, "accelerate": {"accelerate"}, "1965": {"1965"}, "fibre": {"fiber", "fibre"}, "tyres": {"tires", "tyres"}, "armour": {"armor", "armour"}, "3000": {"3", "000"}, "ninety": {"90"}}


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
mid = round(at(9, "boat") - 0.05, 3)
A = "archival"

edl = dict(duration=dur)
edl["shots"] = [
    shot("k01.png", "image", 0.0, S[1], look=A, z=[1.0, 1.1]),
    shot("k02c.png", "image", S[1], S[2], look=A, z=[1.0, 1.1]),
    shot("k03.png", "image", S[2], S[3], look=A, z=[1.0, 1.1]),
    shot("k04_swirl.mp4", "video", S[3], S[4], look=A, src_in=0.3),
    shot("k05.png", "image", S[4], S[5], look=A, z=[1.04, 1.12]),
    shot("k06.png", "image", S[5], S[6], look=A, z=[1.0, 1.1]),
    shot("k07_threads.mp4", "video", S[6], S[7], look=A, src_in=0.3),
    shot("k08.png", "image", S[7], S[8], look=A, z=[1.04, 1.12]),
    shot("k06.png", "image", S[8], S[9], look=A, z=[1.12, 1.02]),
    shot("k09.png", "image", S[9], mid, look=A, z=[1.0, 1.1]),
    shot("k10_hull.mp4", "video", mid, S[10], look="modern", src_in=0.3),
    shot("k11.png", "image", S[10], S[11], look="modern", z=[1.0, 1.1]),
    shot("k12.png", "image", S[11], S[12], look=A, z=[1.04, 1.12]),
    shot("k13.png", "image", S[12], S[13], look="snap", z=[1.0, 1.1]),
    shot("k14_sky.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("A", at(0, "A")), ("cloudy", at(0, "cloudy")), ("liquid", at(0, "liquid"))], [("became", at(0, "became")), ("a", at(0, "a", 1)), ("fibre", at(0, "fibre")), ("stronger", at(0, "stronger")), ("than", at(0, "than")), ("steel.", at(0, "steel"))]),
    H(S[1] + 0.02, S[2] - pre, [("Delaware,", at(1, "Delaware"))], [("1965.", at(1, "1965"))]),
    H(S[2] + 0.02, S[3] - pre, [("Stephanie", at(2, "Stephanie")), ("Kwolek.", at(2, "Kwolek"))], [("DuPont", at(2, "DuPont")), ("chemist", at(2, "chemist")), ("since", at(2, "since")), ("1946.", at(2, "1946"))]),
    H(S[3] + 0.02, S[4] - pre, [("Thin", at(3, "thin")), ("and", at(3, "and")), ("cloudy.", at(3, "cloudy"))]),
    H(S[4] + 0.02, S[5] - pre, [("Everyone", at(4, "Everyone")), ("assumed", at(4, "assumed"))], [("it", at(4, "it")), ("failed.", at(4, "failed"))]),
    H(S[5] + 0.02, S[6] - pre, [("The", at(5, "The")), ("technician", at(5, "technician")), ("refused.", at(5, "refused"))]),
    H(S[6] + 0.02, S[7] - pre, [("She", at(6, "She")), ("insisted.", at(6, "insisted"))]),
    H(S[7] + 0.02, S[8] - pre, [("5", at(7, "five")), ("times", at(7, "times")), ("stronger", at(7, "stronger"))], [("than", at(7, "than")), ("steel.", at(7, "steel"))]),
    H(S[8] + 0.02, S[9] - pre, [("Kevlar,", at(8, "Kevlar"))], [("1971.", at(8, "1971"))]),
    H(S[9] + 0.02, S[10] - pre, [("About", at(9, "about")), ("200", at(9, "200"))], [("products.", at(9, "products"))]),
    H(S[10] + 0.02, S[11] - pre, [("3,000+", at(10, "3"))], [("officers", at(10, "officers")), ("saved.", at(10, "saved"))]),
    H(S[11] + 0.02, S[12] - pre, [("Retired", at(11, "retired")), ("1986.", at(11, "1986"))], [("Died", at(11, "died")), ("2014,", at(11, "2014"))], [("aged", at(11, "aged")), ("90.", at(11, "ninety"))]),
    H(S[12] + 0.02, S[13] - pre, [("The", at(12, "The")), ("failure", at(12, "failure"))], [("was", at(12, "was")), ("the", at(12, "the", 1)), ("discovery.", at(12, "discovery"))]),
]

edl["labels"] = [
    dict(t0=round(S[1] + 0.1, 3), t1=round(S[2] - pre, 3), text="Du Pont research laboratory, Delaware. Source: Science History Institute"),
    dict(t0=round(S[2] + 0.1, 3), t1=round(S[3] - pre, 3), text="DuPont chemist from 1946. Source: Encyclopaedia Britannica"),
    dict(t0=round(S[5] + 0.1, 3), t1=round(S[6] - pre, 3), text="Technician anecdote, single source. Source: Great Patent"),
    dict(t0=round(S[7] + 0.1, 3), t1=round(S[8] - pre, 3), text="About 5 times stronger than steel, by weight. Source: Science History Institute"),
    dict(t0=round(S[8] + 0.1, 3), t1=round(S[9] - pre, 3), text="Commercial launch, 1971. Source: Encyclopaedia Britannica"),
    dict(t0=round(S[9] + 0.1, 3), t1=round(S[10] - pre, 3), text="About 200 applications. Source: Science History Institute"),
    dict(t0=round(S[10] + 0.1, 3), t1=round(S[11] - pre, 3), text="All police body armour, as of 2006. Source: National Institute of Justice"),
    dict(t0=round(S[11] + 0.1, 3), t1=round(S[12] - pre, 3), text="Died 18 June 2014. Source: Encyclopaedia Britannica"),
]

edl["counters"] = []
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "A cloudy liquid that looked like a failure became a fibre stronger than steel."),
    sp(1, "Delaware, 1965."),
    sp(2, "Stephanie Kwolek had been a DuPont chemist since 1946."),
    sp(3, "Her new solution came out thin and cloudy."),
    sp(4, "Everyone assumed it had failed."),
    sp(5, "The technician refused to spin it, fearing it would clog the machine."),
    sp(6, "She insisted."),
    sp(7, "The fibre came out about 5 times stronger than steel by weight."),
    sp(8, "Kevlar reached the market in 1971."),
    sp(9, "Today it goes into about 200 products, from tyres to boat hulls."),
    sp(10, "By 2006, police body armour had saved at least 3,000 officers."),
    sp(11, "Kwolek retired in 1986 and died in 2014, aged 90."),
    sp(12, "The failure was the discovery."),
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
