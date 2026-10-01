#!/usr/bin/env python3
"""Find and prepare real, freely licensed photos for a Top 10 fun-facts sheet.

  search:  python3 photos.py search [--source S[,S...]] "<query>" ["<query>" ...]
           Lists candidates per query and source (id | size | license | title).
           Sources (no API keys needed):
             commons   Wikimedia Commons (default; ids look like File:Name.jpg)
             openverse Openverse: CC photos from Flickr, museums and others (ov:<id>)
             met       The Met Museum, public-domain objects (met:<id>)
             aic       Art Institute of Chicago, public-domain works (aic:<id>)
             inat      iNaturalist, research-grade CC photos of plants and animals (inat:<id>)
             all       every source above
           Non-Commons results are saved to ./candidates.json so build can resolve their ids.
  build:   python3 photos.py build <out_dir> plan.json
           plan.json = {"1": ["File:A.jpg", "ov:…", "met:…", "inat:…"], ..., "10": [...]}; any source
           mix. List 4-5 candidates per entry: each strip uses the first 3 that download, so a
           blocked or broken photo is skipped instead of stopping the run.
           Writes, under <out_dir>:
             images/NN.jpg             one strip per entry (three photos side by side, rounded corners)
             images/originals/NN-a.jpg the three source photos per entry (b, c), up to 1280px wide
             credits.json              author, license and source page per photo; paths are
                                       relative to <out_dir>
             sheet.jpg                 all strips, for a visual check (not part of the report)
           Downloads are cached in <out_dir>/.cache, so rerunning after swapping a few photos
           only fetches the new ones. A photo that can't be downloaded leaves a grey gap and is
           listed at the end (exit code 2) only when an entry has fewer than 3 usable photos.

Never waits long: a failed request is retried once after ~1s, then skipped. Searches query all
chosen sources in parallel; downloads run in parallel, one at a time per Wikimedia host.
"""
import concurrent.futures, hashlib, json, os, random, re, sys, threading, time, urllib.request, urllib.parse

UA = {"User-Agent": "DailyFunFactsSkill/1.0 (personal printable sheet)"}
COMMONS = "https://commons.wikimedia.org/w/api.php?"
PAUSE = 0.5  # polite gap between consecutive requests, in seconds
STEPS = [250, 330, 500, 960, 1280]  # Wikimedia standard thumbnail widths
CANDIDATES = "candidates.json"


class FetchError(Exception):
    pass


def get(url, parse=None, tries=2):
    """Fetch url; on failure retry once after ~1s, then give up (callers skip and move on).
    parse (e.g. json.loads) runs inside the retry, so a garbled reply is retried too."""
    for i in range(tries):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
            return parse(data) if parse else data
        except Exception as e:
            if getattr(e, "code", None) in (400, 401, 403, 404) or i == tries - 1:
                raise FetchError(f"{url}\n  last error: {e}")
            time.sleep(1 + random.uniform(0, 0.5))


def getjson(base, **params):
    return get(base + urllib.parse.urlencode(params), parse=json.loads)


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", "", s or "")).strip()


# --- sources: each search returns [{id, url, width, height, title, author, license, license_url, source}] ---

def commons_search(q):
    d = getjson(COMMONS, format="json", action="query", generator="search", gsrsearch=q + " filetype:bitmap",
                gsrnamespace=6, gsrlimit=12, prop="imageinfo", iiprop="size|extmetadata",
                iiextmetadatafilter="LicenseShortName|ImageDescription")
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii, m = p["imageinfo"][0], p["imageinfo"][0].get("extmetadata", {})
        out.append({"id": p["title"], "width": ii["width"], "height": ii["height"],
                    "license": strip_html(m.get("LicenseShortName", {}).get("value")),
                    "title": strip_html(m.get("ImageDescription", {}).get("value"))[:90]})
    return out


