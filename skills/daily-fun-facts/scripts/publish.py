#!/usr/bin/env python3
"""Publish a rendered report into the GitHub Pages site folder.

  python3 publish.py <report_dir> <site_dir>

<report_dir> is output/<base>/ holding <base>.html (from render.py) and images/NN.jpg.
Writes, under <site_dir>:
  reports/<base>/index.html   the report page
  reports/<base>/images/NN.jpg  strips resized for the web (no originals)
  index.html                  copy of the newest report (by <base> name), so the home page is always the latest
  archive.html                every published report, newest first
Rerunning for the same <base> replaces that report.
"""
import glob, os, re, shutil, sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import CSS, PAGE  # noqa: E402

WEB_WIDTH = 1280  # 2x the page's ~630px image column: sharp on retina, small to download


def nav(prefix):
    """Favicon link and the small 'All sheets' link, with paths relative to the page."""
    return (f'<link rel="icon" type="image/svg+xml" href="{prefix}favicon.svg">\n</head>',
            f'<main>\n<nav class="site-nav"><a href="{prefix}archive.html">All sheets</a></nav>\n')


def page(report_html, prefix, img_prefix=""):
    head, top = nav(prefix)
    out = report_html.replace("</head>", head, 1).replace("<main>\n", top, 1)
    if img_prefix:
        out = out.replace('src="images/', f'src="{img_prefix}images/')
    return out


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    report_dir, site = (os.path.abspath(a) for a in sys.argv[1:])
    base = os.path.basename(report_dir.rstrip("/"))
    src_html = os.path.join(report_dir, base + ".html")
    if not os.path.exists(src_html):
        raise SystemExit(f"missing {src_html}: run render.py first")

    dest = os.path.join(site, "reports", base)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(os.path.join(dest, "images"))
    for src in sorted(glob.glob(os.path.join(report_dir, "images", "[0-9][0-9].jpg"))):
        im = Image.open(src).convert("RGB")
        if im.width > WEB_WIDTH:
            im = im.resize((WEB_WIDTH, round(im.height * WEB_WIDTH / im.width)), Image.LANCZOS)
        im.save(os.path.join(dest, "images", os.path.basename(src)), quality=82, optimize=True, progressive=True)
    report_html = open(src_html, encoding="utf-8").read()
    open(os.path.join(dest, "index.html"), "w", encoding="utf-8").write(page(report_html, "../../"))
    print("wrote", dest)

    reports = sorted((d for d in os.listdir(os.path.join(site, "reports"))
                      if os.path.exists(os.path.join(site, "reports", d, "index.html"))), reverse=True)
    latest = reports[0]
    latest_html = open(os.path.join(site, "reports", latest, "index.html"), encoding="utf-8").read()
    latest_html = latest_html.replace('href="../../', 'href="').replace('src="images/', f'src="reports/{latest}/images/')
    open(os.path.join(site, "index.html"), "w", encoding="utf-8").write(latest_html)
    print("home page ->", latest)

    items = []
    for d in reports:
        t = re.search(r"<title>(.*?)</title>", open(os.path.join(site, "reports", d, "index.html"), encoding="utf-8").read())
        title = t.group(1) if t else d
        items.append(f'<li><a href="reports/{d}/"><span class="date">{d[:10]}</span>{title}</a></li>')
    body = ('<nav class="site-nav"><a href="./">Latest sheet</a></nav>\n'
            '<h1>🌍 All Top 10 sheets</h1>\n<ul class="archive">' + "".join(items) + "</ul>")
    archive = PAGE.format(title="All Top 10 sheets", css=CSS, body=body)
    archive = archive.replace("</head>", '<link rel="icon" type="image/svg+xml" href="favicon.svg">\n</head>', 1)
    open(os.path.join(site, "archive.html"), "w", encoding="utf-8").write(archive)
    print("archive:", len(reports), "report(s)")


if __name__ == "__main__":
    main()
