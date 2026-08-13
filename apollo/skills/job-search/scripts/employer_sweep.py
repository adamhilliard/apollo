#!/usr/bin/env python
"""
Direct-employer board sweep: pull a named list of employers' job boards and
filter locally.

Part of Apollo, a free job-search plugin for Claude Code.
By Adam Hilliard - https://linkedin.com/in/adamhilliard - MIT licensed.

Why this exists: a scoring rubric has structural blind spots, and keyword
search cannot reach them. If the work-shape bucket is binary, an office a
mile away scores the same as one an hour away. If industry is a tiebreaker
rather than a bucket, the user's favorite industry never earns a point. The
countermeasure is to sweep a named set of employers every cycle regardless of
score. See "Technique: named-employer board sweeps" in search-techniques.md.

This script hardcodes NO employers. It reads them from the user's own
Employer_Index.md, which is the canonical list; this file is only the runner.

Index format. Any heading followed by a table with Platform and Slug columns
becomes a sweepable set:

    ## Employers in my metro, 100+ staff

    | Company    | Platform   | Slug       |
    |---|---|---|
    | Example Co | greenhouse | exampleco  |
    | Another Co | lever      | anotherco  |

Supported platforms: greenhouse, lever, ashby, workday. Workday needs three
parts, written `host / tenant / site`, e.g.
`acme.wd5.myworkdayjobs.com / acme / ACMEUS`. Slash-separated, not
pipe-separated: a pipe inside a table cell would break the table.

Title filters come from an HTML comment anywhere in the index, so they stay
invisible in the rendered document:

    <!-- sweep-config
    seniority = chief|svp|vice president|\\bvp\\b|head of
    function  = people|human resource|\\bhr\\b|talent
    stretch   = (senior )?director
    stretch_comp_floor = 320
    -->

`seniority` and `function` must BOTH match a title for it to be reported.
`stretch` is optional: titles matching it, but not seniority, are held back
unless the board publishes comp at or above `stretch_comp_floor` (in
thousands). Held-back rows are listed separately so nothing disappears
silently.

Usage:
    python employer_sweep.py                          # every set in the index
    python employer_sweep.py --set "my metro"          # one set, substring match
    python employer_sweep.py --index path/to/Index.md
    python employer_sweep.py --list                   # show sets and exit

Output: one matching row per line, then a STATUS line naming any board that
could not be read. An unreadable board is a coverage gap, not an empty one.
"""

import sys
import re
import json
import time
import os
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    # Without this a single non-Latin-1 company name kills the run on Windows,
    # leaving a partial file that reads as complete. That is the exact silent
    # truncation the STATUS line exists to catch.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_SENIORITY = r"chief|\bsvp\b|senior vice president|vice president|\bvp\b|head of"
DEFAULT_FUNCTION = r"."          # match anything; the index should narrow this

CONFIG_RE = re.compile(r"<!--\s*sweep-config(.*?)-->", re.S | re.I)
HEADING_RE = re.compile(r"^#{2,4}\s+(.*?)\s*$")
ROW_RE = re.compile(r"^\|(.+)\|\s*$")


# --------------------------------------------------------------------------
# Reading the index
# --------------------------------------------------------------------------

def find_index(explicit=None):
    if explicit:
        if not os.path.isfile(explicit):
            sys.exit("no index file at %s" % explicit)
        return explicit
    for name in ("Employer_Index.md", "employer_index.md"):
        for d in (".", ".."):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    sys.exit("no Employer_Index.md found. Pass --index PATH.")


def parse_config(text):
    cfg = {"seniority": DEFAULT_SENIORITY, "function": DEFAULT_FUNCTION,
           "stretch": "", "stretch_comp_floor": "0"}
    m = CONFIG_RE.search(text)
    if m:
        for line in m.group(1).splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip().lower()
                if k in cfg:
                    cfg[k] = v.strip()
    return cfg


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_sets(text):
    """Return [(heading, [(company, platform, slug), ...]), ...].

    A set is any heading whose section contains a table with Platform and Slug
    columns. Tables without those columns (prose tables, tier notes) are
    skipped, so the index can hold plenty that is not sweepable.
    """
    sets, heading, header, idx = [], None, None, {}
    current = []

    def flush():
        if heading and current:
            sets.append((heading, list(current)))

    for line in text.splitlines():
        h = HEADING_RE.match(line)
        if h:
            flush()
            heading, header, idx, current = h.group(1), None, {}, []
            continue
        r = ROW_RE.match(line)
        if not r:
            continue
        cells = split_row(r.group(1))
        if set("".join(cells)) <= set("-: "):        # separator row
            continue
        low = [c.lower() for c in cells]
        if "platform" in low and "slug" in low:      # header row
            header = low
            idx = {"platform": low.index("platform"), "slug": low.index("slug"),
                   "company": low.index("company") if "company" in low else 0}
            continue
        if not header:
            continue
        if max(idx.values()) >= len(cells):
            continue
        company = re.sub(r"[*`\[\]]", "", cells[idx["company"]]).strip()
        platform = cells[idx["platform"]].strip().lower().strip("`")
        slug = cells[idx["slug"]].strip().strip("`")
        if company and platform and slug:
            current.append((company, platform, slug))
    flush()
    return sets


# --------------------------------------------------------------------------
# Pulling boards
# --------------------------------------------------------------------------

