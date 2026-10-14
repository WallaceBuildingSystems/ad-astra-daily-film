"""Edit list for Robert Goddard, the liquid fuel rocket (14 October 2026), built from the Hall model.

usage: SRC=src KIT=kit python3 films/2026-10-14-goddard/edl.py vo.segments.json vo.words.json out_edl.json

Every time comes from the voice: shots cut on phrase starts, headline words land on the spoken words.
"""
import json, os, re, sys

SRC = os.environ.get("SRC", "src")  # the folder of downloaded pictures and clips
seg_f, words_f, out_f = sys.argv[1:4]
P = json.load(open(seg_f))["segments"]
W = json.load(open(words_f))
assert len(P) == 17, f"expected 17 phrases, got {len(P)}"
S = [p["out_s"] for p in P]
E = [p["out_e"] for p in P]

SYN = {"ad": {"ad", "add"}, "three": {"3", "three"}, "moon": {"moon"}, "metres": {"metres", "meters"},
       "accelerate": {"accelerate"}}


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


def shot(name, kind, t0, t1, **kw):
    return dict(src=f"{SRC}/{name}", kind=kind, t0=round(t0, 3), t1=round(t1, 3), **kw)


def H(t0, t1, *lines):
    return dict(t0=round(t0, 3), t1=round(t1, 3), lines=[[dict(w=w, t=round(t, 3)) for w, t in line] for line in lines])


def sub(t0, t1, text):
    return dict(t0=round(t0, 3), t1=round(t1, 3), text=text)


card_t = round(E[16] + 0.22, 3)
dur = round(card_t + 2.1, 2)
pre = 0.04  # leave a hair before the next cut

edl = dict(duration=dur)
edl["shots"] = [
    shot("s01_press.mp4", "video", 0.0, S[1], look="early", speed=0.6, z=[1.0, 1.02]),
    shot("s02_fireworks.mp4", "video", S[1], S[2], look="early", src_in=0.2),
    shot("s03_powder.png", "image", S[2], S[3], look="early", focus=[0.55, 0.55]),
    shot("s04_professor.png", "image", S[3], S[4], look="early", focus=[0.62, 0.5]),
    shot("s05_fuse.png", "image", S[4], S[5], look="early", focus=[0.5, 0.55]),
    shot("s06_lox.mp4", "video", S[5], S[6], look="early", src_in=0.3, speed=0.9, z=[1.0, 1.02]),
    shot("s07_failed.png", "image", S[6], S[7], look="early", z=[1.08, 1.16]),
    shot("s08_farm.png", "image", S[7], S[8], look="early"),
    shot("s09_flame.mp4", "video", S[8], S[9], look="early", src_in=0.2),
    shot("s10_rise.mp4", "video", S[9], S[10], look="early", speed=0.75),
    shot("s11_landing.png", "image", S[10], S[11], look="early"),
    shot("s12_moon_rocket.mp4", "video", S[11], S[12], look="film", z=[1.1, 1.14], speed=0.8),
    shot("s13_launch_today.mp4", "video", S[12], S[13], look="modern"),
    shot("s14_earth_night.mp4", "video", S[13], S[14], look="film"),
    shot("s15_correction.png", "image", S[14], S[15], look="film", z=[1.04, 1.12]),
    shot("s16_moon.png", "image", S[15], card_t, look="film"),
]

rockets = at(0, "rockets")
the69 = at(14, "the")
edl["headlines"] = [
    H(0.05, rockets - 0.05, [("1920.", at(0, "1920"))],
      [("The", at(0, "The")), ("New", at(0, "New")), ("York", at(0, "York")), ("Times:", at(0, "Times"))]),
    H(rockets, S[1] - pre, [("Rockets", rockets), ("can't", at(0, "can't"))],
      [("fly", at(0, "fly")), ("in", at(0, "in")), ("space.", at(0, "space"))]),
    H(S[1] + 0.02, S[2] - pre, [("Rockets", at(1, "Rockets")), ("were", at(1, "were") + 0.12)],
      [("fireworks.", at(1, "fireworks"))]),
    H(S[3] + 0.02, S[4] - pre, [("Robert", at(3, "Robert")), ("Goddard,", at(3, "Goddard"))],
      [("physics", at(3, "physics")), ("professor.", at(3, "professor"))]),
    H(S[4] + 0.02, S[5] - pre, [("Fireworks", at(4, "Fireworks")), ("burned", at(4, "burned"))],
      [("powder.", at(4, "powder"))]),
    H(S[5] + 0.02, S[6] - pre, [("He", at(5, "He")), ("burned", at(5, "burned"))],
      [("gasoline", at(5, "gasoline")), ("and", at(5, "and"))],
      [("liquid", at(5, "liquid")), ("oxygen.", at(5, "oxygen"))]),
    H(S[6] + 0.02, S[7] - pre, [("First", at(6, "first")), ("attempt:", at(6, "attempt"))],
      [("failed.", at(6, "failed"))]),
    H(S[7] + 0.02, S[8] - pre, [("16", at(7, "March")), ("March", at(7, "16")), ("1926.", at(7, "1926"))]),
    H(S[8] + 0.02, S[9] - pre, [("For", at(8, "For")), ("20", at(8, "20")), ("seconds", at(8, "seconds"))],
      [("it", at(8, "it")), ("just", at(8, "just")), ("burned.", at(8, "burned"))]),
    H(S[9] + 0.02, S[10] - pre, [("Then", at(9, "Then")), ("it", at(9, "it")), ("rose.", at(9, "rose"))]),
    H(S[10] + 0.02, S[11] - pre, [("2.5", at(10, "2")), ("seconds.", at(10, "seconds"))],
      [("12.5", at(10, "12")), ("metres.", at(10, "metres"))]),
    H(S[13] + 0.02, S[14] - pre, [("Your", at(13, "Your")), ("maps", at(13, "maps")), ("and", at(13, "and"))],
      [("weather", at(13, "weather")), ("forecasts", at(13, "forecasts"))],
      [("ride", at(13, "ride")), ("on", at(13, "on")), ("them.", at(13, "them"))]),
    H(S[14] + 0.02, the69 - 0.05, [("1969.", at(14, "1969"))]),
    H(the69, S[15] - pre, [("“The", the69), ("Times", at(14, "Times")), ("regrets", at(14, "printed"))],
      [("the", at(14, "a")), ("error.”", at(14, "correction"))]),
]

