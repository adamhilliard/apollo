# -*- coding: utf-8 -*-
"""Getro VC portfolio-board sweep.  Apollo, by Adam Hilliard (MIT).

Why this file exists: the obvious recipe for these boards (fetch /jobs, parse
__NEXT_DATA__, page with ?page=N) SILENTLY STOPPED PAGINATING. Every page
returns the same first 20 jobs, so a 154-job board reads as 20 and a 25,000-job
board also reads as 20. Nothing errors. The sweep just quietly sees 0.08% of a
board and reports a clean nil.

`offset`, `start`, `from`, `p`, `pageIndex`, `skip` and the _next/data endpoint
were all tested. All return the same first 20.

The working surface is the board's own search API:

    POST https://api.getro.com/api/v2/collections/<collection_id>/search/jobs

  * `Accept: application/json` is MANDATORY. Without it the API returns
    HTTP 406, which reads like a dead endpoint and is not one.
  * `Origin` and `Referer` are also required; a bare POST returns an empty body.
  * Page size is fixed at 20 server-side. `hitsPerPage` is accepted and ignored.
  * <collection_id> is props.pageProps.network.id from the board's own /jobs page.
    Never guess it: a wrong id returns a valid-looking payload for another board.

Every board ends with COMPLETE, INCOMPLETE or UNREADABLE, plus a CANARY line.
Surface anything other than COMPLETE as a coverage gap.

Usage:
    python vc_sweep.py --stems "operations coordinator,operations manager,head of operations"
    python vc_sweep.py --stems-file stems.txt --board accel
    python vc_sweep.py --all-titles          # no filter; inspection only
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
API = "https://api.getro.com/api/v2/collections/{cid}/search/jobs"
PAGE_SIZE = 20
SAFETY_PAGES = 60           # 1,200 rows per board, then stop and SAY SO

# One empty query = an exhaustive sweep, titles filtered locally.
#
# Server-side `query` was tested and rejected, and the reason is the whole point
# of this tool. It looks attractive: it cuts a 10,976-posting board to 73, which
# would make every board COMPLETE instead of capped. But Getro's search does not
# reliably return exact title matches: on one board, querying a title returned
# 24 rows and omitted a posting carrying that exact title, which the unfiltered
# sweep finds.
#
# So it trades a VISIBLE cap (reported INCOMPLETE) for an INVISIBLE miss
# (reported COMPLETE, quietly short). A visible cap is strictly better.
# Do not re-propose query mode without re-running that recall test.
QUERIES = [""]

# Getro-platform boards. Consider-platform boards (a16z, Sequoia, Greylock,
# Bessemer, Lightspeed, Kleiner Perkins, NEA, Contrary) are NOT here: that
# platform replaced its API with a signed-token path and has no working fetch
# recipe. Read those in a browser and report SAMPLED.
BOARDS = [
    ("general-catalyst", "jobs.generalcatalyst.com"),
    ("accel",            "jobs.accel.com"),
    ("khosla",           "jobs.khoslaventures.com"),
    ("insight",          "jobs.insightpartners.com"),
    ("redpoint",         "careers.redpoint.com"),
    ("thrive",           "jobs.thrivecap.com"),
    ("menlo",            "jobs.menlovc.com"),
    ("index",            "indexventures.getro.com"),
    ("bitkraft",         "careers.bitkraft.vc"),
    ("antler",           "careers.antler.co"),
    ("techstars",        "jobs.techstars.com"),
]


def _get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def collection_id(domain):
    """Resolve the board's collection id from its own /jobs page."""
    html = _get("https://%s/jobs" % domain)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise ValueError("no __NEXT_DATA__ on %s" % domain)
    return str(json.loads(m.group(1))["props"]["pageProps"]["network"]["id"])


def fetch_page(cid, domain, page, query=""):
    body = json.dumps({"hitsPerPage": PAGE_SIZE, "page": page,
                       "filters": {"page": page}, "query": query}).encode()
    req = urllib.request.Request(
        API.format(cid=cid), data=body, method="POST",
        headers={
            "content-type": "application/json",
            "Accept": "application/json",          # omit this and it 406s
            "Origin": "https://%s" % domain,
            "Referer": "https://%s/" % domain,
            "User-Agent": UA,
        })
    raw = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
    if not raw.strip():
        raise ValueError("empty body (missing Origin/Referer?)")
    res = json.loads(raw).get("results", {})
    return res.get("jobs", []), res.get("count", 0)


