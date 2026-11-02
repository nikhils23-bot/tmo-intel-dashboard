# Life Science Tools Desk: APMEA

A weekly competitive-intelligence dashboard for the life-science tools industry,
focused on Asia Pacific, the Middle East and Africa. It is a Flask app that runs
on Render.

## Files

| File | What it is |
|---|---|
| `config.py` | Every list: regions, segments, publications, competitors, themes, name traps. **The only file to edit.** |
| `lens.py` | Relevance scoring and region/segment routing. No network. |
| `test_lens.py` | 159 regression cases. Run `python test_lens.py` before every upload. |
| `collectors.py` | Runs a scan and saves `data.json`. |
| `streams.py` | Competitor searches, Reddit, YouTube. |
| `brain.py` | Every Gemini call. |
| `app.py` | Pages, diagnostics, scan lock. |
| `templates/` | `base.html`, `home.html`, `view.html`, `sources.html` |
| `static/` | `style.css` |
| `requirements.txt`, `render.yaml` | Deployment. |

If GitHub's uploader flattens the `templates` and `static` folders, the app
still works.

## Environment variables (Render → Environment)

`GEMINI_API_KEY`, `YOUTUBE_API_KEY`, `SCAN_PASSWORD`, `PYTHON_VERSION=3.12.4`.
Optional: `AUTO_SCAN=0` stops the automatic scan after a restart;
`DATA_FILE` moves the data file to a mounted disk.

Never put a key in any file in this repository.

## After deploying, open in order

`/debug` → `/features` (all stamps must match) → `/test-ai` → `/` (Run scan
now) → `/scan` → `/sources`.

## Weekly scan

On cron-job.org, schedule `GET https://YOUR-LINK.onrender.com/refresh?key=YOUR-SCAN-PASSWORD`
for Monday 08:00.

## Known limits

- Direct feed addresses in `DIRECT_FEEDS` could not be checked during the
  build. The first scan's `/sources` page is the real check; delete the dead
  lines.
- English-language China coverage is thin. Chinese-language sources are out of
  scope for this version.
- Practitioner posts are mostly US- and Europe-based, so APMEA voice panels are
  often thin.
