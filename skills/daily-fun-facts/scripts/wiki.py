#!/usr/bin/env python3
"""Fetch Wikipedia text for fact-checking a fun-facts sheet, politely (see net.py).

  extract: python3 wiki.py extract <out_dir> "Title" ["Title" ...]
           Saves each article's plain-text extract to <out_dir>/<Title>.txt (redirects followed)
           and prints the resolved title and length. Already-saved titles are not fetched again.
  search:  python3 wiki.py search "query" ["query" ...]
           Prints the top 5 article titles for each query, to find the right title to extract.

Options (before the command's arguments): --lang xx  use xx.wikipedia.org (default en).

All requests share net.py's rules: a contact User-Agent, one Wikipedia request at a time about
1 s apart, Retry-After honoured on 429, and a stop after repeated 429s instead of hammering.
Use this instead of curl loops.
"""
import os, re, sys

from net import FetchError, getjson, wikimedia_blocked


def api(lang):
    return f"https://{lang}.wikipedia.org/w/api.php?"


def safe_name(title):
    return re.sub(r"[/\\:*?\"<>|\s]+", "_", title).strip("_") + ".txt"


def extract(out_dir, titles, lang="en"):
    os.makedirs(out_dir, exist_ok=True)
    for t in titles:
        path = os.path.join(out_dir, safe_name(t))
        if os.path.exists(path) and os.path.getsize(path) > 0:
            print(f"{t} -> (saved earlier) {os.path.getsize(path)} chars")
            continue
        try:
            d = getjson(api(lang), action="query", format="json", prop="extracts", explaintext=1,
                        redirects=1, titles=t)
        except FetchError as e:
            print(f"{t} -> FAILED: {str(e).splitlines()[-1].strip()}")
            continue
        page = next(iter(d.get("query", {}).get("pages", {}).values()), {})
        text = page.get("extract", "")
        if text:
            open(path, "w").write(text)
        print(f"{t} -> {page.get('title', '?')} {len(text)} chars" + ("" if text else "  (no article; try search)"))


def search(queries, lang="en"):
    for q in queries:
        try:
            d = getjson(api(lang), action="query", format="json", list="search", srlimit=5, srsearch=q)
            print(f"{q} => {[s['title'] for s in d['query']['search']]}")
        except FetchError as e:
            print(f"{q} => FAILED: {str(e).splitlines()[-1].strip()}")


if __name__ == "__main__":
    args, lang = sys.argv[1:], "en"
    if args[:1] == ["--lang"] and len(args) > 1:
        lang, args = args[1], args[2:]
    if len(args) >= 3 and args[0] == "extract":
        extract(args[1], args[2:], lang)
    elif len(args) >= 2 and args[0] == "search":
        search(args[1:], lang)
    else:
        print(__doc__)
        sys.exit(1)
    if wikimedia_blocked():
        print("\nWikipedia is throttling this run; rerun later for the FAILED titles "
              "(saved ones are skipped), or read the pages with web fetch instead.")
