"""Polite HTTP for the daily-fun-facts scripts (photos.py, wiki.py).

Wikimedia (Commons, Wikipedia, upload.wikimedia.org) rate-limits clients hard, so every request
here goes through one gate:

  * a descriptive User-Agent with a contact URL, as Wikimedia's bot policy asks
    (https://w.wiki/4wJS); unknown-looking clients get throttled much sooner
  * per host: at most N requests in flight and a minimum gap between request starts
    (Wikimedia hosts: one at a time, 1-1.5 s apart)
  * on HTTP 429/503: wait for the server's Retry-After (5-60 s), then retry once
  * after 2 consecutive 429s from Wikimedia, stop sending it anything for the rest of the run;
    callers get a FetchError right away and fall back to their next (non-Wikimedia) candidate
"""
import email.utils, json, random, sys, threading, time, urllib.parse, urllib.request

UA = {"User-Agent": "DailyFunFacts/1.0 (https://dailyfunfacts.app/; daily printable fact sheets)"}

# minimum seconds between request starts, and max requests in flight, per host
WIKIMEDIA_GAP = {"upload.wikimedia.org": 1.5, "commons.wikimedia.org": 1.0}
DEFAULT_WIKIMEDIA_GAP = 1.0   # *.wikipedia.org and other Wikimedia hosts
DEFAULT_GAP, DEFAULT_SLOTS = 0.2, 3
MAX_RETRY_WAIT = 60
BLOCK_AFTER = 2               # consecutive Wikimedia 429s before we stop calling it this run


class FetchError(Exception):
    pass


def is_wikimedia(host):
    return host.endswith("wikimedia.org") or host.endswith("wikipedia.org")


class _Host:
    def __init__(self, host):
        wm = is_wikimedia(host)
        self.gap = WIKIMEDIA_GAP.get(host, DEFAULT_WIKIMEDIA_GAP) if wm else DEFAULT_GAP
        self.slots = threading.BoundedSemaphore(1 if wm else DEFAULT_SLOTS)
        self.lock, self.next_start = threading.Lock(), 0.0

    def wait_turn(self):
        with self.lock:
            now = time.monotonic()
            start = max(now, self.next_start)
            self.next_start = start + self.gap
        if start > now:
            time.sleep(start - now)


_hosts, _guard = {}, threading.Lock()
_wm = {"streak": 0, "blocked": False}


def _host(host):
    with _guard:
        if host not in _hosts:
            _hosts[host] = _Host(host)
        return _hosts[host]


def wikimedia_blocked():
    return _wm["blocked"]


def _retry_after(err):
    value = (getattr(err, "headers", None) or {}).get("Retry-After")
    if value:
        try:
            secs = float(value)
        except ValueError:
            try:
                secs = email.utils.parsedate_to_datetime(value).timestamp() - time.time()
            except (TypeError, ValueError):
                secs = 0
    else:
        secs = 0
    return min(MAX_RETRY_WAIT, max(5.0, secs)) + random.uniform(0, 1)


def _note_429(wm):
    if not wm:
        return
    with _guard:
        _wm["streak"] += 1
        if _wm["streak"] >= BLOCK_AFTER and not _wm["blocked"]:
            _wm["blocked"] = True
            print("Wikimedia is throttling us (HTTP 429); skipping its remaining requests this run. "
                  "Non-Wikimedia candidates are used instead; rerun later for the rest.", file=sys.stderr)


def get(url, parse=None, tries=2):
    """Fetch url politely. parse (e.g. json.loads) runs inside the retry, so a garbled reply is
    retried too. Raises FetchError when it gives up; callers skip and move on."""
    host = urllib.parse.urlparse(url).netloc
    wm, h = is_wikimedia(host), _host(host)
    last = None
    for i in range(tries):
        if wm and _wm["blocked"]:
            raise FetchError(f"{url}\n  last error: skipped, Wikimedia is throttling this run")
        with h.slots:
            h.wait_turn()
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
                result = parse(data) if parse else data
                if wm:
                    _wm["streak"] = 0
                return result
            except Exception as e:
                last, code = e, getattr(e, "code", None)
        if code == 429:
            _note_429(wm)
        if code in (400, 401, 403, 404, 410) or i == tries - 1 or (wm and _wm["blocked"]):
            break
        time.sleep(_retry_after(last) if code in (429, 503) else 1 + random.uniform(0, 0.5))
    raise FetchError(f"{url}\n  last error: {last}")


def getjson(base, **params):
    return get(base + urllib.parse.urlencode(params), parse=json.loads)
