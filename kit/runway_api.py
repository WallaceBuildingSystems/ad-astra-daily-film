#!/usr/bin/env python3
"""Runway developer platform helper for the Ad Astra daily film.

The developer key never appears in this file or in the session. It is stored as a network
secret on the cloud environment (allowed website api.dev.runwayml.com, header Authorization,
prefix Bearer) and the agent proxy adds it to each request. If RUNWAYML_API_SECRET is set in
the environment instead, it is sent as the bearer token.

  python3 runway_api.py balance
  python3 runway_api.py stills shots.json outdir [--ids a,b] [--budget N] [--dry-run]
  python3 runway_api.py videos shots.json outdir [--ids a,b] [--model gen4.5] [--seconds 4] [--budget N] [--dry-run]
  python3 runway_api.py task TASK_ID

shots.json: {"shots": [{"id": ..., "still": prompt, "video": true, "motion": prompt, "seconds": 3}]}
Stills: gemini_image3_pro (Nano Banana Pro), 2048 by 2048, 20 credits each, saved as outdir/<id>.png.
Videos: image to video from outdir/<id>.png (sent inline as a JPEG data URI), 960 by 960,
gen4.5 at 12 credits a second or gen4_turbo at 5, saved as outdir/<id>.mp4.
Every task is recorded in outdir/runway_tasks.json with its id, status and credits.
"""
import argparse, base64, concurrent.futures as cf, io, json, os, sys, threading, time
import urllib.error, urllib.request

BASE = "https://api.dev.runwayml.com"
VERSION = "2024-11-06"
IMAGE = {"gemini_image3_pro": ("2048:2048", 20), "gemini_image3.1_flash": ("2048:2048", 11),
         "seedream5_pro": ("2048:2048", 9), "gen4_image": ("1080:1080", 8)}
VIDEO = {"gen4.5": 12, "gen4_turbo": 5}
LOCK = threading.Lock()


class NoKey(Exception):
    pass


def call(method, path, body=None):
    headers = {"X-Runway-Version": VERSION}
    key = os.environ.get("RUNWAYML_API_SECRET")
    if key:
        headers["Authorization"] = "Bearer " + key
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    tries = 6
    for k in range(tries):
        req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:600]
            if e.code == 401:
                raise NoKey(text)
            # A POST is retried only on 429 (nothing was created); a GET on any transient error.
            transient = e.code == 429 or (method == "GET" and e.code >= 500)
            if transient and k < tries - 1:
                time.sleep(min(60, 5 * 2 ** k))
                continue
            raise RuntimeError(f"{method} {path} answered {e.code}: {text}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if method == "GET" and k < tries - 1:
                time.sleep(5 * (k + 1))
                continue
            raise RuntimeError(f"{method} {path} failed: {e}")


def wait(task_id, every=6, limit=1500):
    t0 = time.time()
    while True:
        t = call("GET", f"/v1/tasks/{task_id}")
        if t.get("status") in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return t
        if time.time() - t0 > limit:
            return dict(t, status="TIMEOUT")
        time.sleep(every)


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url), timeout=300) as r:
        return r.read()


def save_image(raw, path):
    from PIL import Image
    Image.open(io.BytesIO(raw)).convert("RGB").save(path, "PNG")


