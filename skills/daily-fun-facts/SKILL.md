---
name: daily-fun-facts
description: Make a printable "Top 10" fun-facts sheet on an obscure theme as a local Markdown + styled HTML report, with 10 illustrated entries (real, freely licensed photos) and a closing fun fact. Use when the user asks for today's fun facts, a daily fact sheet, a Top 10 printable, or runs /daily-fun-facts (optionally with a theme).
---

# Daily Top 10 Fun Facts

Produces one local report per day (Markdown, styled HTML and PDF) in a fixed format that the user has approved. **Do not change the format.** Only the theme and content change. The format was revised on 2026-09-30, so sheets logged before that date in `themes-used.md` use the old layout; this file is the authority.

**Where it runs:** local Claude Code with network access. `<repo>` is `~/Desktop/code/manzana`, the GitHub Pages repo behind https://dailyfunfacts.app/ (Pages serves `<repo>/docs`, custom domain in `docs/CNAME`). `<home>` is `<repo>/skills/daily-fun-facts`: always read and write `themes-used.md` and `output/` there. `<skill>` is the folder this SKILL.md was loaded from; it is installed via the symlink `~/.claude/skills/daily-fun-facts` → `<home>`, so normally they are the same folder.

## 1. Pick the theme

- If the user named a theme (in the args or message), use it.
- Otherwise read `<home>/themes-used.md` and offer 4 fresh, obscure themes with AskUserQuestion, each with 3–4 example items. Never repeat a used theme. Good themes are specific and visual: things that photograph well (festivals, creatures, buildings, foods, objects, places, rituals, machines).
- Before committing, check that most candidate items actually have photos on Commons. Swap an item for a comparable one when fewer than 3 real photos exist, and tell the user about any swap.

## 2. The frozen format

```
# 🌍 Top 10 <Theme>
YYYY-MM-DD                            (date alone on its line; the HTML shows it as a chip)

---                                   (horizontal rule)
## 1. <flag or fitting emoji> <The surprising fact as a short sentence>
                                      (e.g. "🇦🇺 The thorny devil drinks through its skin" —
                                       name the thing in the heading, under ~10 words)
![<alt>](images/NN.jpg)               (ONE image: a strip of 3 real photos side by side)
<2–4 short paragraphs, 1–3 sentences each: how it works, step by step, with one
 concrete number or date put in human terms. Bold at most one or two key phrases.>
<Takeaway: one line, its own paragraph, comparing it to something everyday>
---
... entries 2–10, same shape ...
### Fun fact
<3–4 sentences: a surprising true story connected to one of the entries that also
 points toward a NEW theme the reader could explore next (it seeds tomorrow's idea)>
```

Must NOT include: a "photos are real" disclaimer line, photo credits, a sources list, a "strangest ones" recap, the author mention, label lines like "Where:" or "Odd detail:", or any other extra section. Use flag emojis for country-tied items; for regions with emoji flags (England, Scotland, Wales) use those. When the place matters and the heading doesn't say it, mention it in the first sentence.

Content rules: every fact must be verifiable. Pull the Wikipedia extract for each item (the MediaWiki API with `prop=extracts&explaintext=1` via curl), and state only what the sources support. If curl can't reach Wikipedia, use web search or web fetch on the item's Wikipedia page instead.

Voice: explain it like a friend who just learned something wild and wants you to get it.

- Plain everyday words. If a technical or local term is the thing's real name, keep it and explain it in the same sentence: "its cloaca (the single rear opening for waste and eggs)."
- Cause and effect, not a list of facts: "the grooves pull water along → it reaches the mouth → it drinks without dipping its head."
- Put every number in human terms: "about 25 mL, roughly 15% of his body weight," "as tall as a 10-story building."
- Short conversational openers are welcome: "This isn't ordinary poop." / "And here's the twist."
- End each entry with the takeaway line: the strange fact in a familiar image ("It's sweating, but with poop."). Vary its lead-in ("Basically," "Think of it as," "In other words," or none) and don't reuse one lead-in more than twice per sheet.
- No academic filler ("notably," "renowned for," "is characterized by," "remarkably"). Before filling each entry, reread it and swap any word a general reader would need to look up.

Example entry (match this voice and shape):

> ## 2. 🏜️ A male sandgrouse carries water to his chicks in his feathers
> ![Sandgrouse](images/02.jpg)
> Male sandgrouse fly to a distant watering hole, soak their belly feathers, and fly back to the nest. The feathers hold about **25 mL of water**, roughly 15% of the bird's body weight.
>
> The chicks then drink straight from their dad's wet belly. Tiny strands on those feathers uncoil when wet and form a sponge-like mesh that holds the water instead of letting it drip off.
>
> Think of it as a built-in water bottle with wings.

## Naming and output (fixed, never vary)

Work these out once, before writing anything, and use them everywhere:

- **`<date>`**: today as `YYYY-MM-DD`.
- **`<seq>`**: a two-digit run number for that date, always present: `01`, or the next free number if `<home>/output/` already has a folder for `<date>`.
- **`<slug>`**: `top-10-` + the theme in lowercase ASCII, accents removed, `&` → `and`, any other run of non-alphanumerics → `-`, no leading/trailing `-`, at most 60 chars total (cut at a word boundary). No emoji. Example: "Odd Festivals Around the World" → `top-10-odd-festivals-around-the-world`.
- **`<base>`** = `<date>-<seq>-<slug>`, e.g. `2026-09-29-01-top-10-odd-festivals-around-the-world`. Sorting names alphabetically sorts by date, then by run.

