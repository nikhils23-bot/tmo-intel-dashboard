"""
app.py: Flask routes, diagnostic pages and the scan lock.

Start command (Render):
  gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 600
One worker matters: the scan state and the wrong-password counter live in memory.
"""

import datetime as dt
import hashlib
import hmac
import html
import os
import re
import sys
import threading
import time

from flask import (Flask, abort, jsonify, redirect, render_template,
                   render_template_string, request, send_from_directory, session,
                   url_for)
from jinja2 import ChoiceLoader, FileSystemLoader
from werkzeug.exceptions import HTTPException

import brain
import collectors
import config
import lens
import streams

BUILD = "2026-10-31.b1"

BASE = os.path.dirname(os.path.abspath(__file__))

# Rule 17: tolerate a flat upload.
app = Flask(__name__, static_folder=None)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(BASE, "templates")),
    FileSystemLoader(BASE),
])

SERVABLE = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg",
            ".ico", ".woff", ".woff2", ".ttf", ".webp"}

# Rule 20: the scan lock. Secret key derives from the password.
SCAN_PASSWORD = os.environ.get("SCAN_PASSWORD", "")
app.secret_key = hashlib.sha256(("tmo-intel-dashboard:" + (SCAN_PASSWORD or "unlocked")).encode()).hexdigest()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
MAX_WRONG = 5
LOCKOUT_SECONDS = 600
_wrong = {"count": 0, "until": 0.0}
_scan_lock = threading.Lock()

EXPECTED_FILES = ["config.py", "lens.py", "collectors.py", "streams.py", "brain.py",
                  "app.py", "base.html", "home.html", "view.html", "sources.html",
                  "style.css", "requirements.txt", "render.yaml", "test_lens.py"]

