"""
brain.py: every call to Google Gemini. Nothing else may call the model.

Rules from the brief:
  6  thinking tokens eat the output budget, so switch thinking off where allowed
  7  negotiate settings with an ordered list of profiles; any HTTP 400 moves on
  8  probe models with a real call; never trust ListModels; never cache a
     discovery failure permanently; always record LAST_ERROR
  14 screen practitioner posts in one global pass, defaulting to keep, with a floor
  21 prompts describe the business generically
The key travels in a header, never in a URL, so it cannot leak into logs.
"""

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request

import config

BUILD = "2026-10-31.b1"

BASE = "https://generativelanguage.googleapis.com/v1beta"

PROFILES = [
    {"thinking_off": True,  "json_mime": True,  "headroom": 1},
    {"thinking_off": False, "json_mime": True,  "headroom": 4},
    {"thinking_off": True,  "json_mime": False, "headroom": 1},
    {"thinking_off": False, "json_mime": False, "headroom": 4},
]
FALLBACK_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash",
                   "gemini-flash-lite-latest", "gemini-flash-latest"]
DISCOVERY_RETRY_SECONDS = 120

LAST_ERROR = ""
MODEL = None
PROFILE = None
TALLY = {"calls": 0, "ok": 0, "failed": 0, "probes": 0}
_last_call = [0.0]
_last_discovery_fail = [0.0]
_lock = threading.Lock()


def _key():
    return os.environ.get("GEMINI_API_KEY", "").strip()


def _scrub(text):
    k = _key()
    text = str(text or "")
    return text.replace(k, "[key]") if k else text


def _set_error(msg):
    global LAST_ERROR
    LAST_ERROR = _scrub(msg)[:400]


def _http(url, payload=None, timeout=90):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                 headers={"Content-Type": "application/json",
                                          "x-goog-api-key": _key()})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _err_body(exc):
    try:
        body = exc.read().decode("utf-8", "replace")
        msg = json.loads(body).get("error", {}).get("message", body)
    except Exception:
        msg = ""
    return _scrub(f"HTTP {exc.code}: {msg}")[:300]


def _config(profile, max_tokens):
    cfg = {"temperature": 0.3, "maxOutputTokens": int(max_tokens)}
    if profile["json_mime"]:
        cfg["responseMimeType"] = "application/json"
    if profile["thinking_off"]:
        cfg["thinkingConfig"] = {"thinkingBudget": 0}
    return cfg


