"""
collectors.py: runs a scan, classifies every item into cells, and saves.

Public: refresh(), classify(), load(), save(), age_days(), PROGRESS.
Order of a scan:
  1  news collection (feeds, site searches, theme searches) in parallel,
     with the Reddit collector running alongside because it is slow
  2  classify and de-duplicate
  3  competitor searches
  4  YouTube, then wait for Reddit
  5  SAVE (rule 12): everything above is now safe from a restart
  6  model work: vocabulary, rescue near misses, spot companies, screen posts,
     then one brief per populated cell, saving after each
"""

import datetime as dt
import json
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import brain
import config
import lens
import streams

BUILD = "2026-10-31.b1"

DATA_FILE = os.environ.get("DATA_FILE", "data.json")
_save_lock = threading.Lock()

PROGRESS = {
    "running": False, "stage": "idle", "done": 0, "total": 0,
    "started": None, "finished": None, "error": None, "log": [],
}

REGION_LABEL = {r["key"]: r["label"] for r in config.REGIONS}
SEGMENT_LABEL = {s["key"]: s["label"] for s in config.SEGMENTS}


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _log(msg):
    stamp = _now().strftime("%H:%M:%S")
    PROGRESS["log"].append(f"{stamp}  {msg}")
    PROGRESS["log"] = PROGRESS["log"][-80:]


def _stage(name, total=0):
    PROGRESS.update(stage=name, done=0, total=total)
    _log(f"stage: {name}")


def _tick(done, total):
    PROGRESS["done"], PROGRESS["total"] = done, total


def age_days(published):
    if not published:
        return None
    try:
        when = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=dt.timezone.utc)
        return (_now() - when).total_seconds() / 86400
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
_cache = {"mtime": None, "data": None}


def empty():
    return {"generated": None, "news": [], "rivals": [], "voice": [], "briefs": {},
            "voice_briefs": {}, "ranked_voice": [], "grid": {}, "totals": {},
            "report": {}, "rejected": [], "build": BUILD}


