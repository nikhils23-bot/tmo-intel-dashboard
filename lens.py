"""
lens.py: relevance scoring, region routing and segment routing.

It imports nothing but `re` and `config`. It does no network calls and keeps
no state between calls (apart from a regex cache). That is what lets
test_lens.py cover it completely.
"""

import re

import config

BUILD = "2026-10-31.b1"

_WORD_RE = {}
_CASE_RE = {}

LEAVES = [r for r in config.REGIONS if r["type"] == "leaf"]
LEAF_KEYS = [r["key"] for r in LEAVES]
APAC_LEAVES = {r["key"] for r in LEAVES if r.get("parent") == "apac"}
REGION_ORDER = [r["key"] for r in config.REGIONS]
SEGMENT_ORDER = [s["key"] for s in config.SEGMENTS]

THRESHOLDS = {
    "specialist": config.SPECIALIST_THRESHOLD,
    "general": config.KEEP_THRESHOLD,
    "search": config.SEARCH_THRESHOLD,
    "rival": config.RIVAL_THRESHOLD,
}

_TEXT_BANDS = ["TECHNOLOGY", "CUSTOMER_MOVES", "REGULATION", "MARKET_STRUCTURE",
               "DEMAND_SHIFTS", "SUPPLY_CHAIN", "SEGMENT_BASE", "BUSINESS_VERBS",
               "NOISE"]
_SOURCE_BANDS = ["REPUTABLE_PRESS", "WEAK_PUBLISHERS"]
_COMPETITOR_TERMS = [t for c in config.COMPETITORS for t in c["terms"]]


# ---------------------------------------------------------------------------
# Matching primitives (rules 1 and 4)
# ---------------------------------------------------------------------------
def _pattern(term):
    """Whole-word regex for short single words; None means plain substring."""
    if term in _WORD_RE:
        return _WORD_RE[term]
    term = term.strip()
    if len(term) <= 8 and " " not in term:
        pat = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")
    else:
        pat = None
    _WORD_RE[term] = pat
    return pat


def _present(text, term):
    pat = _pattern(term)
    if pat is not None:
        return bool(pat.search(text))
    return term in text


def _blocked(text, term, extra=None):
    blockers = config.AMBIGUOUS_TERMS.get(term)
    if extra and term in extra:
        blockers = list(blockers or []) + list(extra[term])
    return bool(blockers) and any(b in text for b in blockers)


def hit(text, term, extra=None):
    """True if term appears in (lowercased) text and no blocker is present."""
    return _present(text, term) and not _blocked(text, term, extra)


def hits(text, terms, extra=None):
    """Every distinct term from `terms` that hits."""
    seen = []
    for term in terms:
        if term not in seen and hit(text, term, extra):
            seen.append(term)
    return seen


def _match(text, terms):
    """True if any term appears in text. Empty term list means match-all.
    Kept with the brief's name and contract; ambiguity blockers apply."""
    if not terms:
        return True
    return any(hit(text, t) for t in terms)


def _case_hits(raw):
    out = set()
    for term, label in config.CASE_SENSITIVE_TERMS.items():
        pat = _CASE_RE.get(term)
        if pat is None:
            pat = _CASE_RE[term] = re.compile(r"(?<![\w.])" + re.escape(term) + r"(?![\w])")
        if pat.search(raw):
            out.add(label)
    return out


# ---------------------------------------------------------------------------
# Relevance (Part 6)
# ---------------------------------------------------------------------------
def _band_points(weight, n):
    if n <= 0:
        return 0
    return weight if n == 1 else weight + int(weight / 2)


def score(title, summary="", source="", learned=(), extra_ambiguous=None):
    """Return (score, why). `why` lists the bands that fired, as BAND:term."""
    text = f"{title} {summary}".lower()
    src = (source or "").lower()
    total, why = 0, []

    def add(band, found):
        nonlocal total
        if found:
            total += _band_points(config.BAND_WEIGHTS[band], len(found))
            why.append(f"{band}:{found[0]}")

    add("SUBJECT", hits(text, config.SUBJECT_TERMS, extra_ambiguous))
    add("COMPETITORS", hits(text, _COMPETITOR_TERMS, extra_ambiguous))
    for band in _TEXT_BANDS:
        add(band, hits(text, config.BANDS[band], extra_ambiguous))
    for band in _SOURCE_BANDS:
        add(band, hits(src, config.BANDS[band]) if src else [])
    if learned:
        add("LEARNED", hits(text, [t.lower() for t in learned], extra_ambiguous))
    return total, why