def _text_of(out):
    parts = (out.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def _rank(names):
    """Newest and cheapest first: higher version, then lite > flash > others."""
    def version(n):
        m = re.search(r"gemini-(\d+(?:\.\d+)?)", n)
        return float(m.group(1)) if m else 0.0

    def tier(n):
        if "flash-lite" in n:
            return 0
        if "flash" in n:
            return 1
        return 2

    usable = [n for n in names if "gemini" in n and not any(
        bad in n for bad in ("embedding", "tts", "image", "audio", "live", "vision",
                             "thinking", "exp", "preview-tts", "robotics", "computer-use",
                             "pro"))]
    return sorted(set(usable), key=lambda n: (-version(n), tier(n), len(n)))


def _list_models():
    try:
        out = _http(f"{BASE}/models?pageSize=200", timeout=30)
        names = [m["name"].split("/", 1)[-1] for m in out.get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
        return _rank(names)
    except Exception as exc:
        _set_error(f"ListModels failed: {type(exc).__name__}")
        return []


def _probe(name):
    """Call the model for real. Returns the first profile it accepts, or None."""
    for profile in PROFILES:
        payload = {"contents": [{"role": "user", "parts": [{"text":
                       'Reply with only this JSON: {"ok":true}'}]}],
                   "generationConfig": _config(profile, 1200 * profile["headroom"])}
        TALLY["probes"] += 1
        try:
            out = _http(f"{BASE}/models/{name}:generateContent", payload, timeout=60)
            if _text_of(out):
                return profile
            _set_error(f"{name}: empty reply with profile {profile}")
        except urllib.error.HTTPError as exc:
            _set_error(f"probe {name}: {_err_body(exc)}")
            if exc.code == 400:
                continue          # settings rejected: try a simpler profile
            if exc.code in (403, 404):
                return None       # model not usable at all
            continue
        except Exception as exc:
            _set_error(f"probe {name}: {type(exc).__name__}: {exc}")
            continue
    return None


def discover(force=False):
    """Find a working model. Success is cached; failure is retried later."""
    global MODEL, PROFILE
    if not _key():
        _set_error("GEMINI_API_KEY is not set")
        return None
    if MODEL and not force:
        return MODEL
    if (not force and _last_discovery_fail[0]
            and time.time() - _last_discovery_fail[0] < DISCOVERY_RETRY_SECONDS):
        return None
    candidates = _list_models()
    for fb in FALLBACK_MODELS:
        if fb not in candidates:
            candidates.append(fb)
    for name in candidates[:6]:
        profile = _probe(name)
        if profile:
            MODEL, PROFILE = name, profile
            _last_discovery_fail[0] = 0.0
            return MODEL
        time.sleep(1)
    _last_discovery_fail[0] = time.time()
    if not LAST_ERROR:
        _set_error("no model answered a probe")
    return None


# ---------------------------------------------------------------------------
# Calling
# ---------------------------------------------------------------------------
def _parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        a, b = text.find(open_c), text.rfind(close_c)
        if a != -1 and b > a:
            try:
                return json.loads(text[a:b + 1])
            except Exception:
                continue
    return None


def call(prompt, max_tokens=1500):
    """Send one prompt; return parsed JSON (dict or list) or None."""
    global PROFILE
    with _lock:
        if not discover():
            TALLY["failed"] += 1
            return None
        start = PROFILES.index(PROFILE) if PROFILE in PROFILES else 0
        for profile in PROFILES[start:]:
            for attempt in range(2):
                gap = config.MIN_GAP_SECONDS - (time.time() - _last_call[0])
                if gap > 0:
                    time.sleep(gap)
                _last_call[0] = time.time()
                TALLY["calls"] += 1
                payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                           "generationConfig": _config(profile, max_tokens * profile["headroom"])}
                try:
                    out = _http(f"{BASE}/models/{MODEL}:generateContent", payload)
                    text = _text_of(out)
                    if not text:
                        reason = (out.get("candidates") or [{}])[0].get("finishReason", "?")
                        _set_error(f"{MODEL}: empty reply (finishReason={reason})")
                        break                      # try the next profile
                    data = _parse_json(text)
                    if data is None:
                        _set_error(f"{MODEL}: reply was not JSON")
                        break
                    PROFILE = profile
                    TALLY["ok"] += 1
                    return data
                except urllib.error.HTTPError as exc:
                    _set_error(_err_body(exc))
                    if exc.code == 400:
                        break                      # next profile, whatever the text says
                    if exc.code == 429 and attempt == 0:
                        time.sleep(30)
                        continue
                    if exc.code >= 500 and attempt == 0:
                        time.sleep(5)
                        continue
                    TALLY["failed"] += 1
                    return None
                except Exception as exc:
                    _set_error(f"{type(exc).__name__}: {exc}")
                    if attempt == 0:
                        continue
                    TALLY["failed"] += 1
                    return None
        TALLY["failed"] += 1
        return None


def status():
    return {"key_set": bool(_key()), "model": MODEL, "profile": PROFILE,
            "last_error": LAST_ERROR, "tally": dict(TALLY)}


def test_call():
    """One real call for /test-ai."""
    t0 = time.time()
    model = discover(force=True)
    out = {"model": model, "profile": PROFILE, "reply": None, "error": LAST_ERROR,
           "seconds": 0.0}
    if model:
        reply = call('Reply with only this JSON: {"ok": true, "note": "short greeting"}', 200)
        out["reply"] = reply
        out["error"] = "" if reply else LAST_ERROR
    out["seconds"] = round(time.time() - t0, 1)
    return out


# ---------------------------------------------------------------------------
# The four jobs (Part 7)
# ---------------------------------------------------------------------------
def _lines(stories, limit, with_url=True):
    rows = []
    for i, s in enumerate(stories[:limit]):
        bits = [f"[{i}] {s.get('title', '')}", f"({s.get('source', '')}, {s.get('published', '')[:10]})"]
        if s.get("summary"):
            bits.append("- " + s["summary"][:220])
        rows.append(" ".join(bits))
    return "\n".join(rows)


def learn_vocab(headlines, known_terms):
    """Job 2: extract company, product and technology names nobody configured."""
    if not headlines:
        return [], {}
    known = ", ".join(sorted(known_terms)[:300])
    prompt = (
        f"You help maintain a keyword list for a news filter used by {config.BUSINESS_DESCRIPTION}.\n"
        "From the trade-press headlines below, list up to 40 NEW names of companies, products, "
        "instrument platforms, technologies or programmes in life-science tools, bioprocessing, "
        "genomics, analytical instruments, diagnostics or pharma services that are NOT already in "
        "the known list. Lowercase them. Skip generic words.\n"
        "Also list any of your new terms that are ordinary words or place names, each with 2-4 "
        "short lowercase phrases that would show the text is NOT about the company.\n"
        'Return JSON only: {"terms": ["..."], "ambiguous": {"term": ["blocker", "..."]}}\n\n'
        f"Known list (partial): {known}\n\nHeadlines:\n" + "\n".join(headlines))
    data = call(prompt, 1500)
    if not isinstance(data, dict):
        return [], {}
    terms, known_set = [], {k.lower() for k in known_terms}
    for t in data.get("terms", []) or []:
        t = str(t).strip().lower()
        if 3 <= len(t) <= 40 and t not in known_set and t not in terms:
            terms.append(t)
    amb = {}
    for k, v in (data.get("ambiguous") or {}).items():
        k = str(k).strip().lower()
        if k in terms and isinstance(v, list):
            amb[k] = [str(b).lower() for b in v][:5]
    return terms[:40], amb


def spot_companies(stories, known_names):
    """Job 3: companies getting attention that are on no list."""
    if len(stories) < 10:
        return []
    prompt = (
        f"These are this week's industry stories for {config.BUSINESS_DESCRIPTION}.\n"
        "Name up to 8 companies that appear repeatedly or prominently but are NOT in the known list "
        "and are NOT large pharma customers. For each, say in under 15 words why it is getting "
        "attention, and give the indices of the stories that mention it.\n"
        'Return JSON only: {"companies": [{"name": "...", "why": "...", "stories": [0, 3]}]}\n\n'
        f"Known list: {', '.join(known_names)}\n\nStories:\n{_lines(stories, 120)}")
    data = call(prompt, 1200)
    out = []
    if isinstance(data, dict):
        for c in data.get("companies", []) or []:
            if isinstance(c, dict) and c.get("name"):
                idx = [i for i in c.get("stories", []) if isinstance(i, int) and 0 <= i < len(stories)]
                out.append({"name": str(c["name"])[:60], "why": str(c.get("why", ""))[:160],
                            "urls": [stories[i]["url"] for i in idx][:5]})
    return out[:8]


def screen_voice(posts):
    """Job 1: one global pass over every post (rule 14). Default to keeping.
    Returns (kept_posts, dropped_count)."""
    if not posts:
        return [], 0
    kept = []
    for start in range(0, len(posts), config.SCREEN_BATCH):
        batch = posts[start:start + config.SCREEN_BATCH]
        listing = "\n".join(
            f"[{i}] {p.get('source', '')}: {p.get('title', '')} - {p.get('summary', '')[:200]}"
            for i, p in enumerate(batch))
        prompt = (
            "Below are public posts by scientists and lab staff. Keep any post that is plausibly "
            "about laboratory work, lab instruments, reagents, consumables, bioprocessing, "
            "sequencing, diagnostics labs, lab software, vendors, service, pricing, procurement, "
            "or careers and conditions in labs. DEFAULT TO KEEPING. Drop a post only if it is "
            "clearly about something else (games, sport, a person or place that shares a brand "
            "name, unrelated hobbies).\n"
            'Return JSON only: {"drop": [indices to drop]}\n\n' + listing)
        data = call(prompt, 600)
        drop = set()
        if isinstance(data, dict):
            drop = {i for i in data.get("drop", []) or [] if isinstance(i, int)}
        elif data is None:
            drop = set()                     # model failed: keep the batch
        kept += [p for i, p in enumerate(batch) if i not in drop]
    if len(kept) < len(posts) * config.VOICE_SCREEN_FLOOR:
        seen = {p.get("url") for p in kept}
        kept += [p for p in posts if p.get("url") not in seen]
    return kept, len(posts) - len(kept)


def write_brief(region_label, segment_label, stories, rivals):
    """Job 4: the analyst read for one cell."""
    rival_lines = "\n".join(f"- {r.get('rival', '')}: {r.get('title', '')}" for r in rivals[:10])
    prompt = (
        f"You are a market analyst writing for {config.BUSINESS_DESCRIPTION}.\n"
        f"Cell: region = {region_label}; segment = {segment_label}.\n"
        "Using ONLY the stories below, write what is actually happening. Be concrete: name "
        "companies, places and policies from the stories. Do not invent facts or numbers. If the "
        "stories do not form a pattern, say so plainly.\n"
        "Return JSON only, in this shape:\n"
        '{"read": "2-4 sentences", "implications": ["2-3 short bullets on what it means for an '
        'instruments, reagents and bioprocessing supplier"], "watch": "the one thing to watch next", '
        '"titles": ["the 3 most decision-relevant headlines, copied exactly"], '
        '"indices": [their story indices]}\n\n'
        f"Stories:\n{_lines(stories, config.STORIES_PER_BRIEF)}\n\n"
        f"Recent competitor moves (context only):\n{rival_lines or '- none'}")
    data = call(prompt, 1400)
    if not isinstance(data, dict) or not data.get("read"):
        return None
    idx = [i for i in data.get("indices", []) or [] if isinstance(i, int) and 0 <= i < len(stories)]
    titles = [stories[i]["title"] for i in idx][:3] or [str(t) for t in data.get("titles", [])][:3]
    return {
        "read": str(data.get("read", ""))[:1200],
        "implications": [str(x)[:300] for x in (data.get("implications") or [])][:4],
        "watch": str(data.get("watch", ""))[:300],
        "titles": titles,
        "urls": [stories[i]["url"] for i in idx][:3],
        "model": MODEL,
    }


def write_voice_brief(region_label, posts):
    """Job 4b: a short read for the practitioner panel."""
    listing = "\n".join(f"- {p.get('source', '')}: {p.get('title', '')} - {p.get('summary', '')[:160]}"
                        for p in posts[:40])
    prompt = (
        f"You summarise what working scientists and lab buyers are saying, for {config.BUSINESS_DESCRIPTION}.\n"
        f"Region: {region_label}. Using ONLY the posts below, give the recurring complaints or "
        "praise (service, pricing, downtime, software, procurement, sales behaviour, products). "
        "Do not invent anything.\n"
        'Return JSON only: {"read": "2-3 sentences", "themes": ["short theme", "..."]}\n\n' + listing)
    data = call(prompt, 800)
    if not isinstance(data, dict) or not data.get("read"):
        return None
    return {"read": str(data["read"])[:800],
            "themes": [str(t)[:120] for t in (data.get("themes") or [])][:5]}
