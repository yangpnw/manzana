# Manzana - Top 10 Daily Fun Facts

A static, printable "Top 10" fun-facts sheet, published daily at https://dailyfunfacts.app/.

## How it works

- **Site**: GitHub Pages serves [docs/](docs/) from `main` (custom domain in [docs/CNAME](docs/CNAME)). There is no build step and no backend.
  - `docs/index.html`: the latest sheet (the home page)
  - `docs/archive.html`: every sheet, newest first
  - `docs/reports/<base>/`: one folder per sheet (`index.html` plus web-sized `images/`)
- **Generator**: the Claude Code skill in [skills/daily-fun-facts/](skills/daily-fun-facts/). It picks a theme, checks facts against Wikipedia, builds photo strips from Wikimedia Commons, writes the sheet as Markdown, renders it to HTML, publishes it into `docs/`, then commits and pushes.

`<base>` is `YYYY-MM-DD-NN-top-10-<theme-slug>`, so folders sort by date.

## Make today's sheet

1. Install the skill once: `ln -sfn "$PWD/skills/daily-fun-facts" ~/.claude/skills/daily-fun-facts`
2. In Claude Code, run `/daily-fun-facts` (optionally with a theme).

The skill does the rest, including `git push`. The site updates about a minute later.

## Scripts (in `skills/daily-fun-facts/scripts/`)

| Script | What it does |
| --- | --- |
| `photos.py` | Search Commons; build 3-photo strips, originals and `credits.json` (downloads are cached) |
| `render.py` | Markdown → styled, printable HTML (Claude Docs look; light/dark; `--credits` adds photo credits) |
| `publish.py` | Copy a rendered sheet into `docs/`, resize images to 1280px, refresh the home page and archive |

Full-size working files (original photos, PDF, cache) stay in `skills/daily-fun-facts/output/`, which is gitignored.

Requires Python 3 with `Pillow` and `markdown` (`pip install pillow markdown`).