def get(url, data=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    return json.load(urllib.request.urlopen(req, timeout=30))


def pull(platform, slug):
    """Return a list of (title, location, comp_summary) or raise.

    comp_summary is whatever the board publishes, or "". An absent value must
    stay falsy: it feeds the stretch-tier comp test, where undisclosed has to
    fail rather than pass.
    """
    if platform == "greenhouse":
        d = get("https://boards-api.greenhouse.io/v1/boards/%s/jobs" % slug)
        return [(j.get("title", ""), (j.get("location") or {}).get("name", ""), "")
                for j in d.get("jobs", [])]
    if platform == "lever":
        d = get("https://api.lever.co/v0/postings/%s?mode=json" % slug)
        return [(j.get("text", ""), (j.get("categories") or {}).get("location", ""), "")
                for j in d]
    if platform == "ashby":
        d = get("https://api.ashbyhq.com/posting-api/job-board/%s"
                "?includeCompensation=true" % slug)
        # workplaceType is the posting's own field. isRemote is NOT the same
        # thing and the two disagree routinely, so print the real one. It goes
        # FIRST because the location column gets truncated for display and this
        # is the field the location screen actually turns on.
        return [(j.get("title", ""),
                 "[%s] %s" % (j.get("workplaceType", "?"), j.get("location", "")),
                 (j.get("compensation") or {}).get("compensationTierSummary") or "")
                for j in d.get("jobs", [])]
    if platform == "workday":
        parts = [p.strip().strip("`") for p in re.split(r"[/|,]", slug) if p.strip()]
        if len(parts) != 3:
            raise ValueError("workday slug needs host / tenant / site, got %r" % slug)
        host, tenant, site = parts
        out, offset = [], 0
        while offset < 400:
            body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset,
                               "searchText": ""}).encode()
            d = get("https://%s/wday/cxs/%s/%s/jobs" % (host, tenant, site), body,
                    {"content-type": "application/json"})
            posts = d.get("jobPostings", [])
            if not posts:
                break
            out += [(p.get("title", ""), p.get("locationsText", ""), "") for p in posts]
            offset += 20
            if offset >= (d.get("total") or 0):
                break
            time.sleep(0.2)
        return out
    raise ValueError("unknown platform %r" % platform)


def comp_clears(comp_summary, floor_k):
    """True only when the board explicitly publishes comp at or above floor_k.

    Undisclosed comp fails. A row this rejects can still be added by hand if
    the user has a reason the board cannot show.
    """
    if not comp_summary or floor_k <= 0:
        return False
    nums = [int(m.group(1)) for m in re.finditer(r"\$(\d{3})K", comp_summary, re.I)]
    nums += [int(m.group(1).replace(",", "")) // 1000
             for m in re.finditer(r"\$(\d{3},\d{3})", comp_summary)]
    return bool(nums) and max(nums) >= floor_k


# --------------------------------------------------------------------------
# Sweeping
# --------------------------------------------------------------------------

def sweep(name, board, seniority, function, stretch, floor_k):
    hits, held, failed, scanned = [], [], [], 0
    print("=== %s (%d boards) ===" % (name, len(board)))
    for company, platform, slug in board:
        try:
            rows = pull(platform, slug)
        except Exception as e:
            failed.append("%s (%s)" % (company, str(e)[:40]))
            continue
        scanned += len(rows)
        for title, loc, comp in rows:
            if not function.search(title):
                continue
            if seniority.search(title):
                hits.append((company, title, loc, comp or ""))
            elif stretch and stretch.search(title):
                if comp_clears(comp, floor_k):
                    hits.append((company, title, loc, comp or ""))
                else:
                    held.append((company, title, comp or "no comp posted"))
        time.sleep(0.2)

    for c, t, l, comp in sorted(hits):
        print("  %-22s | %-52s | %-26s | %s" % (c, t[:52], l[:26], comp[:28]))
    if not hits:
        print("  (no target-title matches)")
    if held:
        print("  -- %d stretch-tier titles held back below the $%dK comp floor:"
              % (len(held), floor_k))
        for c, t, comp in sorted(held):
            print("       %-20s | %-46s | %s" % (c, t[:46], comp[:30]))
        print("     Add one by hand only with a reason the board cannot show.")
    print("  scanned %d postings across %d boards" % (scanned, len(board) - len(failed)))
    return failed


def arg(flag, default=None):
    """Value following `flag`, or default. Safe when the flag is last."""
    if flag not in sys.argv:
        return default
    i = sys.argv.index(flag) + 1
    return sys.argv[i] if i < len(sys.argv) else default


def main():
    path = find_index(arg("--index"))
    text = open(path, encoding="utf-8").read()
    cfg = parse_config(text)
    sets = parse_sets(text)

    if not sets:
        sys.exit("no employer tables found in %s. Each set needs a heading plus a "
                 "table with Platform and Slug columns." % path)

    if "--list" in sys.argv:
        print("Sets in %s:" % path)
        for h, b in sets:
            print("  %-40s %d boards" % (h, len(b)))
        return

    wanted = arg("--set")
    if wanted:
        sets = [(h, b) for h, b in sets if wanted.lower() in h.lower()]
        if not sets:
            sys.exit("no set matching %r. Run --list to see them." % wanted)

    seniority = re.compile(cfg["seniority"], re.I)
    function = re.compile(cfg["function"], re.I)
    stretch = re.compile(cfg["stretch"], re.I) if cfg["stretch"] else None
    try:
        floor_k = int(cfg["stretch_comp_floor"])
    except ValueError:
        floor_k = 0

    print("index: %s" % path)
    failed = []
    for heading, board in sets:
        failed += sweep(heading.upper(), board, seniority, function, stretch, floor_k)

    print("-" * 60)
    if failed:
        print("STATUS: INCOMPLETE - unreadable boards: %s" % "; ".join(failed))
        print("        Report this as a coverage gap in the digest.")
        sys.exit(1)
    print("STATUS: COMPLETE - every listed board read.")


if __name__ == "__main__":
    main()
