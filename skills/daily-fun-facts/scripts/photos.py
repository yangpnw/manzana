#!/usr/bin/env python3
"""Find and prepare real Wikimedia Commons photos for a Top 10 fun-facts sheet.

  search:  python3 photos.py search "<query>" ["<query>" ...]
           Lists candidate photos per query (index | title | size | license | description).
  build:   python3 photos.py build <out_dir> plan.json
           plan.json = {"1": ["File:A.jpg", "File:B.jpg", "File:C.jpg"], ..., "10": [...]}
           Writes, under <out_dir>:
             images/NN.jpg             one strip per entry (three photos side by side, rounded corners)
             images/originals/NN-a.jpg the three source photos per entry (b, c), about 1600–2000px wide
             credits.json              author, license and Commons page per photo; paths are
                                       relative to <out_dir>
             sheet.jpg                 all strips, for a visual check (not part of the report)
           Downloads are cached in <out_dir>/.cache, so rerunning after swapping a few photos
           only fetches the new ones.

Commons rate-limits bursts. The script batches lookups, paces downloads and retries on errors.
"""
import hashlib, json, os, random, re, sys, time, urllib.request, urllib.parse

UA = {"User-Agent": "DailyFunFactsSkill/1.0 (personal printable sheet)"}
API = "https://commons.wikimedia.org/w/api.php?"


PAUSE = 0.5  # polite gap between consecutive requests, in seconds


def get(url, parse=None, tries=6):
    """Fetch url, retrying with exponential backoff (1, 2, 4, 8, 16s, plus jitter).
    parse (e.g. json.loads) runs inside the retry, so a garbled reply is retried too."""
    for i in range(tries):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            return parse(data) if parse else data
        except Exception as e:
            if i == tries - 1:
                raise SystemExit(f"failed after {tries} tries: {url}\n  last error: {e}")
            wait = 2 ** i + random.uniform(0, 0.5)
            print(f"retry {i + 1}/{tries - 1} in {wait:.1f}s: {e}", file=sys.stderr)
            time.sleep(wait)


def api(**params):
    return get(API + urllib.parse.urlencode(dict(format="json", action="query", **params)), parse=json.loads)


def search(queries):
    for q in queries:
        print(f"=== {q}")
        d = api(generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=12,
                prop="imageinfo", iiprop="size|extmetadata", iiextmetadatafilter="LicenseShortName|ImageDescription")
        pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
        if not pages:
            print("  (no results - try a broader or local-language query)")
        for n, p in enumerate(pages):
            ii = p["imageinfo"][0]
            m = ii.get("extmetadata", {})
            desc = re.sub("<[^>]+>", "", m.get("ImageDescription", {}).get("value", "")).replace("\n", " ")[:90]
            lic = m.get("LicenseShortName", {}).get("value", "")
            print(f"  {n} | {p['title']} | {ii['width']}x{ii['height']} | {lic} | {desc}")
        time.sleep(PAUSE)


def text(meta, key):
    return re.sub("<[^>]+>", "", meta.get(key, {}).get("value", "")).strip()


def lookup(titles):
    """imageinfo for many files at once (the API takes 50 titles per call), keyed by title."""
    info = {}
    for i in range(0, len(titles), 50):
        d = api(titles="|".join(titles[i:i + 50]), prop="imageinfo", iiprop="url|extmetadata",
                iiurlwidth=1600, iiextmetadatafilter="Artist|LicenseShortName|LicenseUrl")
        q = d["query"]
        names = {n["to"]: n["from"] for n in q.get("normalized", [])}
        for page in q["pages"].values():
            title = names.get(page["title"], page["title"])
            if "imageinfo" not in page:
                raise SystemExit(f"not found on Commons: {title}")
            info[title] = page["imageinfo"][0]
    return info


def build(out_dir, plan_path):
    from PIL import Image, ImageDraw, ImageOps
    img_dir = os.path.join(out_dir, "images")
    orig_dir = os.path.join(img_dir, "originals")
    cache = os.path.join(out_dir, ".cache")
    for d in (orig_dir, cache):
        os.makedirs(d, exist_ok=True)
    plan = json.load(open(plan_path))
    info = lookup(sorted({t for key in plan for t in plan[key][:3]}))
    H, W, GAP, R = 420, 560, 16, 22
    rows, credits = [], {}
    for key in sorted(plan, key=int):
        nn = f"{int(key):02d}"
        out = Image.new("RGB", (3 * W + 2 * GAP, H), "white")
        credits[nn] = []
        for n, title in enumerate(plan[key][:3]):
            ii = info[title]
            cached = os.path.join(cache, hashlib.sha1(title.encode()).hexdigest() + ".img")
            if not os.path.exists(cached):
                open(cached, "wb").write(get(ii["thumburl"]))
                time.sleep(PAUSE)
            rel = f"images/originals/{nn}-{'abc'[n]}.jpg"
            im = ImageOps.exif_transpose(Image.open(cached)).convert("RGB")
            im.save(os.path.join(out_dir, rel), quality=90)
            m = ii.get("extmetadata", {})
            credits[nn].append({"file": title, "image": rel, "author": text(m, "Artist"),
                                "license": text(m, "LicenseShortName"),
                                "license_url": text(m, "LicenseUrl"), "source": ii["descriptionurl"]})
            im = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.4))
            mask = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, W, H), R, fill=255)
            out.paste(im, (n * (W + GAP), 0), mask)
        row = os.path.join(img_dir, f"{nn}.jpg")
        out.save(row, quality=88)
        rows.append(out)
        print("wrote", row)
    json.dump(credits, open(os.path.join(out_dir, "credits.json"), "w"), indent=2, ensure_ascii=False)
    print("wrote", os.path.join(out_dir, "credits.json"))
    sheet = Image.new("RGB", (864 * 2, 210 * ((len(rows) + 1) // 2)), "white")
    for i, r in enumerate(rows):
        sheet.paste(r.resize((864, 210)), ((i % 2) * 864, (i // 2) * 210))
    sheet.save(os.path.join(out_dir, "sheet.jpg"))
    print("wrote", os.path.join(out_dir, "sheet.jpg"))

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        search(sys.argv[2:])
    elif len(sys.argv) == 4 and sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
