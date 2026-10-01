#!/usr/bin/env python3
"""Render a fun-facts Markdown report to a styled HTML page in the Claude Docs look.

  python3 render.py <report_dir> [--credits]

Reads <report_dir>/<name>.md (the only .md in the folder) and writes <name>.html next to it.
Image links stay relative (images/NN.jpg), so the folder works as-is on any static website.
The line right after the H1, if it is a bare YYYY-MM-DD date, is shown as a date chip.
--credits adds a collapsible "Photo credits" footer built from credits.json.
"""
import datetime, glob, html, json, os, re, sys

import markdown

CSS = """
:root {
  --bg: #faf9f5; --page: #ffffff; --text: #1f1e1d; --muted: #6b6a66; --rule: #e8e6dc;
  --chip-bg: #f0eee6; --chip-text: #3d3929; --accent: #c96442; --shadow: 0 1px 3px rgba(31,30,29,.06);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #1f1e1d; --page: #262624; --text: #f5f4ef; --muted: #a3a29c; --rule: #3a3936;
    --chip-bg: #34332f; --chip-text: #e8e6dc; --accent: #d97757; --shadow: none;
  }
}
:root[data-theme="dark"] {
  --bg: #1f1e1d; --page: #262624; --text: #f5f4ef; --muted: #a3a29c; --rule: #3a3936;
  --chip-bg: #34332f; --chip-text: #e8e6dc; --accent: #d97757; --shadow: none;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.65 "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}
main {
  max-width: 760px; margin: 40px auto; padding: 56px 64px 64px;
  background: var(--page); border: 1px solid var(--rule); border-radius: 16px; box-shadow: var(--shadow);
}
h1, h2, h3 { font-family: "Source Serif 4", "Tiempos Text", Georgia, serif; font-weight: 600; line-height: 1.25; }
h1 { font-size: 2.25rem; margin: 0 0 12px; letter-spacing: -0.01em; }
h2 { font-size: 1.45rem; margin: 0 0 16px; }
h3 { font-size: 1.2rem; margin: 0 0 10px; }
p { margin: 0 0 14px; }
strong { font-weight: 600; }
a { color: var(--accent); }
hr { border: 0; border-top: 1px solid var(--rule); margin: 36px 0; }
img { display: block; width: 100%; height: auto; border-radius: 12px; margin: 4px 0 20px; }
.chip {
  display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
  background: var(--chip-bg); color: var(--chip-text); font-size: 0.85rem; font-weight: 500;
}
.chip svg { width: 14px; height: 14px; }
.site-nav { display: flex; justify-content: flex-end; margin: -24px 0 16px; font-size: 0.85rem; }
.site-nav a { color: var(--muted); text-decoration: none; }
.site-nav a:hover { color: var(--accent); }
ul.archive { list-style: none; padding: 0; margin: 24px 0 0; }
ul.archive li { border-top: 1px solid var(--rule); }
ul.archive a { display: flex; gap: 16px; padding: 14px 0; color: var(--text); text-decoration: none; }
ul.archive a:hover { color: var(--accent); }
ul.archive .date { color: var(--muted); font-variant-numeric: tabular-nums; flex: none; }
details.credits { margin-top: 40px; color: var(--muted); font-size: 0.8rem; line-height: 1.5; }
details.credits summary { cursor: pointer; font-weight: 500; }
details.credits ol { padding-left: 1.4em; }
details.credits a { color: inherit; }
@media (max-width: 720px) {
  main { margin: 0; padding: 32px 16px 40px; border: 0; border-radius: 0; }
  h1 { font-size: 1.75rem; }
  h2 { font-size: 1.25rem; }
}
@media print {
  body { background: #fff; color: #000; }
  main { margin: 0; padding: 0; max-width: none; border: 0; box-shadow: none; }
  hr { margin: 20px 0; }
  h2, img { break-after: avoid; }
  details.credits, .site-nav { display: none; }
}
"""

CAL = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">'
       '<rect x="2" y="3" width="12" height="11" rx="2"/><path d="M2 6.5h12M5.5 1.5v3M10.5 1.5v3"/></svg>')

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def date_chip(md_text):
    """Swap a bare YYYY-MM-DD line right after the H1 for a chip placeholder."""
    m = re.search(r"\A(#[^\n]*\n+)(\d{4}-\d{2}-\d{2})[ \t]*\n", md_text)
    if not m:
        return md_text, None
    d = datetime.date.fromisoformat(m.group(2))
    chip = f'<p><span class="chip">{CAL}{d.strftime("%b")} {d.day}, {d.year}</span></p>\n'
    return md_text[:m.start(2)] + "CHIP_PLACEHOLDER\n" + md_text[m.end():], chip


def credits_html(report_dir):
    path = os.path.join(report_dir, "credits.json")
    if not os.path.exists(path):
        return ""
    items = []
    for nn, photos in sorted(json.load(open(path)).items()):
        for p in photos:
            name = html.escape(p["file"].removeprefix("File:"))
            lic = html.escape(p["license"])
            if p.get("license_url"):
                lic = f'<a href="{html.escape(p["license_url"])}">{lic}</a>'
            items.append(f'<li>#{int(nn)}: <a href="{html.escape(p["source"])}">{name}</a>'
                         f' by {html.escape(p["author"] or "unknown")}, {lic}</li>')
    return ('<details class="credits"><summary>Photo credits (Wikimedia Commons)</summary><ol>'
            + "".join(items) + "</ol></details>")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    report_dir = args[0]
    mds = glob.glob(os.path.join(report_dir, "*.md"))
    if len(mds) != 1:
        raise SystemExit(f"expected exactly one .md in {report_dir}, found {len(mds)}")
    md_text, chip = date_chip(open(mds[0], encoding="utf-8").read())
    body = markdown.markdown(md_text, extensions=["extra", "sane_lists"])
    if chip:
        body = body.replace("<p>CHIP_PLACEHOLDER</p>\n", chip)
    if "--credits" in sys.argv:
        body += "\n" + credits_html(report_dir)
    h1 = re.search(r"^#\s+(.+)$", md_text, flags=re.M)
    title = re.sub(r"^[^\w]+", "", h1.group(1)).strip() if h1 else "Top 10"
    out = os.path.splitext(mds[0])[0] + ".html"
    open(out, "w", encoding="utf-8").write(PAGE.format(title=html.escape(title), css=CSS, body=body))
    print("wrote", out)


if __name__ == "__main__":
    main()