REGION_LABEL = {r["key"]: r["label"] for r in config.REGIONS}
SEGMENT_LABEL = {s["key"]: s["label"] for s in config.SEGMENTS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _find_file(name):
    """Where a project file is on disk, allowing for a flattened upload."""
    sub = {"html": "templates", "css": "static"}.get(name.rsplit(".", 1)[-1])
    candidates = [os.path.join(BASE, sub, name)] if sub else []
    candidates.append(os.path.join(BASE, name))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _stamp_of(name):
    path = _find_file(name)
    if not path:
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            m = re.search(r"BUILD\s*[=:]\s*[\"']?([0-9]{4}-[0-9]{2}-[0-9]{2}\.b\d+)", fh.read(4000))
        return m.group(1) if m else "no stamp"
    except Exception:
        return "unreadable"


def _lock_on():
    return bool(SCAN_PASSWORD)


def _unlocked():
    return not _lock_on() or session.get("scan_ok") is True


def _check_password(given):
    if time.time() < _wrong["until"]:
        return False, "Too many wrong guesses. Try again in a few minutes."
    if given and hmac.compare_digest(given.encode(), SCAN_PASSWORD.encode()):
        _wrong["count"] = 0
        return True, ""
    _wrong["count"] += 1
    if _wrong["count"] >= MAX_WRONG:
        _wrong.update(count=0, until=time.time() + LOCKOUT_SECONDS)
        return False, "Too many wrong guesses. Locked for ten minutes."
    return False, "Wrong password."


def _start_scan():
    with _scan_lock:
        if collectors.PROGRESS["running"]:
            return False
        collectors.PROGRESS["running"] = True          # claim before the thread starts
        collectors.PROGRESS["stage"] = "starting"
    threading.Thread(target=collectors.refresh, kwargs={"claimed": True}, daemon=True).start()
    return True


def _ago(iso_text):
    if not iso_text:
        return "never"
    days = collectors.age_days(iso_text)
    if days is None:
        return iso_text[:10]
    hours = days * 24
    if hours < 1:
        return f"{int(hours * 60)} min ago"
    if hours < 48:
        return f"{int(hours)} h ago"
    return f"{int(days)} days ago"


app.jinja_env.filters["ago"] = _ago
app.jinja_env.filters["date"] = lambda s: (s or "")[:10]


@app.context_processor
def _globals():
    return {"BUILD": BUILD, "REGIONS": config.REGIONS, "SEGMENTS": config.SEGMENTS,
            "REGION_LABEL": REGION_LABEL, "SEGMENT_LABEL": SEGMENT_LABEL,
            "PROGRESS": collectors.PROGRESS, "LOCK_ON": _lock_on()}


@app.before_request
def _auto_scan():
    """Free Render wipes data.json on restart; rebuild on the next home visit."""
    if request.endpoint != "home" or os.environ.get("AUTO_SCAN", "1") == "0":
        return
    if not os.path.exists(collectors.DATA_FILE) and not collectors.PROGRESS["running"]:
        _start_scan()


# ---------------------------------------------------------------------------
# Reader pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    data = collectors.load()
    return render_template("home.html", data=data, grid=data.get("grid") or {},
                           briefs=data.get("briefs") or {})


@app.route("/cell/<region>/<segment>")
def view(region, segment):
    if region not in REGION_LABEL or segment not in SEGMENT_LABEL:
        abort(404)
    data = collectors.load()
    stories = collectors.cell_items(data.get("news", []), region, segment)
    stories = sorted(stories, key=lambda s: s.get("published") or "", reverse=True)
    return render_template(
        "view.html", data=data, region=region, segment=segment,
        stories=stories[:config.MAX_PANEL_STORIES], total=len(stories),
        brief=(data.get("briefs") or {}).get(f"{region}:{segment}"),
        rivals=collectors.rivals_for(data.get("rivals", []), region, segment),
        voice=collectors.voice_for(data.get("voice", []), region, segment),
        voice_brief=(data.get("voice_briefs") or {}).get(region),
        min_stories=config.MIN_STORIES_FOR_BRIEF)


@app.route("/sources")
def sources():
    data = collectors.load()
    rep = data.get("report") or {}
    feeds = rep.get("feeds", [])
    dead = [f for f in feeds if f.get("status") != 200 or not f.get("items")]
    return render_template("sources.html", data=data, rep=rep, feeds=feeds, dead=dead,
                           ai=brain.status())


# ---------------------------------------------------------------------------
# Scan control (rule 20)
# ---------------------------------------------------------------------------
LOCK_FORM = """{% extends "base.html" %}{% block content %}
<section class="panel narrow"><h2>Run a scan</h2>
<p>A scan takes about 25 minutes and uses part of the day's free model and YouTube quota.</p>
{% if message %}<p class="warn">{{ message }}</p>{% endif %}
<form method="post" action="{{ url_for('refresh') }}">
<label>Password <input type="password" name="password" autofocus></label>
<button type="submit">Start scan</button></form></section>{% endblock %}"""


@app.route("/refresh", methods=["GET", "POST"])
def refresh():
    key = request.args.get("key", "")
    if key and _lock_on():                      # cron-job.org path
        ok, msg = _check_password(key)
        if not ok:
            return msg, 403
        started = _start_scan()
        return ("scan started" if started else "scan already running"), 202
    if request.method == "POST" and _lock_on():
        ok, msg = _check_password(request.form.get("password", ""))
        if not ok:
            return render_template_string(LOCK_FORM, message=msg), 403
        session["scan_ok"] = True
    if not _unlocked():
        return render_template_string(LOCK_FORM, message="")
    _start_scan()
    return redirect(url_for("scan"))


SCAN_PAGE = """{% extends "base.html" %}{% block content %}
<section class="panel"><h2>Scan</h2>
{% if p.running %}<meta http-equiv="refresh" content="10">{% endif %}
<p><b>Status:</b> {{ "running" if p.running else "idle" }} &middot;
<b>Stage:</b> {{ p.stage }} {% if p.total %}({{ p.done }} / {{ p.total }}){% endif %}</p>
<p><b>Started:</b> {{ p.started or "-" }} &middot; <b>Finished:</b> {{ p.finished or "-" }}</p>
{% if p.error %}<p class="warn"><b>Died with:</b> {{ p.error }}</p>{% endif %}
{% if not p.running %}<p><a class="button" href="{{ url_for('refresh') }}">Run scan now</a></p>{% endif %}
<pre class="log">{% for line in p.log %}{{ line }}
{% endfor %}</pre></section>{% endblock %}"""


@app.route("/scan")
def scan():
    return render_template_string(SCAN_PAGE, p=collectors.PROGRESS)


# ---------------------------------------------------------------------------
# Diagnostics (Part 11)
# ---------------------------------------------------------------------------
def _plain(title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<style>body{font:15px/1.5 system-ui,sans-serif;margin:24px;max-width:900px;color:#1d2433}"
            "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #dde;padding:6px 8px;"
            "text-align:left;vertical-align:top}.bad{color:#b42318;font-weight:600}.ok{color:#05603a}"
            "code{background:#f2f4f7;padding:1px 4px;border-radius:3px}</style></head><body>"
            f"<h1>{html.escape(title)}</h1>{body}"
            "<p><a href='/'>Home</a> &middot; <a href='/debug'>/debug</a> &middot; "
            "<a href='/features'>/features</a> &middot; <a href='/sources'>/sources</a></p></body></html>")


@app.route("/debug")
def debug():
    rows = []
    for name in EXPECTED_FILES:
        where = _find_file(name)
        cell = (f"<span class='ok'>found</span> <code>{html.escape(os.path.relpath(where, BASE))}</code>"
                if where else "<span class='bad'>MISSING</span>")
        rows.append(f"<tr><td>{name}</td><td>{cell}</td></tr>")
    env = {k: bool(os.environ.get(k)) for k in
           ("GEMINI_API_KEY", "YOUTUBE_API_KEY", "SCAN_PASSWORD", "AUTO_SCAN", "DATA_FILE")}
    env_rows = "".join(f"<tr><td>{k}</td><td>{'<span class=ok>set</span>' if v else 'not set'}</td></tr>"
                       for k, v in env.items())
    df = collectors.DATA_FILE
    exists = os.path.exists(df)
    size = os.path.getsize(df) if exists else 0
    ai = brain.status()
    body = (
        "<h2>Files</h2><table>" + "".join(rows) + "</table>"
        "<h2>Environment (values are never shown)</h2><table>" + env_rows + "</table>"
        f"<h2>State</h2><table><tr><td>Scan lock</td><td>{'on' if _lock_on() else 'off (SCAN_PASSWORD not set)'}</td></tr>"
        f"<tr><td>Data file</td><td><code>{html.escape(df)}</code>: {'exists, ' + str(size // 1024) + ' KB' if exists else 'not yet written'}</td></tr>"
        f"<tr><td>Scan</td><td>{html.escape(str(collectors.PROGRESS['stage']))} (running: {collectors.PROGRESS['running']})</td></tr>"
        f"<tr><td>AI model</td><td>{html.escape(str(ai['model'] or 'not discovered yet'))}</td></tr>"
        f"<tr><td>AI last error</td><td>{html.escape(ai['last_error'] or '-')}</td></tr>"
        f"<tr><td>Python</td><td>{html.escape(sys.version.split()[0])}</td></tr>"
        f"<tr><td>Base folder</td><td><code>{html.escape(BASE)}</code></td></tr></table>")
    return _plain("Debug", body)


@app.route("/features")
def features():
    modules = {"app.py": BUILD, "config.py": config.BUILD, "lens.py": lens.BUILD,
               "collectors.py": collectors.BUILD, "streams.py": streams.BUILD,
               "brain.py": brain.BUILD}
    for f in ("test_lens.py", "base.html", "home.html", "view.html", "sources.html", "style.css"):
        modules[f] = _stamp_of(f) or "MISSING"
    stamps = set(modules.values())
    verdict = ("<p class='ok'><b>All build stamps match.</b> What you uploaded is what is running.</p>"
               if len(stamps) == 1 else
               "<p class='bad'><b>BUILD STAMPS DO NOT MATCH.</b> Some files on GitHub are from a "
               "different release. Re-upload every file before debugging anything else.</p>")
    rows = "".join(f"<tr><td>{k}</td><td class='{'ok' if v == BUILD else 'bad'}'>{html.escape(str(v))}</td></tr>"
                   for k, v in modules.items())
    feats = ("<h2>Features in this build</h2><ul>"
             "<li>APMEA grid: World, Asia Pacific (rollup) + China, India &amp; South Asia, Rest of APAC; Middle East &amp; Africa</li>"
             "<li>Three panels per cell: industry signal, competitor watch, practitioner voice</li>"
             f"<li>{sum(1 for c in config.COMPETITORS if c.get('star'))} competitor searches; "
             f"{len(config.PUBLICATIONS)} site-scoped publications; {len(config.DIRECT_FEEDS)} direct feeds (unverified)</li>"
             "<li>Gemini: vocabulary learning, near-miss rescue, company spotting, post screening, briefs</li>"
             "<li>Scan lock with cron key; checkpoint saves after every brief</li></ul>")
    return _plain("Features", verdict + "<table>" + rows + "</table>" + feats)


@app.route("/test-ai")
def test_ai():
    res = brain.test_call()
    ok = bool(res.get("reply"))
    body = (f"<p class='{'ok' if ok else 'bad'}'><b>{'Model call succeeded' if ok else 'Model call failed'}</b></p>"
            "<table>"
            f"<tr><td>Key set</td><td>{brain.status()['key_set']}</td></tr>"
            f"<tr><td>Model</td><td>{html.escape(str(res.get('model')))}</td></tr>"
            f"<tr><td>Settings accepted</td><td>{html.escape(str(res.get('profile')))}</td></tr>"
            f"<tr><td>Reply</td><td><code>{html.escape(str(res.get('reply')))}</code></td></tr>"
            f"<tr><td>Exact error</td><td>{html.escape(res.get('error') or '-')}</td></tr>"
            f"<tr><td>Took</td><td>{res.get('seconds')} s</td></tr></table>")
    return _plain("Test AI", body)


FIND_PAGE = """{% extends "base.html" %}{% block content %}
<section class="panel"><h2>Find an item</h2>
<form method="get"><input name="q" value="{{ q }}" placeholder="words from a headline, or a URL" size="50">
<button type="submit">Find</button></form>
{% if q %}
<p>Collected and <b>kept</b>: {{ kept|length }} &middot; collected but <b>rejected</b>: {{ rejected|length }}
&middot; competitor panel: {{ rivals|length }} &middot; practitioner panel: {{ voice|length }}</p>
<p class="muted">Nothing anywhere means a collection problem. Rejected means a scoring problem. Kept but in the
wrong cell means a routing problem.</p>
{% for group, rows in [("Kept", kept), ("Competitor", rivals), ("Practitioner", voice), ("Rejected", rejected)] %}
{% if rows %}<h3>{{ group }}</h3><table class="tbl">
<tr><th>Headline</th><th>Source</th><th>Score</th><th>Filed into</th><th>Why</th></tr>
{% for r in rows[:50] %}<tr><td><a href="{{ r.url }}" target="_blank" rel="noopener">{{ r.title }}</a></td>
<td>{{ r.source }}</td><td>{{ r.score }}{% if r.kind %} / bar {{ bars.get(r.kind, "") }}{% endif %}</td>
<td>{{ (r.regions or [])|map("replace","global","World")|join(", ") }}{% if r.categories %} &times; {{ r.categories|join(", ") }}{% endif %}</td>
<td class="tags">{% for w in (r.why or []) %}<span class="tag">{{ w }}</span>{% endfor %}</td></tr>{% endfor %}
</table>{% endif %}{% endfor %}
{% endif %}</section>{% endblock %}"""


@app.route("/find")
def find():
    q = (request.args.get("q") or "").strip()
    data = collectors.load()
    match = lambda rows: [r for r in rows if q.lower() in (r.get("title", "") + " " + r.get("url", "")).lower()]
    return render_template_string(
        FIND_PAGE, q=q,
        kept=match(data.get("news", [])) if q else [],
        rivals=match(data.get("rivals", [])) if q else [],
        voice=match(data.get("voice", [])) if q else [],
        rejected=match(data.get("rejected", [])) if q else [],
        bars=lens.THRESHOLDS)


@app.route("/api/data")
def api_data():
    return jsonify(collectors.load())


@app.route("/healthz")
def healthz():
    return "ok", 200


@app.route("/static/<path:fname>")
def static_file(fname):
    if os.path.splitext(fname)[1].lower() not in SERVABLE or ".." in fname:
        abort(404)
    for folder in (os.path.join(BASE, "static"), BASE):
        if os.path.isfile(os.path.join(folder, fname)):
            return send_from_directory(folder, fname)
    abort(404)


# ---------------------------------------------------------------------------
# Catch-all error page: hand-written, because the commonest failure is a
# missing template.
# ---------------------------------------------------------------------------
@app.errorhandler(Exception)
def _on_error(exc):
    if isinstance(exc, HTTPException):
        if exc.code == 404:
            return _plain("Not found", "<p>No page at this address.</p>"), 404
        return exc
    found = "".join(
        f"<tr><td>{n}</td><td>{html.escape(os.path.relpath(p, BASE)) if (p := _find_file(n)) else '<span class=bad>MISSING</span>'}</td></tr>"
        for n in EXPECTED_FILES)
    body = (f"<p class='bad'><b>{html.escape(type(exc).__name__)}:</b> {html.escape(str(exc)[:500])}</p>"
            f"<p>Page: <code>{html.escape(request.path)}</code></p>"
            "<h2>What the server can see</h2><table>" + found + "</table>"
            "<p>If a template is missing, upload it (into <code>templates/</code> or the top folder; both work).</p>")
    return _plain("Something broke", body), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
