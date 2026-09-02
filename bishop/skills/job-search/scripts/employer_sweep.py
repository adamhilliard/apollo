#!/usr/bin/env python
"""
Direct-employer board sweep: pull a named list of employers' job boards and
filter locally.

Part of Bishop, a free job-search plugin for Claude Code.
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

Supported platforms: greenhouse, lever, ashby, workday, icims. Workday needs
three parts, written `host / tenant / site`, e.g.
`acme.wd5.myworkdayjobs.com / acme / ACMEUS`. Slash-separated, not
pipe-separated: a pipe inside a table cell would break the table.

The icims slug is the tenant, e.g. `acmecareers` reaches
`careers-acmecareers.icims.com`. iCIMS has no public JSON API and its listing
pages are noindex, so keyword search never surfaces its fresh reqs; this is why
an iCIMS employer belongs here and gets fetched from the tenant's own board
HTML rather than an API.

Title filters come from an HTML comment anywhere in the index, so they stay
invisible in the rendered document:

    <!-- sweep-config
    seniority  = manager|supervisor|lead|head of
    function   = operations|logistics|supply chain
    stretch    = (senior )?director
    step_down  = coordinator|associate
    comp_floor = 120
    no_pay     = all
    -->

`function` must match a title, plus one of the level tiers, for a row to be
reported. `seniority` is the target level; `stretch` (optional) is a rung up;
`step_down` (optional) is a rung down.

Comp is read in thousands against `comp_floor`:
  - A stated number below the floor holds a stretch or step_down row back
    (target rows are always reported; the caller screens their floor).
  - A row with NO stated pay is governed by `no_pay`:
      all               show every no-pay row (the default)
      except_step_down  show them except on step_down titles
      none              hold every no-pay row back
Held-back rows are listed separately so nothing disappears silently.
`stretch_comp_floor` is still accepted as an alias for `comp_floor`.

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
from html import unescape

if hasattr(sys.stdout, "reconfigure"):
    # Without this a single non-Latin-1 company name kills the run on Windows,
    # leaving a partial file that reads as complete. That is the exact silent
    # truncation the STATUS line exists to catch.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_SENIORITY = r"."         # match anything; the index should narrow this.
DEFAULT_FUNCTION = r"."          # A shipped default matching only senior titles
                                 # hides every other rung from anyone who never
                                 # writes a sweep-config.

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
           "stretch": "", "step_down": "",
           "comp_floor": "", "stretch_comp_floor": "0",
           "no_pay": "all"}
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


def get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def pull(platform, slug):
    """Return a list of (title, location, comp_summary) or raise.

    comp_summary is whatever the board publishes, or "". An absent value must
    stay an empty string: comp_k reads that as "no number stated", which the
    no_pay rule handles separately from a stated number below the floor.
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
    if platform == "icims":
        # iCIMS has no clean JSON API and its listing pages are noindex, so
        # keyword search misses fresh reqs. The in-iframe search page returns
        # the whole current board server-side, no auth, no JS. slug is the
        # tenant: "acmecareers" -> careers-acmecareers.icims.com. Each job card
        # carries an anchor whose title attribute is "<id> - <Title>" and a
        # "Job Locations" span; paginate on pr until a page adds no new ids.
        out, seen, pr = [], set(), 0
        while pr < 25:
            page = get_text("https://careers-%s.icims.com/jobs/search"
                            "?in_iframe=1&pr=%d" % (slug, pr))
            new = 0
            for card in page.split("iCIMS_JobCardItem")[1:]:
                mt = re.search(r'iCIMS_Anchor"\s+title="(\d+)\s*-\s*([^"]+)"',
                               card)
                if not mt or mt.group(1) in seen:
                    continue
                seen.add(mt.group(1))
                new += 1
                ml = re.search(
                    r"Job Locations</span>\s*<span[^>]*>\s*([^<]+)", card)
                out.append((unescape(mt.group(2)).strip(),
                            unescape(ml.group(1)).strip() if ml else "", ""))
            if new == 0:
                break
            pr += 1
            time.sleep(0.2)
        return out
    raise ValueError("unknown platform %r" % platform)


def comp_k(comp_summary):
    """Highest salary figure in the summary, in thousands, or None when the
    board stated no pay. Absent must read as None, not 0: the no_pay rule and
    the floor test treat "no number" and "a low number" differently.
    """
    if not comp_summary:
        return None
    nums = [int(m.group(1)) for m in re.finditer(r"\$(\d{3})K", comp_summary, re.I)]
    nums += [int(m.group(1).replace(",", "")) // 1000
             for m in re.finditer(r"\$(\d{3},\d{3})", comp_summary)]
    return max(nums) if nums else None


def classify(tier, comp_summary, floor_k, no_pay):
    """Return 'hit' (report the row) or 'held' (list it under held-back, never
    drop it). tier is 'target', 'step_up', or 'step_down'.
    """
    k = comp_k(comp_summary)
    if k is not None:
        # A stated number. Target rows are always reported (the caller screens
        # their floor); an off-target row must clear the floor to earn a spot.
        if tier == "target" or floor_k <= 0 or k >= floor_k:
            return "hit"
        return "held"
    # No stated pay: the user's no_pay choice decides.
    if no_pay == "none":
        return "held"
    if no_pay == "except_step_down" and tier == "step_down":
        return "held"
    return "hit"


# --------------------------------------------------------------------------
# Sweeping
# --------------------------------------------------------------------------

def sweep(name, board, seniority, function, stretch, step_down, floor_k, no_pay):
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
                tier = "target"
            elif stretch and stretch.search(title):
                tier = "step_up"
            elif step_down and step_down.search(title):
                tier = "step_down"
            else:
                continue
            if classify(tier, comp, floor_k, no_pay) == "hit":
                hits.append((company, title, loc, comp or ""))
            else:
                held.append((company, title, tier, comp or "no pay posted"))
        time.sleep(0.2)

    for c, t, l, comp in sorted(hits):
        print("  %-22s | %-52s | %-26s | %s" % (c, t[:52], l[:26], comp[:28]))
    if not hits:
        print("  (no target-title matches)")
    if held:
        print("  -- %d off-target rows held back (below the $%dK floor, or no pay "
              "posted under no_pay=%s):" % (len(held), floor_k, no_pay))
        for c, t, tier, reason in sorted(held):
            print("       %-20s | %-40s | %-9s | %s" % (c, t[:40], tier, reason[:24]))
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
    step_down = re.compile(cfg["step_down"], re.I) if cfg["step_down"] else None
    try:
        floor_k = int(cfg["comp_floor"] or cfg["stretch_comp_floor"])
    except ValueError:
        floor_k = 0
    no_pay = cfg["no_pay"].strip().lower()
    if no_pay not in ("all", "except_step_down", "none"):
        no_pay = "all"

    print("index: %s" % path)
    failed = []
    for heading, board in sets:
        failed += sweep(heading.upper(), board, seniority, function, stretch,
                        step_down, floor_k, no_pay)

    print("-" * 60)
    if failed:
        print("STATUS: INCOMPLETE - unreadable boards: %s" % "; ".join(failed))
        print("        Report this as a coverage gap in the digest.")
        sys.exit(1)
    print("STATUS: COMPLETE - every listed board read.")


if __name__ == "__main__":
    main()