def load():
    try:
        mtime = os.path.getmtime(DATA_FILE)
    except OSError:
        return empty()
    if _cache["mtime"] == mtime and _cache["data"] is not None:
        return _cache["data"]
    try:
        with open(DATA_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        base = empty()
        base.update(data)
        _cache.update(mtime=mtime, data=base)
        return base
    except Exception:
        return empty()


def save(data):
    with _save_lock:
        folder = os.path.dirname(os.path.abspath(DATA_FILE))
        os.makedirs(folder, exist_ok=True)
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
def classify(item, kind, home=None, learned=(), extra_ambiguous=None):
    """Score and route one item. Returns (item, kept, near_miss)."""
    pts, why = lens.score(item["title"], item.get("summary", ""), item.get("source", ""),
                          learned, extra_ambiguous)
    regions, origins = lens.route_regions(item["title"], item.get("summary", ""), home)
    cats = lens.route_segments(item["title"], item.get("summary", ""), item.get("source", ""))
    out = dict(item, score=pts, why=why, regions=regions, categories=cats,
               origins=origins, kind=kind, home=home)
    out["rivals_named"] = lens.competitors_named(item["title"], item.get("summary", ""))
    return out, lens.keep(pts, kind), lens.near_miss(pts, kind)


def _jobs():
    """Every news request: (label, url, kind, home)."""
    jobs = []
    for f in config.DIRECT_FEEDS:
        jobs.append(("feed: " + f["name"], f["url"], f["kind"], f.get("home")))
    for p in config.PUBLICATIONS:
        q = f"site:{p['site']}"
        if p.get("topic"):
            q += " " + p["topic"]
        window = config.SPECIALIST_WINDOW if p["kind"] == "specialist" else config.SEARCH_WINDOW
        jobs.append(("site: " + p["name"], streams.gn_url(q, "US", window), p["kind"], p.get("home")))
    jobs.append(("search: subject", streams.gn_url(config.SUBJECT_QUERY, "US"), "search", None))
    for theme in config.GLOBAL_THEMES:
        jobs.append(("search: " + theme, streams.gn_url(theme, "US"), "search", None))
    for leaf in lens.LEAVES:
        key = leaf["key"]
        editions = [leaf.get("edition", "US")] + config.REGION_EXTRA_EDITIONS.get(key, [])
        for theme in config.REGION_THEMES.get(key, []):
            jobs.append((f"{key}: {theme}", streams.gn_url(theme, editions[0]), "search", None))
        for seg, words in config.SEGMENT_QUERY_WORDS.items():
            q = f"({leaf['search_name']}) {words}"
            jobs.append((f"{key}x{seg}", streams.gn_url(q, editions[0]), "search", None))
        for ed in editions[1:]:
            q = f"({leaf['search_name']}) (laboratory OR diagnostics OR biotech OR biomanufacturing OR genomics)"
            jobs.append((f"{key}@{ed}", streams.gn_url(q, ed), "search", None))
    return jobs


def _fetch_job(job):
    label, url, kind, home = job
    items, info = streams.fetch_feed(url)
    info.update(label=label, kind=kind, url=url if label.startswith("feed:") else "")
    return job, items, info


def _collect_news():
    jobs = _jobs()
    _stage("collecting trade press and searches", len(jobs))
    raw, report = [], []
    with ThreadPoolExecutor(max_workers=config.FEED_WORKERS) as pool:
        for i, (job, items, info) in enumerate(pool.map(_fetch_job, jobs), 1):
            _, _, kind, home = job
            for it in items:
                it["_kind"], it["_home"] = kind, home
                if not it.get("source"):
                    it["source"] = job[0].split(": ", 1)[-1] if job[0].startswith(("feed:", "site:")) else ""
            raw += items
            report.append(info)
            _tick(i, len(jobs))
    return raw, report


def _dedupe(items):
    seen, out = set(), []
    for it in items:
        key = lens.normalise_title(it.get("title", "")) or it.get("url")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _in_window(it):
    age = age_days(it.get("published"))
    return age is None or age <= config.NEWS_WINDOW_DAYS


def _sort_recent(items):
    return sorted(items, key=lambda x: x.get("published") or "", reverse=True)


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------
def cell_items(items, region, segment):
    return [i for i in items if region in i.get("regions", []) and segment in i.get("categories", [])]


def build_grid(news):
    grid = {}
    for r in config.REGIONS:
        grid[r["key"]] = {}
        for s in config.SEGMENTS:
            grid[r["key"]][s["key"]] = len(cell_items(news, r["key"], s["key"]))
    return grid


def rivals_for(rivals, region, segment):
    """Rule 18 fallback: region+segment, then region, then segment, then any
    (flagged as a global move)."""
    tiers = [
        [r for r in rivals if region in r["regions"] and segment in r["categories"]],
        [r for r in rivals if region in r["regions"]],
        [r for r in rivals if segment != "all" and (segment in r["categories"] or r.get("rival_segment") == segment)],
        rivals,
    ]
    out, seen = [], set()
    for level, tier in enumerate(tiers):
        for r in _sort_recent(tier):
            if r["url"] in seen:
                continue
            seen.add(r["url"])
            out.append(dict(r, global_move=level >= 2 and region not in r["regions"]))
            if len(out) >= config.MAX_PANEL_RIVALS:
                return out
    return out


def voice_for(voice, region, segment):
    tiers = [
        [v for v in voice if region in v["regions"] and segment in v["categories"]],
        [v for v in voice if region in v["regions"]],
        [v for v in voice if segment in v["categories"]],
    ]
    out, seen = [], set()
    for level, tier in enumerate(tiers):
        for v in _sort_recent(tier):
            if v["url"] in seen:
                continue
            seen.add(v["url"])
            out.append(dict(v, elsewhere=level == 2 and region not in v["regions"]))
            if len(out) >= config.MAX_PANEL_VOICE:
                return out
    return out


def brief_order():
    """World/All first, then roll-up and MEA totals, then leaves, then segments.
    If quota runs out mid-scan, the most important cells already have briefs."""
    regions = [r["key"] for r in config.REGIONS]
    segs = [s["key"] for s in config.SEGMENTS]
    first = [("global", "all"), ("apac", "all"), ("mea", "all")]
    rest = [(r, "all") for r in regions if (r, "all") not in first]
    rest += [(r, s) for r in regions for s in segs if s != "all"]
    return first + rest


# ---------------------------------------------------------------------------
# The scan
# ---------------------------------------------------------------------------
def refresh(include_voice=True, include_ai=True, claimed=False):
    """Run one full scan. `claimed` means the caller already set
    PROGRESS["running"] under its own lock (app.py does)."""
    if PROGRESS["running"] and not claimed:
        return False
    PROGRESS.update(running=True, started=_now().isoformat(), finished=None, error=None, log=[])
    try:
        _refresh(include_voice, include_ai)
        _stage("done")
    except Exception as exc:
        PROGRESS["error"] = f"{type(exc).__name__}: {exc}"
        _log("FAILED: " + PROGRESS["error"])
        _log(traceback.format_exc()[-600:])
    finally:
        PROGRESS.update(running=False, finished=_now().isoformat())
    return True


def _refresh(include_voice, include_ai):
    t0 = time.time()
    report = {"feeds": [], "rivals": [], "reddit": [], "youtube": [], "notes": [],
              "ai": {}, "learned": [], "learned_ambiguous": {}, "spotted": [],
              "screened_out": 0, "prefiltered_out": 0, "briefs_written": 0,
              "briefs_skipped_thin": 0, "rescued": 0, "timings": {}}

    # Reddit is slow by design (20s spacing), so it runs alongside collection.
    reddit_box = {"items": [], "report": []}
    reddit_thread = None
    if include_voice and config.REDDIT_ENABLED:
        def _reddit():
            try:
                reddit_box["items"], reddit_box["report"] = streams.collect_reddit_rss()
            except Exception as exc:
                reddit_box["report"] = [{"query": "-", "status": 0, "items": 0,
                                         "error": f"{type(exc).__name__}: {exc}"}]
        reddit_thread = threading.Thread(target=_reddit, daemon=True)
        reddit_thread.start()
    elif include_voice:
        report["notes"].append("Reddit switched off in config.py")

    # 1-2. News
    raw, report["feeds"] = _collect_news()
    report["timings"]["collect"] = round(time.time() - t0)
    _stage("classifying stories", len(raw))
    raw = [r for r in _dedupe(raw) if _in_window(r)]
    news, near, rejected = [], [], []
    for i, it in enumerate(raw, 1):
        kind, home = it.pop("_kind", "search"), it.pop("_home", None)
        out, kept, near_flag = classify(it, kind, home)
        if kept:
            news.append(out)
        else:
            (near if near_flag else rejected).append(out)
        if i % 200 == 0:
            _tick(i, len(raw))
    _log(f"{len(raw)} unique items, {len(news)} kept, {len(near)} near misses")

    # 3. Competitors
    _stage("competitor searches", sum(1 for c in config.COMPETITORS if c.get("star")))
    rival_raw, report["rivals"] = streams.collect_competitors(_tick)
    rivals = []
    for it in _dedupe([r for r in rival_raw if _in_window(r)]):
        out, kept, _ = classify(it, "rival")
        if kept and it["rival"] in out["rivals_named"]:
            rivals.append(out)
    _log(f"{len(rivals)} competitor stories kept")

    # 4. Practitioner voice
    voice = []
    if include_voice:
        _stage("YouTube", len(config.YOUTUBE_QUERIES))
        if config.YOUTUBE_ENABLED:
            yt, report["youtube"] = streams.collect_youtube(_tick)
            voice += yt
        rev, _ = streams.collect_reviews()
        voice += rev
        if reddit_thread:
            _stage("waiting for Reddit")
            reddit_thread.join(timeout=config.REDDIT_TIME_LIMIT + 120)
            voice += reddit_box["items"]
            report["reddit"] = reddit_box["report"]
    voice_kept = []
    for v in _dedupe(voice):
        ok, reason = lens.voice_prefilter(v["title"], v.get("summary", ""))
        if not ok:
            report["prefiltered_out"] += 1
            continue
        regions, origins = lens.route_regions(v["title"], v.get("summary", ""), v.get("fallback_region"))
        cats = lens.route_segments(v["title"], v.get("summary", ""))
        voice_kept.append(dict(v, regions=regions, origins=origins, categories=cats, why=[reason]))

    # 5. Save before any model call (rule 12)
    data = empty()
    data.update(generated=_now().isoformat(), news=_sort_recent(news), rivals=_sort_recent(rivals),
                voice=voice_kept, ranked_voice=voice_kept, report=report,
                rejected=[{k: r.get(k) for k in ("title", "url", "source", "score", "why", "regions", "kind")}
                          for r in (near + rejected)][:4000])
    data["near_misses"] = len(near)
    data["grid"] = build_grid(data["news"])
    data["totals"] = {"raw": len(raw), "news": len(news), "rivals": len(rivals),
                      "voice": len(voice_kept), "near_misses": len(near)}
    report["timings"]["pre_ai"] = round(time.time() - t0)
    save(data)
    _log("saved collection (before AI)")

    if not include_ai or not brain.discover():
        report["notes"].append("AI skipped: " + (brain.LAST_ERROR or "switched off"))
        report["ai"] = brain.status()
        save(data)
        return

    # 6a. Learn vocabulary, rescue near misses (rule 15)
    _stage("learning vocabulary")
    specialist = [n["title"] for n in news if n.get("kind") == "specialist"][: config.VOCAB_SAMPLE]
    known = set(lens._COMPETITOR_TERMS) | set(config.SUBJECT_TERMS)
    for band in ("TECHNOLOGY",):
        known |= set(config.BANDS[band])
    learned, learned_amb = brain.learn_vocab(specialist, known)
    report["learned"], report["learned_ambiguous"] = learned, learned_amb
    if learned:
        still_near = []
        for it in near:
            base = {k: it[k] for k in ("title", "summary", "url", "source", "published") if k in it}
            out, kept, _ = classify(base, it["kind"], it.get("home"), learned, learned_amb)
            if kept:
                out["why"].append("RESCUED")
                news.append(out)
                report["rescued"] += 1
            else:
                still_near.append(it)
        near = still_near
        news = _sort_recent(news)
        data.update(news=news, grid=build_grid(news))
        data["totals"]["news"] = len(news)
        _log(f"learned {len(learned)} terms, rescued {report['rescued']} stories")
    save(data)

    # 6b. Spot companies on no list (job 3)
    _stage("spotting new companies")
    ranked = sorted(news, key=lambda n: n.get("score", 0), reverse=True)
    report["spotted"] = brain.spot_companies(ranked[:120], [c["name"] for c in config.COMPETITORS])
    save(data)

    # 6c. Screen practitioner posts: one global pass (rule 14)
    if voice_kept:
        _stage("screening practitioner posts", len(voice_kept))
        screened, dropped = brain.screen_voice(voice_kept)
        report["screened_out"] = dropped
        data["voice"] = data["ranked_voice"] = screened
        data["totals"]["voice"] = len(screened)
        save(data)

    # 6d. Briefs, saving after each (rule 12)
    order = brief_order()
    _stage("writing briefs", len(order))
    written = 0
    for i, (reg, seg) in enumerate(order, 1):
        _tick(i, len(order))
        stories = cell_items(news, reg, seg)
        if len(stories) < config.MIN_STORIES_FOR_BRIEF:
            report["briefs_skipped_thin"] += 1
            continue
        if written >= config.MAX_BRIEFS:
            report["notes"].append(f"brief cap of {config.MAX_BRIEFS} reached")
            break
        stories = sorted(stories, key=lambda s: (s.get("score", 0), s.get("published") or ""),
                         reverse=True)
        brief = brain.write_brief(REGION_LABEL[reg], SEGMENT_LABEL[seg], stories,
                                  rivals_for(rivals, reg, seg))
        if brief:
            brief["n"] = len(stories)
            data["briefs"][f"{reg}:{seg}"] = brief
            written += 1
            report["briefs_written"] = written
            save(data)
        elif brain.LAST_ERROR and "429" in brain.LAST_ERROR:
            report["notes"].append("stopped writing briefs: daily model quota reached")
            break

    # 6e. Practitioner reads, one per region row
    _stage("practitioner reads", len(config.REGIONS))
    for i, r in enumerate(config.REGIONS, 1):
        _tick(i, len(config.REGIONS))
        posts = [v for v in data["voice"] if r["key"] in v["regions"]]
        if len(posts) < config.MIN_POSTS_FOR_VOICE_BRIEF:
            continue
        vb = brain.write_voice_brief(r["label"], posts)
        if vb:
            data["voice_briefs"][r["key"]] = vb
            save(data)

    report["ai"] = brain.status()
    report["timings"]["total"] = round(time.time() - t0)
    data["report"] = report
    save(data)
    _log(f"scan finished in {report['timings']['total']}s, {written} briefs")
