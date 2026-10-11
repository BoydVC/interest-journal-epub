# Interest Journal EPUB

Turns recent **Interest Journal** markdown on the box into a clean **EPUB** + in-browser chapter reader for iPhone Books offline. TokenMax burn · port **4313**.

Chapters are **real excerpts** from `/workspace/ij_*.md` and `interest-journal*` folders (truncated chapters labeled).

## Screens

1. **Cover** — book face + download EPUB  
2. **Contents** — TOC from real filenames/dates, filter by kind  
3. **Reader** — chapter view (markdown → HTML)  
4. **About** — source paths on the box  

Hash routes: `#cover` · `#toc` · `#reader` · `#about` · `#ch/<id>`

## Run

```bash
./run.sh          # build + serve http://127.0.0.1:4313/
./run.sh --shots  # + screenshots/
```

Offline single file: `dist/interest-journal-epub.html`  
EPUB: `dist/interest-journal.epub` (also at `/dist/interest-journal.epub`)

## Layout

- `web/` — index.html, app.css, app.js  
- `data/chapters.json` — real excerpts embedded into dist  
- `build.py` packs EPUB (stdlib `zipfile` + XHTML) and offline HTML  
- `server.py` / `tests/screenshot.sh`


---
## Repo notes
- **Built:** Oct 2026 (TokenMax build week; see SHORTLIST/ledger), by TokenMax (Boyd's Grok Bot) on the Grok Bot box.
- **Run:** `./run.sh` (then open the localhost URL it prints).
- Imported from `/workspace/tokenmax/interest-journal-epub` on Oct 23, 2026. node_modules, virtualenvs, logs and files over 20 MB were left out.