def job_row(j):
    org = j.get("organization") or {}
    comp = ""
    lo, hi = j.get("compensation_amount_min_cents"), j.get("compensation_amount_max_cents")
    if j.get("compensation_public") and (lo or hi):
        comp = "$%s-$%s" % ((lo or 0) // 100000, (hi or 0) // 100000)
        comp = comp.replace("$0-", "up to $")
    locs = ", ".join(l for l in (j.get("searchable_locations") or [])[:2] if l)
    return {
        "title": j.get("title", ""),
        "company": org.get("name") or j.get("organization_name") or "",
        "work_mode": j.get("work_mode") or "",
        "location": locs,
        "comp": comp,
        "url": j.get("url", ""),
    }


def sweep_query(cid, domain, query, seen, rows, canary):
    """Paginate one query to exhaustion. Returns a status string."""
    page = 1
    first_ids = None
    while page <= SAFETY_PAGES:
        try:
            jobs, _total = fetch_page(cid, domain, page, query)
        except urllib.error.HTTPError as exc:
            if exc.code == 406:
                return "UNREADABLE - HTTP 406 (missing Accept: application/json?)"
            return "UNREADABLE - HTTP %s on page %d" % (exc.code, page)
        except Exception as exc:                   # noqa: BLE001
            return "INCOMPLETE - page %d of %r failed (%s)" % (page, query, exc)

        ids = [j.get("id") for j in jobs]
        if page == 1:
            first_ids = ids
        elif page == 2 and ids and ids == first_ids:
            # The exact regression this tool exists for.
            canary["fail"] = True
            return "UNREADABLE - pagination broken (page 2 == page 1)"
        if page == 2 and ids and ids != first_ids:
            canary["pass"] = True

        new = [j for j in jobs if j.get("id") not in seen]
        if not new:
            return "COMPLETE"
        seen.update(i for i in ids if i is not None)
        rows.extend(new)
        page += 1
        time.sleep(0.2)
    return "INCOMPLETE - hit SAFETY_PAGES (%d) on %r" % (SAFETY_PAGES, query)


def sweep_board(name, domain, stems):
    print("\n=== %s (%s) ===" % (name, domain))
    try:
        cid = collection_id(domain)
    except Exception as exc:                       # noqa: BLE001
        print("STATUS: UNREADABLE - could not resolve collection id (%s)" % exc)
        return
    print("collection_id=%s" % cid)

    seen, rows, canary = set(), [], {}
    problems = []
    for q in QUERIES:
        st = sweep_query(cid, domain, q, seen, rows, canary)
        if st != "COMPLETE":
            problems.append(st)
    status = "COMPLETE" if not problems else "; ".join(problems[:3])

    if canary.get("fail"):
        print("CANARY: FAIL - page 2 repeated page 1; pagination is dead again, "
              "do NOT report a nil from this board")
    elif canary.get("pass"):
        print("CANARY: PASS - page 2 ids differ from page 1")
    else:
        print("CANARY: n/a - the whole board fit on one page")

    hits = []
    for j in rows:
        r = job_row(j)
        if stems is None or any(s in r["title"].lower() for s in stems):
            hits.append(r)

    for r in hits:
        print("  %s | %s | %s | %s | %s | %s" % (
            r["company"], r["title"], r["location"], r["work_mode"], r["comp"], r["url"]))
    # Per-source count, zeros included. This line is what the weekly audit reads.
    print("COUNT: %s read=%d matched=%d" % (name, len(rows), len(hits)))
    print("STATUS: %s" % status)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", help="sweep one board by name")
    ap.add_argument("--stems", help="comma-separated title stems to keep")
    ap.add_argument("--stems-file", help="file with one title stem per line")
    ap.add_argument("--all-titles", action="store_true",
                    help="no title filter; inspection only, these boards are large")
    args = ap.parse_args()

    stems = None
    if args.stems_file:
        with open(args.stems_file, encoding="utf-8") as fh:
            stems = [ln.strip().lower() for ln in fh if ln.strip()]
    elif args.stems:
        stems = [s.strip().lower() for s in args.stems.split(",") if s.strip()]
    elif not args.all_titles:
        sys.exit("give --stems, --stems-file, or --all-titles.\n"
                 "Take the stems from the Queries section of your Methodology.md "
                 "so the sweep and the rest of the search agree on what counts.")

    boards = BOARDS
    if args.board:
        boards = [b for b in BOARDS if b[0] == args.board]
        if not boards:
            sys.exit("unknown board %r; known: %s"
                     % (args.board, ", ".join(b[0] for b in BOARDS)))

    for name, domain in boards:
        try:
            sweep_board(name, domain, stems)
        except Exception as exc:                   # noqa: BLE001
            print("STATUS: UNREADABLE - %s (%s)" % (name, exc))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    main()
