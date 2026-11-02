"""
streams.py: one function per source. Each returns a plain list of dicts.

Also holds the shared HTTP and feed helpers that collectors.py uses.
"""

import datetime as dt
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import feedparser

import config
import lens

BUILD = "2026-10-31.b1"

BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_TAG_RE = re.compile(r"<[^>]+>")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def http_get(url, headers=None, timeout=None):
    """Return (status, body_bytes, error_text). Never raises."""
    req = urllib.request.Request(url, headers=headers or {"User-Agent": BROWSER_UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout or config.HTTP_TIMEOUT) as resp:
            return resp.status, resp.read(), ""
    except urllib.error.HTTPError as exc:
        return exc.code, b"", f"HTTP {exc.code}"
    except Exception as exc:          # timeouts, DNS, TLS
        return 0, b"", type(exc).__name__ + ": " + str(exc)[:120]


def clean(text, limit=600):
    text = html.unescape(_TAG_RE.sub(" ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def iso(struct):
    if not struct:
        return ""
    try:
        return dt.datetime(*struct[:6], tzinfo=dt.timezone.utc).isoformat()
    except Exception:
        return ""


def gn_url(query, edition="US", window=None):
    q = f"{query} {window or config.SEARCH_WINDOW}".strip()
    params = config.GN_EDITIONS.get(edition, config.GN_EDITIONS["US"])
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(q) + "&" + params


def fetch_feed(url, headers=None):
    """Fetch and parse an RSS/Atom feed. Returns (items, status_dict)."""
    status, body, err = http_get(url, headers=headers)
    info = {"url": url, "status": status, "items": 0, "error": err}
    if status != 200 or not body:
        if not err:
            info["error"] = f"HTTP {status}" if status else "empty response"
        return [], info
    parsed = feedparser.parse(body)
    items = []
    for e in parsed.entries:
        title = clean(e.get("title", ""), 300)
        source = ""
        src = e.get("source")
        if isinstance(src, dict):
            source = src.get("title", "")
        elif src is not None:
            source = getattr(src, "title", "") or ""
        if source and title.endswith(" - " + source):
            title = title[: -(len(source) + 3)]
        summary = clean(e.get("summary", "") or e.get("description", ""))
        # Google News summaries are just the headline again; drop them.
        if summary.lower().startswith(title.lower()[:40]):
            summary = ""
        items.append({
            "title": title,
            "summary": summary,
            "url": e.get("link", ""),
            "source": source,
            "published": iso(e.get("published_parsed") or e.get("updated_parsed")),
        })
    info["items"] = len(items)
    if not items and parsed.bozo:
        info["error"] = "not a valid feed"
    return items, info


# ---------------------------------------------------------------------------
# Competitors
# ---------------------------------------------------------------------------
def _one_competitor(comp):
    items, info = fetch_feed(gn_url(comp["query"], "US"))
    for it in items:
        it["rival"] = comp["name"]
        it["rival_segment"] = comp["segment"]
    info["name"] = comp["name"]
    return items, info


def collect_competitors(progress=None):
    starred = [c for c in config.COMPETITORS if c.get("star")]
    out, report = [], []
    with ThreadPoolExecutor(max_workers=config.RIVAL_WORKERS) as pool:
        for i, (items, info) in enumerate(pool.map(_one_competitor, starred), 1):
            out += items
            report.append(info)
            if progress:
                progress(i, len(starred))
    return out, report


# ---------------------------------------------------------------------------
# Reddit (rule 9): RSS only, budgeted, spaced, gives up
# ---------------------------------------------------------------------------
_reddit_budget = [0]
_reddit_429s = [0]
_reddit_started = [0.0]


def _reddit_exhausted():
    if _reddit_budget[0] >= config.REDDIT_MAX_REQUESTS:
        return True
    if _reddit_429s[0] >= config.REDDIT_GIVE_UP_AFTER:
        return True
    if _reddit_started[0] and time.time() - _reddit_started[0] > config.REDDIT_TIME_LIMIT:
        return True
    return False


def _reddit_request(url):
    headers = {"User-Agent": config.REDDIT_USER_AGENT}
    _reddit_budget[0] += 1
    items, info = fetch_feed(url, headers=headers)
    if info["status"] == 429:
        _reddit_429s[0] += 1
        if _reddit_exhausted():
            return items, info
        time.sleep(config.REDDIT_RETRY_SLEEP)
        _reddit_budget[0] += 1                 # retry the SAME url once
        items, info = fetch_feed(url, headers=headers)
        if info["status"] == 429:
            _reddit_429s[0] += 1
        else:
            _reddit_429s[0] = 0
    else:
        _reddit_429s[0] = 0
    return items, info


def collect_reddit_rss(progress=None):
    _reddit_budget[0], _reddit_429s[0], _reddit_started[0] = 0, 0, time.time()
    subs = "+".join(config.REDDIT_SUBS)
    out, report, seen = [], [], set()
    for i, q in enumerate(config.REDDIT_QUERIES, 1):
        if _reddit_exhausted():
            report.append({"query": q, "status": "skipped", "items": 0,
                           "error": "budget exhausted"})
            continue
        url = (f"https://www.reddit.com/r/{subs}/search.rss?"
               + urllib.parse.urlencode({"q": q, "restrict_sr": "on",
                                         "sort": "new", "t": "month"}))
        items, info = _reddit_request(url)
        info["query"] = q
        report.append(info)
        for it in items:
            if it["url"] in seen:
                continue
            seen.add(it["url"])
            m = re.search(r"/r/([^/]+)/", it["url"])
            it["source"] = f"r/{m.group(1)}" if m else "Reddit"
            it["platform"] = "reddit"
            it["fallback_region"] = None
            out.append(it)
        if progress:
            progress(i, len(config.REDDIT_QUERIES))
        if i < len(config.REDDIT_QUERIES) and not _reddit_exhausted():
            time.sleep(config.REDDIT_SPACING)
    return out, report


# ---------------------------------------------------------------------------
# YouTube Data API v3
# ---------------------------------------------------------------------------
def collect_youtube(progress=None):
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        return [], [{"query": "-", "status": "skipped", "items": 0,
                     "error": "YOUTUBE_API_KEY not set"}]
    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=config.NEWS_WINDOW_DAYS))
    after = after.strftime("%Y-%m-%dT%H:%M:%SZ")
    out, report, seen = [], [], set()
    for i, spec in enumerate(config.YOUTUBE_QUERIES, 1):
        params = {"part": "snippet", "type": "video", "q": spec["q"],
                  "maxResults": config.YOUTUBE_MAX_RESULTS, "order": "relevance",
                  "publishedAfter": after, "relevanceLanguage": "en", "key": key}
        if spec.get("regionCode"):
            params["regionCode"] = spec["regionCode"]
        url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
        status, body, err = http_get(url, headers={"User-Agent": BROWSER_UA})
        info = {"query": spec["q"], "status": status, "items": 0, "error": err}
        if status == 200:
            try:
                data = json.loads(body)
                for v in data.get("items", []):
                    vid = (v.get("id") or {}).get("videoId")
                    if not vid or vid in seen:
                        continue
                    seen.add(vid)
                    sn = v.get("snippet", {})
                    out.append({
                        "title": clean(sn.get("title", ""), 300),
                        "summary": clean(sn.get("description", "")),
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "source": "YouTube: " + clean(sn.get("channelTitle", ""), 80),
                        "published": sn.get("publishedAt", ""),
                        "platform": "youtube",
                        "fallback_region": spec.get("region"),
                    })
                    info["items"] += 1
            except Exception as exc:
                info["error"] = "bad JSON: " + type(exc).__name__
        elif status == 403:
            info["error"] = "HTTP 403 (quota used up, or the API is not enabled for this key)"
        report.append(info)
        if progress:
            progress(i, len(config.YOUTUBE_QUERIES))
    return out, report


def collect_reviews(progress=None):
    """Placeholder kept for parity with the F&B build (rule 16). No review
    sites are scraped in this industry: see Part 4d of the brief."""
    return [], []
