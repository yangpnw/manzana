#!/usr/bin/env python3
"""Publish a rendered report into the GitHub Pages site folder.

  python3 publish.py [--force] <report_dir> <site_dir>

<report_dir> is output/<base>/ holding <base>.html (from render.py), any translations
<base>.<code>.html for the languages in languages.json, and images/NN.jpg.
Safety guard: when <site_dir> is inside a git repo, publishing is refused unless that repo is on
`main` with no uncommitted changes to tracked files outside docs/ and themes-used.md, so a dev
branch or half-finished edit never reaches the live site. --force skips the check. A <site_dir>
outside any repo (a scratch copy for testing) is never blocked.
Writes, under <site_dir>:
  reports/<base>/index.html         the report in the main language
  reports/<base>/<code>/index.html  each translation (shares the images below), with a language switcher
  reports/<base>/images/NN.jpg      strips resized for the web (no originals)
  index.html                  copy of the newest report (by <base> name), so the home page is always the latest
  archive.html                every published report, newest first, with links to its translations
Rerunning for the same <base> replaces that report.
"""
import glob, html, os, posixpath, re, shutil, subprocess, sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import CSS, PAGE  # noqa: E402
import langs as L  # noqa: E402

WEB_WIDTH = 1280  # 2x the page's ~630px image column: sharp on retina, small to download
PUBLISH_BRANCH = "main"
ALLOWED_DIRTY = ("docs/", "skills/daily-fun-facts/themes-used.md")  # what a daily run itself changes


def git(site, *args):
    r = subprocess.run(["git", "-C", site, *args], capture_output=True, text=True)
    return r.stdout.rstrip() if r.returncode == 0 else None  # keep leading spaces: porcelain status codes


def check_safe_to_publish(site):
    """Refuse to publish from a dev branch or a working tree with unfinished edits."""
    if git(site, "rev-parse", "--is-inside-work-tree") != "true":
        return  # scratch site folder for testing: nothing live to protect
    problems = []
    branch = git(site, "branch", "--show-current")
    if branch != PUBLISH_BRANCH:
        problems.append(f"on branch '{branch or 'detached HEAD'}', not '{PUBLISH_BRANCH}'")
    status = git(site, "status", "--porcelain", "--untracked-files=no") or ""
    dirty = [line[3:] for line in status.splitlines() if not line[3:].startswith(ALLOWED_DIRTY)]
    if dirty:
        problems.append("uncommitted changes outside docs/: " + ", ".join(dirty))
    if problems:
        raise SystemExit("publish refused (development in progress?):\n  - " + "\n  - ".join(problems)
                         + "\nFinish or stash the work and switch to main, or rerun with --force.")


def lang_dir(lang, langs):
    """'' for the main language, '<code>/' for a translation (relative to reports/<base>/)."""
    return "" if lang is L.main_lang(langs) else lang["code"] + "/"


def site_nav(lang, langs, available, root, base):
    """Language switcher (only when the sheet has translations) plus the 'All sheets' link."""
    here = f"reports/{base}/{lang_dir(lang, langs)}"
    links = []
    if len(available) > 1:
        for other in available:
            name = html.escape(other["name"])
            if other is lang:
                links.append(f'<span aria-current="page">{name}</span>')
            else:
                href = posixpath.relpath(f"reports/{base}/{lang_dir(other, langs)}", here) + "/"  # "./", "zh-hans/", "../"
                links.append(f'<a href="{href}" hreflang="{other["html_lang"]}" lang="{other["html_lang"]}">{name}</a>')
    switch = f'<span class="lang-switch">{" · ".join(links)}</span>' if links else ""
    return (f'<nav class="site-nav">{switch}'
            f'<a href="{root}archive.html">{html.escape(lang["all_sheets"])}</a></nav>')


def page(report_html, nav, root, img_prefix=""):
    """Add the favicon and site nav to a rendered report; img_prefix moves its image links."""
    out = report_html.replace("</head>", f'<link rel="icon" type="image/svg+xml" href="{root}favicon.svg">\n</head>', 1)
    out = out.replace("<main>\n", f"<main>\n{nav}\n", 1)
    if img_prefix:
        out = out.replace('src="images/', f'src="{img_prefix}images/')
    return out


ABSOLUTE = ("http:", "https:", "//", "/", "#", "data:", "mailto:")