edl["labels"] = [
    dict(t0=round(at(0, "The") - 0.1, 3), t1=round(S[1] - pre, 3), text="The New York Times, editorial, 13 January 1920."),
    dict(t0=round(at(3, "physics"), 3), t1=round(S[4] - pre, 3), text="Clark University, Worcester, Massachusetts."),
    dict(t0=round(S[6] + 0.1, 3), t1=round(S[7] - pre, 3), text="8 March 1926."),
    dict(t0=round(at(7, "1926"), 3), t1=round(S[8] - pre, 3), text="His aunt Effie Ward's farm, Auburn, Massachusetts."),
    dict(t0=round(S[8] + 0.1, 3), t1=round(S[9] - pre, 3), text="The motor burned 20 seconds before it lifted. Source: National Air and Space Museum"),
    dict(t0=round(at(10, "seconds"), 3), t1=round(S[11] - pre, 3), text="It landed 56 metres away, in a cabbage patch. Source: National Aeronautics and Space Administration"),
    dict(t0=round(the69, 3), t1=round(S[15] - pre, 3), text="The New York Times, 17 July 1969, as Apollo 11 flew."),
]

edl["counters"] = [
    dict(t0=round(at(2, "over") - 0.1, 3), t1=round(S[3] - pre, 3), a=98, b=98, fmt="int", prefix="Over ", unit="%",
         src="Energy a powder rocket wasted, Goddard to the Smithsonian, 1916. Source: Smithsonian Institution Archives"),
    dict(t0=round(S[11], 3), t1=round(S[12] - pre, 3), a=12.5, b=384400000, unit=" m", a_label="12.5 m",
         tick=[round(S[11] + 0.1, 3), round(S[12] - 0.45, 3)], fmt="dec1",
         src="Height of the first flight, 1926, then the distance to the Moon. Source: National Aeronautics and Space Administration"),
    dict(t0=round(S[12], 3), t1=round(S[13] - pre, 3), a=0, b=324,
         tick=[round(at(12, "324") - 0.15, 3), round(S[13] - 0.45, 3)], fmt="int",
         src="Launches to orbit in a year, 1926, then 2025. Source: American Institute of Aeronautics and Astronautics, SpaceNews"),
]
edl["lists"] = []


def sp(k, text, t0=None, t1=None):
    return sub(S[k] if t0 is None else t0, (E[k] + 0.12 if t1 is None else t1), text)


edl["subtitles"] = [
    sp(0, "1920. The New York Times:", t1=rockets), sp(0, "rockets can't fly in space.", t0=rockets),
    sp(1, "Rockets were fireworks."),
    sp(2, "Powder wasted over 98 per cent of its energy."),
    sp(3, "Robert Goddard, physics professor,", t1=at(3, "aimed")), sp(3, "aimed for space.", t0=at(3, "aimed")),
    sp(4, "Fireworks burned powder."),
    sp(5, "He burned gasoline and liquid oxygen."),
    sp(6, "His first attempt failed."),
    sp(7, "16 March 1926, his aunt's farm."),
    sp(8, "For 20 seconds it just burned."),
    sp(9, "Then it rose."),
    sp(10, "2.5 seconds. 12.5 metres."),
    sp(11, "43 years later,", t1=at(11, "his")), sp(11, "his idea flew 3 men to the Moon.", t0=at(11, "his")),
    sp(12, "Last year, 324 launches to orbit."),
    sp(13, "Your maps and weather forecasts ride on them."),
    sp(14, "In 1969, The Times printed a correction."),
]
# keep subtitles from overlapping the next one
subs = edl["subtitles"]
for a, b in zip(subs, subs[1:]):
    a["t1"] = round(min(a["t1"], b["t0"] - 0.02), 3)

edl["glitches"] = [round(S[11], 3), round(S[15], 3)]
edl["end"] = dict(t0=round(S[15], 3),
                  words=[dict(w="Ad", t=at(15, "Ad")), dict(w="Astra.", t=at(15, "Astra", frac=0.5))],
                  slogan=[dict(w="Fucking", t=at(16, "Fucking")), dict(w="accelerate.", t=at(16, "accelerate", frac=0.45))],
                  card_t=card_t, emblem=os.path.join(os.environ.get("KIT", "kit"), "emblem.jpg"), url_line="Apply at joinadastra.com")
json.dump(edl, open(out_f, "w"), indent=1, ensure_ascii=False)
print("duration", dur, "drop", round(S[11], 3), "card", card_t)
for s in edl["shots"]:
    print(f"  {s['t0']:6.2f}-{s['t1']:6.2f} {s['src'].split('/')[-1]}")