Each sheet gets its own folder in `<home>/output/`, named for its `<base>`:

```
output/
  <base>/
    <base>.md                    the report; image links are images/NN.jpg
    <base>.html                  styled page (Claude Docs look), from scripts/render.py
    <base>.pdf                   printable copy, printed from the HTML
    credits.json                 author, license and Commons link for every photo
    images/01.jpg … 10.jpg       the 3-photo strips shown in the sheet
    images/originals/NN-a.jpg    the source photos (a, b, c per entry), up to 1280px wide
```

All files and folders are lowercase with no spaces, so the folder can be uploaded to a website exactly as it is. Nothing in it links back to Wikimedia, so it keeps working if the Commons files change. Most Commons photos are CC BY or CC BY-SA: a public page must show the credits from `credits.json`. `render.py --credits` adds them as a small collapsible footer in the HTML; the Markdown and the PDF stay credit-free. Never rename or overwrite an existing `<base>` folder.

## Network check (do this before anything else)

Run `curl -s -o /dev/null -w "%{http_code}" "https://commons.wikimedia.org/w/api.php?action=query&format=json&meta=siteinfo"`. If it doesn't return `200`, stop and tell the user Wikimedia is unreachable (offline, VPN or proxy), and ask whether to retry or make a text-only sheet now. For text-only, leave out the image lines and don't mention photos in the doc.

## 3. Build it

Everything is local: no Claude Docs or online artifacts. Let `O` = `<home>/output/<base>`.

1. **Facts**: pull each item's Wikipedia extract (see *Content rules*) and note the numbers and details you'll use.
2. **Photos** (work in the session scratchpad dir; run every `photos.py` command from there so `candidates.json` stays next to `plan.json`):
   - `python3 <skill>/scripts/photos.py search --source all "<query>" "<query>" ...` searches all 10 items across every source at once, in parallel:
     - `commons` (Wikimedia Commons, ids `File:…`)
     - `openverse` (Creative Commons photos from Flickr, museums and more, `ov:…`)
     - `met` and `aic` (public-domain museum objects, `met:…`, `aic:…`)
     - `inat` (research-grade CC photos of species, `inat:…`; query by species name)
     Use specific queries (species or object + place); if results are thin, try local-language names. Use `--source commons,openverse` and so on to narrow it.
   - **Only freely licensed photos**: the site is public, so use only what these sources return. Never use Getty, stock sites, or images found through general web search: they're copyrighted.
   - Choose photos that show the thing itself (not a logo, map, diagram or unrelated file). Write `plan.json` as `{"1": ["File:…", "ov:…", "met:…", "inat:…", "File:…"], …}` with **4–5 candidates per entry**, best first. Each strip uses the first 3 that download, so a blocked photo is skipped automatically.
   - `python3 <skill>/scripts/photos.py build <builddir> plan.json` writes `images/`, `credits.json` and `sheet.jpg`. It never waits long: a failed download is skipped and the next candidate used. Downloads are cached in `<builddir>/.cache`, so reruns take seconds. Exit code 2 means an entry ran out of candidates: add more and rerun.
   - **Read `sheet.jpg` and look at it.** Reorder or replace dark, blurry, badly cropped, off-topic or inappropriate photos, then rerun.
3. **Write the report**: create `O`, copy `<builddir>/images/` and `<builddir>/credits.json` into it (not `.cache` or `sheet.jpg`), and write `O/<base>.md` in the frozen format. Reread it against the voice rules and the sources before moving on.
4. **Render**: `python3 <skill>/scripts/render.py O --credits` writes `O/<base>.html`. Leave out `--credits` only if the user says the page won't be public.
5. **PDF** (if Google Chrome is installed): `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=5000 --print-to-pdf=O/<base>.pdf "file://O/<base>.html"`. Without Chrome, skip it and tell the user to print the HTML from a browser.
6. **Check it**: screenshot the HTML the same way (`--screenshot=<scratchpad>/shot.png --window-size=1100,1500`) and look at it.
7. Append a line to `<home>/themes-used.md`: `- YYYY-MM-DD · <Theme> · <base>`.
8. **Publish to the site**: `python3 <skill>/scripts/publish.py O <repo>/docs`. It writes `docs/reports/<base>/` (the page plus strips resized to 1280px; no originals, PDF or Markdown), makes `docs/index.html` a copy of the newest report, and rebuilds `docs/archive.html`. Screenshot `docs/index.html` through a local server (`python3 -m http.server` in `docs/`) and look at it.
9. **Commit and push** from `<repo>`, staging only these paths:
   `git add docs/ skills/daily-fun-facts/themes-used.md && git commit -m "Daily fun facts: <date> <Theme>" && git pull --rebase && git push`.
   `output/` is gitignored and stays local. If the push fails, stop and show the error; never force-push.
10. Hand off in one short line: https://dailyfunfacts.app/ updates about a minute after the push (GitHub Pages caches pages for up to 10 minutes, so a hard refresh may be needed). Mention any swapped items.