def rebase_links(page_html, from_dir):
    """Rewrite relative href/src links of a page living in from_dir so it works from the site root."""
    def fix(m):
        attr, url = m.group(1), m.group(2)
        if not url or url.startswith(ABSOLUTE):
            return m.group(0)
        new = posixpath.normpath(posixpath.join(from_dir, url))
        if new == ".":
            new = "./"
        elif url.endswith("/") or url in (".", "./"):
            new += "/"
        return f'{attr}="{new}"'
    return re.sub(r'\b(href|src)="([^"]*)"', fix, page_html)


def save_web_images(report_dir, dest):
    os.makedirs(os.path.join(dest, "images"))
    for src in sorted(glob.glob(os.path.join(report_dir, "images", "[0-9][0-9].jpg"))):
        im = Image.open(src).convert("RGB")
        if im.width > WEB_WIDTH:
            im = im.resize((WEB_WIDTH, round(im.height * WEB_WIDTH / im.width)), Image.LANCZOS)
        im.save(os.path.join(dest, "images", os.path.basename(src)), quality=82, optimize=True, progressive=True)


def write_archive(site, langs, reports):
    main = L.main_lang(langs)
    items = []
    for d in reports:
        t = re.search(r"<title>(.*?)</title>", open(os.path.join(site, "reports", d, "index.html"), encoding="utf-8").read())
        title = t.group(1) if t else d
        extra = [f'<a href="reports/{d}/{l["code"]}/" hreflang="{l["html_lang"]}" lang="{l["html_lang"]}">{html.escape(l["name"])}</a>'
                 for l in langs[1:] if os.path.exists(os.path.join(site, "reports", d, l["code"], "index.html"))]
        langs_html = f'<span class="langs">{"".join(extra)}</span>' if extra else ""
        items.append(f'<li><a class="sheet" href="reports/{d}/"><span class="date">{d[:10]}</span>{title}</a>{langs_html}</li>')
    body = (f'<nav class="site-nav"><a href="./">{html.escape(main["latest_sheet"])}</a></nav>\n'
            f'<h1>🌍 {html.escape(main["archive_title"])}</h1>\n<ul class="archive">' + "".join(items) + "</ul>")
    archive = PAGE.format(lang=main["html_lang"], title=html.escape(main["archive_title"]), css=CSS, body=body)
    archive = archive.replace("</head>", '<link rel="icon" type="image/svg+xml" href="favicon.svg">\n</head>', 1)
    open(os.path.join(site, "archive.html"), "w", encoding="utf-8").write(archive)
    print("archive:", len(reports), "report(s)")


def main():
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    if len(args) != 2:
        raise SystemExit(__doc__)
    report_dir, site = (os.path.abspath(a) for a in args)
    if not force:
        check_safe_to_publish(site)
    langs = L.load()
    base = os.path.basename(report_dir.rstrip("/"))
    available = [l for l in langs if os.path.exists(os.path.join(report_dir, base + L.suffix(l, langs) + ".html"))]
    if L.main_lang(langs) not in available:
        raise SystemExit(f"missing {os.path.join(report_dir, base + '.html')}: run render.py first")
    missing = [l["code"] for l in langs if l not in available]
    if missing:
        print("note: no translation for", ", ".join(missing), "(publishing the languages that exist)")

    dest = os.path.join(site, "reports", base)
    shutil.rmtree(dest, ignore_errors=True)
    save_web_images(report_dir, dest)
    for lang in available:
        sub = lang_dir(lang, langs)
        root = "../../" + ("../" if sub else "")
        src = open(os.path.join(report_dir, base + L.suffix(lang, langs) + ".html"), encoding="utf-8").read()
        out_dir = os.path.join(dest, sub)
        os.makedirs(out_dir, exist_ok=True)
        nav = site_nav(lang, langs, available, root, base)
        open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(page(src, nav, root, "../" if sub else ""))
        print("wrote", os.path.join(dest, sub) if sub else dest, f"({lang['code']})")

    reports = sorted((d for d in os.listdir(os.path.join(site, "reports"))
                      if os.path.exists(os.path.join(site, "reports", d, "index.html"))), reverse=True)
    latest = reports[0]
    latest_html = open(os.path.join(site, "reports", latest, "index.html"), encoding="utf-8").read()
    open(os.path.join(site, "index.html"), "w", encoding="utf-8").write(rebase_links(latest_html, f"reports/{latest}/"))
    print("home page ->", latest)
    write_archive(site, langs, reports)


if __name__ == "__main__":
    main()