def threshold(kind):
    return THRESHOLDS.get(kind, config.SEARCH_THRESHOLD)


def keep(points, kind):
    return points >= threshold(kind)


def near_miss(points, kind):
    bar = threshold(kind)
    return bar - config.NEAR_MISS_MARGIN <= points < bar


def competitors_named(title, summary=""):
    """Names (from config.COMPETITORS) mentioned in the text."""
    text = f"{title} {summary}".lower()
    return [c["name"] for c in config.COMPETITORS if hits(text, c["terms"])]


# ---------------------------------------------------------------------------
# Region routing (Part 2 routing rule, rules 2-4)
# ---------------------------------------------------------------------------
def _region_hit(geo_text, terms):
    for term in terms:
        if hit(geo_text, term):
            return True
    return False


def route_regions(title, summary="", home=None):
    """Return (regions, origins).

    regions: keys from config.REGIONS, in grid order.
    origins: outside-APMEA labels (US / Europe / LatAm), for the chip on World
             stories.
    `home` is the publication's home region. It applies only when the story
    itself names no APMEA market (rule 2). The publication name never enters
    geo_text.
    """
    raw = f"{title} {summary}"
    geo_text = raw.lower()

    leaves = [r["key"] for r in LEAVES if _region_hit(geo_text, r["terms"])]
    apac_wide = _region_hit(geo_text, config.APAC_WIDE_TERMS)
    if _region_hit(geo_text, config.APMEA_WIDE_TERMS):
        apac_wide = True
        if "mea" not in leaves:
            leaves.append("mea")

    if not leaves and not apac_wide and home:
        if home == "apac":
            apac_wide = True
        elif home in LEAF_KEYS:
            leaves = [home]

    regions = set(leaves)
    if apac_wide or any(l in APAC_LEAVES for l in leaves):
        regions.add("apac")
    if not regions:
        regions.add("global")
    elif _region_hit(geo_text, config.GLOBAL_MARKERS):
        regions.add("global")

    origins = set(_case_hits(raw))
    for label, terms in config.OUTSIDE_REGIONS.items():
        if _region_hit(geo_text, terms):
            origins.add(label)

    ordered = [k for k in REGION_ORDER if k in regions]
    return ordered, sorted(origins)


# ---------------------------------------------------------------------------
# Segment routing
# ---------------------------------------------------------------------------
def route_segments(title, summary="", source_hint=""):
    """Segments the story belongs to. Always includes "all". The publication
    name is allowed to help here (rule 2)."""
    cat_text = f"{title} {summary} {source_hint}".lower()
    out = ["all"]
    for seg in config.SEGMENTS:
        if seg["key"] == "all":
            continue
        if any(hit(cat_text, t) for t in seg["terms"]):
            out.append(seg["key"])
    return out


# ---------------------------------------------------------------------------
# Practitioner posts: deterministic pre-filter before the model screens them
# ---------------------------------------------------------------------------
def voice_prefilter(title, summary=""):
    """(keep, reason). Drops obvious off-topic posts, such as a gaming post
    that happens to contain a brand name."""
    text = f"{title} {summary}".lower()
    off = hits(text, config.VOICE_OFFTOPIC)
    if off:
        return False, f"off-topic:{off[0]}"
    ctx = hits(text, config.VOICE_LAB_CONTEXT)
    if not ctx:
        return False, "no lab context"
    return True, f"lab:{ctx[0]}"


def normalise_title(title):
    """For de-duplication: lowercase, publisher suffix and punctuation removed."""
    t = (title or "").lower()
    t = re.sub(r"\s+[-|–]\s+[^-|–]{2,60}$", "", t)
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()