def data_uri(path, limit=3_300_000):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    for side, q in ((im.width, 92), (im.width, 85), (1536, 88), (1280, 85)):
        im2 = im if im.width <= side else im.resize((side, round(im.height * side / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im2.save(buf, "JPEG", quality=q)
        if buf.tell() <= limit:
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    raise RuntimeError(f"{path} will not fit in a data URI")


def load_shots(path, ids):
    shots = json.load(open(path))["shots"]
    if ids:
        want = [i.strip() for i in ids.split(",") if i.strip()]
        missing = [i for i in want if i not in {s["id"] for s in shots}]
        if missing:
            raise SystemExit(f"not in {path}: {', '.join(missing)}")
        shots = [s for s in shots if s["id"] in want]
    return shots


def record(outdir, rec):
    p = os.path.join(outdir, "runway_tasks.json")
    with LOCK:
        rows = json.load(open(p)) if os.path.exists(p) else []
        rows.append(rec)
        json.dump(rows, open(p, "w"), indent=1)


def balance():
    org = call("GET", "/v1/organization")
    return org.get("creditBalance"), org


def run(jobs, submit, outdir, parallel, download=True):
    """jobs: list of (shot, body, out_path, kind). Submits, waits, downloads (unless download is False), records."""
    def one(job):
        shot, body, out, kind = job
        rec = dict(kind=kind, id=shot["id"], model=body["model"], at=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        try:
            task = call("POST", submit, body)
            rec["task"] = task["id"]
            done = wait(task["id"])
            rec.update(status=done.get("status"), credits=(done.get("cost") or {}).get("credits"),
                       failure=done.get("failure"), failureCode=done.get("failureCode"))
            if done.get("status") == "SUCCEEDED" and not download:
                rec["url"] = done["output"][0]
            elif done.get("status") == "SUCCEEDED":
                raw = fetch(done["output"][0])
                if kind == "still":
                    save_image(raw, out)
                else:
                    open(out, "wb").write(raw)
                rec["file"] = out
        except NoKey:
            raise
        except Exception as e:
            rec.update(status=rec.get("status") or "ERROR", error=str(e)[:400])
        record(outdir, rec)
        note = rec.get("file") or ("output link recorded" if rec.get("url") else "") or rec.get("failure") or rec.get("error") or ""
        print(f"{rec['id']:<22} {rec.get('status'):<10} {str(rec.get('credits')):>5} credits  {note}", flush=True)
        return rec

    with cf.ThreadPoolExecutor(parallel) as ex:
        recs = list(ex.map(one, jobs))
    used = sum(r.get("credits") or 0 for r in recs)
    ok = sum(1 for r in recs if r.get("status") == "SUCCEEDED")
    print(f"done: {ok} of {len(recs)} succeeded, {used} credits used")
    return recs


def check_budget(est, budget, dry):
    print(f"estimate: {est} credits, budget {budget}")
    if est > budget:
        raise SystemExit("over budget, nothing submitted")
    if dry:
        raise SystemExit(0)
    bal, _ = balance()
    print(f"balance before: {bal} credits")
    if bal is not None and est > bal:
        raise SystemExit("not enough credits, nothing submitted")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["balance", "stills", "videos", "task", "links"])
    ap.add_argument("shots", nargs="?")
    ap.add_argument("outdir", nargs="?")
    ap.add_argument("--ids", default="")
    ap.add_argument("--budget", type=int, default=400)
    ap.add_argument("--image-model", default="gemini_image3_pro", choices=sorted(IMAGE))
    ap.add_argument("--model", default="gen4.5", choices=sorted(VIDEO))
    ap.add_argument("--seconds", type=int, default=4)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-download", action="store_true",
                    help="record each output link in runway_tasks.json instead of downloading it")
    ap.add_argument("--image-links", default="",
                    help="videos: JSON file mapping shot id to an approved still's https link, used instead of outdir/ID.png")
    a = ap.parse_args()
    if a.cmd == "links":
        # python3 runway_api.py links OUTDIR: latest succeeded output link per shot and kind, as JSON
        p = os.path.join(a.shots or ".", "runway_tasks.json")
        rows = json.load(open(p)) if os.path.exists(p) else []
        out = {}
        for r in rows:
            if r.get("status") == "SUCCEEDED" and r.get("url"):
                out.setdefault(r["kind"], {})[r["id"]] = r["url"]
        print(json.dumps(out, indent=1))
        return
    try:
        if a.cmd == "balance":
            bal, org = balance()
            tier = org.get("tier", {})
            print(json.dumps(dict(creditBalance=bal, maxMonthlyCreditSpend=tier.get("maxMonthlyCreditSpend")), indent=1))
            return
        if a.cmd == "task":
            print(json.dumps(call("GET", f"/v1/tasks/{a.shots}"), indent=1))
            return
        if not (a.shots and a.outdir):
            raise SystemExit("needs shots.json and outdir")
        os.makedirs(a.outdir, exist_ok=True)
        shots = load_shots(a.shots, a.ids)
        if a.cmd == "stills":
            ratio, price = IMAGE[a.image_model]
            check_budget(price * len(shots), a.budget, a.dry_run)
            jobs = [(s, dict(model=a.image_model, promptText=s["still"][:5500], ratio=ratio),
                     os.path.join(a.outdir, s["id"] + ".png"), "still") for s in shots]
            run(jobs, "/v1/text_to_image", a.outdir, a.parallel, download=not a.no_download)
        else:
            shots = [s for s in shots if s.get("video")]
            secs = {s["id"]: max(2, min(10, int(s.get("seconds") or a.seconds))) for s in shots}
            links = json.load(open(a.image_links)) if a.image_links else {}
            if links:
                shots = [s for s in shots if s["id"] in links]
                missing = []
            else:
                missing = [s["id"] for s in shots if not os.path.exists(os.path.join(a.outdir, s["id"] + ".png"))]
            if missing:
                raise SystemExit("no approved still for: " + ", ".join(missing))
            if not shots:
                raise SystemExit("no moving shots to make")
            check_budget(sum(VIDEO[a.model] * secs[s["id"]] for s in shots), a.budget, a.dry_run)

            def image(s):
                return links[s["id"]] if links else data_uri(os.path.join(a.outdir, s["id"] + ".png"))
            jobs = [(s, dict(model=a.model, promptImage=image(s),
                             promptText=s["motion"][:1000], ratio="960:960", duration=secs[s["id"]]),
                     os.path.join(a.outdir, s["id"] + ".mp4"), "video") for s in shots]
            run(jobs, "/v1/image_to_video", a.outdir, a.parallel, download=not a.no_download)
    except NoKey:
        raise SystemExit("Runway answered 401: no developer key reached it. The network secret for "
                         "api.dev.runwayml.com is missing on this environment (playbook, Runway section).")


if __name__ == "__main__":
    main()
