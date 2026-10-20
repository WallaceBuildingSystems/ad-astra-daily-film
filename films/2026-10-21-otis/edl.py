"""Edit list for Elisha Otis, the safety elevator (21 October 2026), built from the Bohlin model.

usage: SRC=src CLIPS=clips KIT=kit python3 films/2026-10-21-otis/edl.py vo.segments.json vo.words.json out_edl.json
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
SYN = {"four": {"4", "four"}, "two": {"2", "two"}, "ax": {"ax", "axe"}, "1854": {"1854"}, "billion": {"billion"}, "five": {"5"}, "ad": {"ad", "add"}, "accelerate": {"accelerate"}, "1959": {"1959"}, "2004": {"2004"}, "one": {"1", "one"}, "15": {"15"}, "eight": {"8", "eight"}, "germanys": {"germanys", "germany"}, "waist": {"waist", "waste"}, "it": {"it"}, "carmaker": {"carmaker", "car"}}


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
mid = round(at(12, "billion") - 0.05, 3)
A = "archival"

edl = dict(duration=dur)
edl["shots"] = [
    shot("o01_rope.png", "image", 0.0, S[1], look=A, z=[1.0, 1.1]),
    shot("o02_street.mp4", "video", S[1], S[2], look=A, src_in=0.3),
    shot("o03_stairs.png", "image", S[2], S[3], look=A, z=[1.0, 1.1]),
    shot("o04_hoist.png", "image", S[3], S[4], look=A, z=[1.04, 1.12]),
    shot("o05_factory.mp4", "video", S[4], S[5], look=A, src_in=0.3),
    shot("o06_palace.png", "image", S[5], S[6], look=A, z=[1.0, 1.1]),
    shot("o07_axe.png", "image", S[6], S[7], look=A, z=[1.0, 1.1]),
    shot("o08_platform.png", "image", S[7], S[8], look=A, z=[1.04, 1.12]),
    shot("o09_crowd.png", "image", S[8], S[9], look=A, z=[1.0, 1.1]),
    shot("o10_ledger.png", "image", S[9], S[10], look=A, z=[1.0, 1.1]),
    shot("o11_store.mp4", "video", S[10], S[11], look=A, src_in=0.3),
    shot("o12_grave.png", "image", S[11], S[12], look=A, z=[1.04, 1.12]),
    shot("o13_towers.mp4", "video", S[12], mid, look="modern", src_in=0.3),
    shot("o14_lobby.png", "image", mid, S[13], look="snap", z=[1.0, 1.1]),
    shot("o15_stars.mp4", "video", S[13], card_t, look="film", src_in=0.3),
]

edl["headlines"] = [
    H(0.05, S[1] - pre, [("The", at(0, "The")), ("skyscraper", at(0, "skyscraper"))], [("began", at(0, "began")), ("with", at(0, "with")), ("a", at(0, "a")), ("rope", at(0, "rope")), ("cut", at(0, "cut")), ("on", at(0, "on")), ("purpose.", at(0, "purpose"))]),
    H(S[1] + 0.02, S[2] - pre, [("New", at(1, "New")), ("York,", at(1, "York"))], [("1854.", at(1, "1854"))]),
    H(S[2] + 0.02, S[3] - pre, [("Buildings", at(2, "Buildings")), ("rarely", at(2, "rarely"))], [("passed", at(2, "passed")), ("4", at(2, "four")), ("floors.", at(2, "floors"))]),
    H(S[3] + 0.02, S[4] - pre, [("Nobody", at(3, "nobody")), ("trusted", at(3, "trusted"))], [("the", at(3, "the")), ("rope.", at(3, "rope"))]),
    H(S[4] + 0.02, S[5] - pre, [("Elisha", at(4, "Elisha")), ("Otis.", at(4, "Otis"))], [("A", at(4, "a")), ("platform", at(4, "platform")), ("that", at(4, "that")), ("locks.", at(4, "locks"))]),
    H(S[5] + 0.02, S[6] - pre, [("Crystal", at(5, "Crystal")), ("Palace.", at(5, "Palace"))], [("High", at(5, "high")), ("above", at(5, "above")), ("a", at(5, "a")), ("crowd.", at(5, "crowd"))]),
    H(S[6] + 0.02, S[7] - pre, [("Cut", at(6, "cut")), ("the", at(6, "the")), ("rope.", at(6, "rope"))]),
    H(S[7] + 0.02, S[8] - pre, [("Dropped", at(7, "dropped")), ("2", at(7, "two")), ("feet.", at(7, "feet"))], [("Stopped.", at(7, "stopped"))]),
    H(S[8] + 0.02, S[9] - pre, [("All", at(8, "All")), ("safe,", at(8, "safe"))], [("gentlemen.", at(8, "gentlemen"))]),
    H(S[9] + 0.02, S[10] - pre, [("15", at(9, "15")), ("in", at(9, "in")), ("1855.", at(9, "1855"))], [("27", at(9, "27")), ("in", at(9, "in", 1)), ("1856.", at(9, "1856"))]),
    H(S[10] + 0.02, S[11] - pre, [("1857.", at(10, "1857"))], [("First", at(10, "first")), ("passenger", at(10, "passenger")), ("safety", at(10, "safety")), ("elevator.", at(10, "elevator"))]),
    H(S[11] + 0.02, S[12] - pre, [("Died", at(11, "died")), ("1861,", at(11, "1861"))], [("aged", at(11, "aged")), ("49.", at(11, "49"))]),
    H(S[12] + 0.02, S[13] - pre, [("2.5", at(12, "2")), ("billion", at(12, "billion"))], [("people", at(12, "people")), ("a", at(12, "a")), ("day.", at(12, "day"))]),
]

edl["labels"] = [
    dict(t0=round(S[2] + 0.1, 3), t1=round(S[3] - pre, 3), text="Buildings usually no higher than 4 storeys. Source: Encyclopedia.com"),
    dict(t0=round(S[4] + 0.1, 3), t1=round(S[5] - pre, 3), text="Elisha Otis, Yonkers, New York. Source: Encyclopaedia Britannica"),
    dict(t0=round(S[5] + 0.1, 3), t1=round(S[6] - pre, 3), text="New York Crystal Palace, 1854. Source: Encyclopaedia Britannica"),
    dict(t0=round(S[7] + 0.1, 3), t1=round(S[8] - pre, 3), text="The platform dropped 2 feet. Source: New England Historical Society"),
    dict(t0=round(S[9] + 0.1, 3), t1=round(S[10] - pre, 3), text="Sales: 15 in 1855, 27 in 1856. Source: Encyclopedia.com"),
    dict(t0=round(S[10] + 0.1, 3), t1=round(S[11] - pre, 3), text="First passenger safety elevator, 23 March 1857. Source: Encyclopaedia Britannica"),
    dict(t0=round(S[12] + 0.1, 3), t1=round(S[13] - pre, 3), text="About 2.5 billion people a day. Source: Otis, company figure"),
]

edl["counters"] = []
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "The skyscraper began with a rope cut on purpose."),
    sp(1, "New York, 1854."),
    sp(2, "Buildings rarely passed 4 floors, because people would not climb more."),
    sp(3, "Elevators existed, but nobody trusted the rope."),
    sp(4, "Elisha Otis, a bedstead mechanic, built a platform that locks if the rope breaks."),
    sp(5, "At the Crystal Palace he rode it high above a crowd."),
    sp(6, "An assistant cut the rope with an axe."),
    sp(7, "The platform dropped 2 feet and stopped."),
    sp(8, "All safe, gentlemen, all safe."),
    sp(9, "Orders followed, 15 elevators in 1855 and 27 in 1856."),
    sp(10, "1857, the first passenger safety elevator, in a New York store."),
    sp(11, "He died in 1861, aged 49."),
    sp(12, "Otis says its elevators and escalators now move 2.5 billion people a day."),
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