def openverse_search(q):
    d = getjson("https://api.openverse.org/v1/images/?", q=q, page_size=12, mature="false",
                excluded_source="wikimedia")  # Commons is searched directly
    out = []
    for r in d.get("results", []):
        lic = f"CC {r['license'].upper()} {r.get('license_version') or ''}".strip()
        if r["license"] in ("cc0", "pdm"):
            lic = "CC0" if r["license"] == "cc0" else "Public domain"
        out.append({"id": "ov:" + r["id"], "url": r["url"], "width": r.get("width"), "height": r.get("height"),
                    "title": f"{r.get('title') or ''} ({r.get('source')})", "author": r.get("creator") or "",
                    "license": lic, "license_url": r.get("license_url") or "",
                    "source": r.get("foreign_landing_url") or r["url"]})
    return out


def met_search(q):
    ids = (getjson("https://collectionapi.metmuseum.org/public/collection/v1/search?",
                   hasImages="true", q=q).get("objectIDs") or [])[:12]
    out = []
    for oid in ids:
        o = get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}", parse=json.loads)
        time.sleep(0.1)
        if o.get("isPublicDomain") and o.get("primaryImageSmall"):
            out.append({"id": f"met:{oid}", "url": o["primaryImageSmall"], "width": None, "height": None,
                        "title": f"{o.get('title')} ({o.get('objectDate') or o.get('culture') or ''})",
                        "author": o.get("artistDisplayName") or "The Metropolitan Museum of Art",
                        "license": "CC0", "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "source": o.get("objectURL") or ""})
    return out


def aic_search(q):
    d = getjson("https://api.artic.edu/api/v1/artworks/search?", q=q, limit=12,
                fields="id,title,image_id,artist_display,is_public_domain,thumbnail")
    out = []
    for r in d.get("data", []):
        if r.get("is_public_domain") and r.get("image_id"):
            t = r.get("thumbnail") or {}
            out.append({"id": f"aic:{r['id']}", "url": f"https://www.artic.edu/iiif/2/{r['image_id']}/full/843,/0/default.jpg",
                        "width": t.get("width"), "height": t.get("height"), "title": r.get("title") or "",
                        "author": (r.get("artist_display") or "Art Institute of Chicago").split("\n")[0],
                        "license": "CC0", "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                        "source": f"https://www.artic.edu/artworks/{r['id']}"})
    return out


def inat_search(q):
    d = getjson("https://api.inaturalist.org/v1/observations?", taxon_name=q, photos="true", per_page=12,
                quality_grade="research", photo_license="cc0,cc-by,cc-by-sa", order_by="votes")
    out = []
    for r in d.get("results", []):
        for p in r.get("photos", [])[:1]:
            code = (p.get("license_code") or "").upper()
            out.append({"id": f"inat:{p['id']}", "url": p["url"].replace("/square.", "/large."),
                        "width": (p.get("original_dimensions") or {}).get("width"),
                        "height": (p.get("original_dimensions") or {}).get("height"),
                        "title": (r.get("taxon") or {}).get("name", q) + " · " + (r.get("place_guess") or ""),
                        "author": p.get("attribution") or "",
                        "license": "CC0" if code == "CC0" else code.replace("CC-", "CC "),
                        "license_url": f"https://creativecommons.org/licenses/{code.lower().removeprefix('cc-')}/4.0/"
                        if code != "CC0" else "https://creativecommons.org/publicdomain/zero/1.0/",
                        "source": f"https://www.inaturalist.org/photos/{p['id']}"})
    return out


SOURCES = {"commons": commons_search, "openverse": openverse_search, "met": met_search,
           "aic": aic_search, "inat": inat_search}


def save_candidates(path, new):
    """Merge into candidates.json (re-read first, so parallel searches don't drop each other's ids)."""
    saved = json.load(open(path)) if os.path.exists(path) else {}
    saved.update(new)
    json.dump(saved, open(path + ".tmp", "w"), indent=1, ensure_ascii=False)
    os.replace(path + ".tmp", path)


def search(sources, queries):
    def run(q, name):
        try:
            return SOURCES[name](q), None
        except Exception as e:
            return [], str(e).splitlines()[-1].strip()
    jobs = [(q, name) for q in queries for name in sources]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(jobs))) as pool:
        results = list(pool.map(lambda j: run(*j), jobs))
    new = {}
    for (q, name), (found, err) in zip(jobs, results):
        print(f"=== {q}  [{name}]")
        if err:
            print(f"  (skipped: {err})")
        elif not found:
            print("  (no results - try a broader or local-language query)")
        for n, r in enumerate(found):
            size = f"{r['width']}x{r['height']}" if r.get("width") else "?"
            print(f"  {n} | {r['id']} | {size} | {r['license']} | {r['title'][:90]}")
            if not r["id"].startswith("File:"):
                new[r["id"]] = r
    save_candidates(CANDIDATES, new)


# --- build ---

def commons_lookup(titles):
    """Download URL and credits for many Commons files at once (50 titles per call), keyed by title."""
    info = {}
    for i in range(0, len(titles), 50):
        d = getjson(COMMONS, format="json", action="query", titles="|".join(titles[i:i + 50]),
                    prop="imageinfo", iiprop="url|size|extmetadata",
                    iiurlwidth=1280, iiextmetadatafilter="Artist|LicenseShortName|LicenseUrl")
        q = d["query"]
        names = {n["to"]: n["from"] for n in q.get("normalized", [])}
        for page in q["pages"].values():
            title = names.get(page["title"], page["title"])
            if "imageinfo" not in page:
                print(f"not found on Commons: {title}", file=sys.stderr)
                continue
            ii = page["imageinfo"][0]
            url = ii["thumburl"]
            if ii.get("thumbwidth", 0) >= ii["width"]:
                # smaller than 1280px: the API hands back the original, which is throttled hard;
                # ask for the largest standard thumbnail below the original width instead
                step = max([s for s in STEPS if s < ii["width"]] or [STEPS[0]])
                path = ii["url"].split("?", 1)[0].split("/wikipedia/commons/", 1)[1]
                url = (f"https://upload.wikimedia.org/wikipedia/commons/thumb/{path}/"
                       f"{step}px-{path.rsplit('/', 1)[1]}")
            m = ii.get("extmetadata", {})
            info[title] = {"url": url, "author": strip_html(m.get("Artist", {}).get("value")),
                           "license": strip_html(m.get("LicenseShortName", {}).get("value")),
                           "license_url": strip_html(m.get("LicenseUrl", {}).get("value")),
                           "source": ii["descriptionurl"]}
    return info


HOST_LIMITS = {"upload.wikimedia.org": 1, "thumb.wikimedia.org": 1}  # Wikimedia throttles parallel fetches
_host_locks, _host_guard = {}, threading.Lock()


def host_slot(url):
    host = urllib.parse.urlparse(url).netloc
    with _host_guard:
        if host not in _host_locks:
            _host_locks[host] = threading.BoundedSemaphore(HOST_LIMITS.get(host, 3))
        return _host_locks[host]


def fetch_cached(pid, meta, cache):
    """Return the cached file path for pid, downloading it first if needed; raises on failure."""
    if meta is None:
        raise FetchError("unknown id (search for it first so it lands in candidates.json)")
    cached = os.path.join(cache, hashlib.sha1(pid.encode()).hexdigest() + ".img")
    if not os.path.exists(cached) or os.path.getsize(cached) == 0:
        with host_slot(meta["url"]):
            data = get(meta["url"])  # fetch fully first, so a failed download never leaves a cache file
            time.sleep(PAUSE / 2)
        open(cached + ".part", "wb").write(data)
        os.replace(cached + ".part", cached)
    return cached


def build(out_dir, plan_path):
    from PIL import Image, ImageDraw, ImageOps
    img_dir = os.path.join(out_dir, "images")
    orig_dir = os.path.join(img_dir, "originals")
    cache = os.path.join(out_dir, ".cache")
    for d in (orig_dir, cache):
        os.makedirs(d, exist_ok=True)
    plan = json.load(open(plan_path))
    ids = sorted({t for key in plan for t in plan[key]})
    try:
        info = commons_lookup([t for t in ids if t.startswith("File:")])
    except FetchError as e:
        print(f"Commons lookup failed, skipping Commons photos: {e}", file=sys.stderr)
        info = {}
    cand_path = os.path.join(os.path.dirname(os.path.abspath(plan_path)), CANDIDATES)
    cands = json.load(open(cand_path)) if os.path.exists(cand_path) else {}
    info.update({t: cands[t] for t in ids if t in cands})

    # download every candidate in parallel; each strip then takes the first 3 that worked
    def load(pid):
        try:
            path = fetch_cached(pid, info.get(pid), cache)
            return pid, ImageOps.exif_transpose(Image.open(path)).convert("RGB"), None
        except Exception as e:
            return pid, None, str(e).splitlines()[-1].strip()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        loaded = {pid: (im, err) for pid, im, err in pool.map(load, ids)}

    H, W, GAP, R = 420, 560, 16, 22
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W, H), R, fill=255)
    rows, credits, skipped, short = [], {}, [], []
    for key in sorted(plan, key=int):
        nn = f"{int(key):02d}"
        out = Image.new("RGB", (3 * W + 2 * GAP, H), "white")
        credits[nn] = []
        picked = []
        for pid in plan[key]:
            im, err = loaded[pid]
            if im is None:
                skipped.append(f"#{key} {pid}: {err}")
            elif len(picked) < 3:
                picked.append((pid, im))
        if len(picked) < 3:
            short.append(f"#{key}: only {len(picked)} usable photo(s)")
        for n, (pid, im) in enumerate(picked):
            meta = info[pid]
            if im.width > 1280:
                im = im.resize((1280, round(im.height * 1280 / im.width)), Image.LANCZOS)
            rel = f"images/originals/{nn}-{'abc'[n]}.jpg"
            im.save(os.path.join(out_dir, rel), quality=90)
            credits[nn].append({"file": pid.removeprefix("File:") if pid.startswith("File:") else meta.get("title", pid),
                                "id": pid, "image": rel, "author": meta.get("author", ""),
                                "license": meta.get("license", ""), "license_url": meta.get("license_url", ""),
                                "source": meta.get("source", "")})
            out.paste(ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.4)), (n * (W + GAP), 0), mask)
        for n in range(len(picked), 3):
            out.paste(Image.new("RGB", (W, H), "#dddddd"), (n * (W + GAP), 0), mask)
        row = os.path.join(img_dir, f"{nn}.jpg")
        out.save(row, quality=88)
        rows.append(out)
        print(f"wrote {row}  ({', '.join(p for p, _ in picked)})")
    json.dump(credits, open(os.path.join(out_dir, "credits.json"), "w"), indent=2, ensure_ascii=False)
    print("wrote", os.path.join(out_dir, "credits.json"))
    sheet = Image.new("RGB", (864 * 2, 210 * ((len(rows) + 1) // 2)), "white")
    for i, r in enumerate(rows):
        sheet.paste(r.resize((864, 210)), ((i % 2) * 864, (i // 2) * 210))
    sheet.save(os.path.join(out_dir, "sheet.jpg"))
    print("wrote", os.path.join(out_dir, "sheet.jpg"))
    if skipped:
        print("\nskipped (used the next candidate instead):\n  " + "\n  ".join(skipped))
    if short:
        print("\nNEEDS MORE PHOTOS (grey gaps; add candidates to these entries and rerun):\n  " + "\n  ".join(short))
        sys.exit(2)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "search":
        sources, queries = ["commons"], args[1:]
        if queries[0].startswith("--source"):
            spec = queries[0].split("=", 1)[1] if "=" in queries[0] else queries[1]
            queries = queries[1:] if "=" in queries[0] else queries[2:]
            sources = list(SOURCES) if spec == "all" else spec.split(",")
            bad = [s for s in sources if s not in SOURCES]
            if bad:
                raise SystemExit(f"unknown source(s): {', '.join(bad)}; choose from {', '.join(SOURCES)} or all")
        search(sources, queries)
    elif len(args) == 3 and args[0] == "build":
        build(args[1], args[2])
    else:
        print(__doc__)
