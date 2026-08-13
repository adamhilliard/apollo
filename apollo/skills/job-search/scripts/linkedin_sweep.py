#!/usr/bin/env python
"""
LinkedIn guest-search sweep for the job-search digest.

Why this file exists: two silent truncation bugs, found 8/4/26, both of which
made a partial result set look identical to a complete one.

  1. The authenticated results page is virtualized. A query reporting 51
     results rendered only 12 of its 25 first-page cards, and no amount of
     scrolling forced the rest.
  2. The guest endpoint returns TEN cards per page, not 25. The ad-hoc script
     that replaced (1) stepped `start` by 25, so it skipped 15 results per
     page while looking like it was paginating correctly.

Both failures are invisible downstream: the digest just reports fewer roles.
So this tool refuses to report a result set it cannot vouch for. Every run
ends with either COMPLETE or an explicit INCOMPLETE line naming what was
missed, and callers are expected to surface INCOMPLETE in the digest as a
coverage gap the same way a skipped LinkedIn run is surfaced.

Usage:
    python linkedin_sweep.py "<keywords>" "<location>" [--window r604800] [--remote]

    --window   r604800 = past week (default), r2592000 = past month
    --remote   adds f_WT=2

Output: one "id ~ title ~ company ~ location ~ date" line per unique posting,
then a STATUS line. Parse the STATUS line; do not trust the rows without it.

Part of Apollo, a free job-search plugin for Claude Code.
By Adam Hilliard - https://linkedin.com/in/adamhilliard - MIT licensed.
"""

import sys
import re
import time
import html
import urllib.request
import urllib.error

PAGE = 10               # guest API page size, verified 8/4/26, NOT 25
SAFETY_CAP = 1000       # absolute stop; hitting it is reported as INCOMPLETE
EMPTY_STREAK_DONE = 2   # consecutive no-new-id pages that mean "exhausted"
BASE = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/"
        "search?keywords={q}&location={loc}&f_TPR={tpr}{wt}&start={start}")


def fetch(url, attempts=3):
    """Return page HTML, or None if the page genuinely could not be read."""
    for n in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code == 429:            # rate limited, back off and retry
                time.sleep(3 * (n + 1))
                continue
            if e.code in (400, 404):     # past the end of the result set
                return ""
            time.sleep(1 + n)
        except Exception:
            time.sleep(1 + n)
    return None


def parse(page_html):
    out = []
    for card in page_html.split("<li>")[1:]:
        def grab(pattern, group=1):
            m = re.search(pattern, card, re.S)
            if not m:
                return ""
            return html.unescape(re.sub("<[^>]*>", "", m.group(group))).strip()

        jid = grab(r'data-entity-urn="urn:li:jobPosting:(\d+)"') or grab(r"-(\d{10})\?")
        if not jid:
            continue
        out.append((
            jid,
            grab(r'class="sr-only">\s*(.*?)\s*</span>'),
            grab(r"hidden-nested-link[^>]*>\s*(.*?)\s*</a>"),
            grab(r'job-search-card__location">\s*(.*?)\s*</span>'),
            grab(r'datetime="([\d-]+)"'),
        ))
    return out


def sweep(keywords, location, window="r604800", remote=False):
    seen, rows = set(), []
    start, empty_streak, failed_pages = 0, 0, []

    while start < SAFETY_CAP:
        url = BASE.format(q=keywords, loc=location, tpr=window,
                          wt="&f_WT=2" if remote else "", start=start)
        page = fetch(url)

        if page is None:
            # A page we could not read is a hole in the middle of the results.
            # Record it and keep going rather than stopping early and calling
            # the truncated set complete.
            failed_pages.append(start)
            start += PAGE
            continue

        cards = parse(page)
        new = [c for c in cards if c[0] not in seen]
        for c in new:
            seen.add(c[0])
            rows.append(c)

        # Terminate on genuine exhaustion: no NEW ids, twice running. Checking
        # "no new ids" rather than "no cards" also catches the case where
        # LinkedIn loops back and re-serves earlier results forever.
        empty_streak = empty_streak + 1 if not new else 0
        if empty_streak >= EMPTY_STREAK_DONE:
            break

        start += PAGE
        time.sleep(0.25)

    hit_cap = start >= SAFETY_CAP
    return rows, failed_pages, hit_cap


def main():
    # Windows defaults stdout to cp1252, which dies on the first non-Latin-1
    # character in a company name and kills the run mid-sweep (8/5/26).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)

    window = "r604800"
    if "--window" in sys.argv:
        window = sys.argv[sys.argv.index("--window") + 1]
    remote = "--remote" in sys.argv

    rows, failed, hit_cap = sweep(args[0], args[1], window, remote)

    for r in sorted(rows, key=lambda x: (x[2].lower(), x[1].lower())):
        print(" ~ ".join(r))

    print("-" * 60)
    if failed or hit_cap:
        problems = []
        if failed:
            problems.append("unreadable pages at start=" + ",".join(map(str, failed)))
        if hit_cap:
            problems.append("hit the %d safety cap, more results exist" % SAFETY_CAP)
        print("STATUS: INCOMPLETE: %d unique postings. %s" % (len(rows), "; ".join(problems)))
        print("        Report this as a coverage gap in the digest.")
        sys.exit(1)

    print("STATUS: COMPLETE: %d unique postings, paginated to exhaustion." % len(rows))


if __name__ == "__main__":
    main()
