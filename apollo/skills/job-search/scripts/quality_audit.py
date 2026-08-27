# -*- coding: utf-8 -*-
"""Weekly quality audit.  Apollo, by Adam Hilliard (MIT).

Answers one question: is this search mechanically doing what it claims to be
doing? Not "are the files tidy" - a perfectly formatted file set sweeping the
wrong host passes that review and fails this one.

Every number here is computed from the files. Nothing is self-reported, because
self-reported success is the thing being detected. Exits 1 if any check trips,
so a scheduled run cannot pass silently.

    python quality_audit.py --project /path/to/search [--prompt ~/.../SKILL.md]

Reads, when present:
    Tracking_*.md      the Search Notes COVERAGE / CANARY lines (see scaffolding.md)
    Methodology.md     documented stems vs. the live query strings
    Decisions_Log.md   the Open Trials table
    Index_*.md         dedupe index, cross-checked against the archive
    the prompt file    checked for rules it does not own

Checks with no input available report "blocked", never "ok". A check that
cannot see its data has not passed.
"""

from __future__ import print_function

import argparse
import datetime
import glob
import io
import os
import re
import sys

ROUND_NUMBERS = (20, 25, 50, 100, 250, 500, 750, 1000)
STATUSES = ("COMPLETE", "INCOMPLETE", "SAMPLED", "FAILED", "OFF-CADENCE", "CUT")
DEFAULT_READ_BUDGET_KB = 200

# Hosts a role's apply link can sit on, for the cross-surface check (S8).
ATS_HOSTS = {
    "lever": "jobs.lever.co", "greenhouse": "greenhouse.io", "ashby": "ashbyhq.com",
    "workday": "myworkdayjobs.com", "workable": "apply.workable.com",
    "smartrecruiters": "smartrecruiters.com", "rippling": "ats.rippling.com",
    "icims": "icims.com", "bamboohr": "bamboohr.com", "jazzhr": "applytojob.com",
    "adp": "adp.com", "paylocity": "recruiting.paylocity.com",
    "paycom": "paycomonline.net", "dayforce": "dayforcehcm.com",
    "ukg": "recruiting.ultipro.com", "breezy": "breezy.hr", "gem": "jobs.gem.com",
    "taleo": "taleo.net", "oracle": "oraclecloud.com", "cornerstone": "csod.com",
    "avature": "avature.net", "eightfold": "eightfold.ai",
    "teamtailor": "teamtailor.com",
}

trips = []


def trip(check, msg):
    trips.append((check, msg))
    print("  [TRIP %-3s] %s" % (check, msg))


def ok(check, msg):
    print("  [ ok  %-3s] %s" % (check, msg))


def blocked(check, msg):
    print("  [blkd %-3s] %s" % (check, msg))


def section(title):
    print("\n" + title)
    print("-" * len(title))


def read(path):
    try:
        return io.open(path, encoding="utf-8").read()
    except (IOError, OSError):
        return u""


# --------------------------------------------------------------- parsing

ENTRY = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b", re.M)
COUNT = re.compile(r"^(\d+)(?:/(\d+))?$")


def parse_member(token):
    """'lever 6' -> ('lever', 6, None, 6). 'getro 412/10976 INCOMPLETE' ->
    ('getro', 412, 10976, 'INCOMPLETE'). Returns None if unparseable."""
    words = token.strip().split()
    if not words:
        return None
    name = words[0].strip(":").lower()
    got = claimed = None
    status = None
    for w in words[1:]:
        up = w.upper().strip(",")
        if up in STATUSES or up.startswith("CUT"):
            status = up
            continue
        m = COUNT.match(w.strip(",()"))
        if m:
            got = int(m.group(1))
            if m.group(2):
                claimed = int(m.group(2))
    return {"name": name, "got": got, "claimed": claimed, "status": status}


def parse_cycles(text):
    """Split a tracking file's Search Notes into dated entries with their
    COVERAGE and CANARY lines. Newest last."""
    cycles = []
    marks = list(ENTRY.finditer(text))
    for i, m in enumerate(marks):
        body = text[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        cov, can = [], {}
        for line in body.splitlines():
            s = line.strip()
            if s.upper().startswith("COVERAGE:"):
                for tok in s.split(":", 1)[1].split(u"·"):
                    p = parse_member(tok)
                    if p and p["name"]:
                        cov.append(p)
            elif s.upper().startswith("CANARY:"):
                for tok in s.split(":", 1)[1].split(u"·"):
                    w = tok.strip().split()
                    if len(w) >= 2:
                        can[w[0].lower()] = w[1].upper()
        if cov or can:
            cycles.append({"date": m.group(1), "coverage": cov, "canary": can})
    return cycles


def series(cycles, name):
    """Per-cycle counts for one member, oldest first, skipping cycles where it
    did not appear or was off cadence."""
    out = []
    for c in cycles:
        for m in c["coverage"]:
            if m["name"] == name and m["status"] != "OFF-CADENCE":
                out.append(m)
    return out


# --------------------------------------------------------------- checks

def silent_failure(cycles):
    section("3. SILENT FAILURE  (nothing was there, or I did not look?)")
    if not cycles:
        for cid in ("S1", "S2", "S3", "S4", "S5", "S6", "S7"):
            blocked(cid, "no COVERAGE lines found in any Tracking_*.md")
        return
    names = []
    for c in cycles:
        for m in c["coverage"]:
            if m["name"] not in names:
                names.append(m["name"])

    # S1 per-member liveness
    dead = []
    for n in names:
        s = series(cycles, n)[-3:]
        if len(s) == 3 and all((m["got"] or 0) == 0 for m in s):
            peers = [p for p in names if p != n and
                     any((m["got"] or 0) > 0 for m in series(cycles, p)[-3:])]
            if peers:
                dead.append(n)
    if dead:
        trip("S1", "at zero 3+ cycles while peers returned results: %s" % ", ".join(dead))
    else:
        ok("S1", "%d members, none dark for 3 cycles" % len(names))

    # S2 round-number counts
    hits = []
    for m in cycles[-1]["coverage"]:
        got, claimed = m["got"], m["claimed"]
        if got in ROUND_NUMBERS and (claimed is None or claimed > got * 2):
            hits.append("%s=%d" % (m["name"], got))
    if hits:
        trip("S2", "truncation signature, exactly round against a large inventory: %s"
             % ", ".join(hits))
    else:
        ok("S2", "no round-number counts this cycle")

    # S3 trend break
    broke = []
    for n in names:
        s = series(cycles, n)
        if len(s) >= 5 and (s[-1]["got"] or 0) == 0:
            prior = [m["got"] or 0 for m in s[-5:-1]]
            if all(p > 0 for p in prior):
                broke.append("%s (was %s)" % (n, "/".join(str(p) for p in prior)))
    if broke:
        trip("S3", "averaged above zero for 4+ cycles and hit exactly zero: %s"
             % "; ".join(broke))
    else:
        ok("S3", "no source dropped from a steady rate to zero")

    # S4 unvouched nils, rising
    def unvouched(c):
        return [m["name"] for m in c["coverage"]
                if (m["got"] or 0) == 0 and m["status"] != "OFF-CADENCE"
                and m["name"] not in c["canary"]]
    counts = [len(unvouched(c)) for c in cycles[-3:]]
    if len(counts) == 3 and counts[0] < counts[1] < counts[2]:
        trip("S4", "unvouched nils rising: %s" % " -> ".join(str(c) for c in counts))
    else:
        ok("S4", "unvouched nils this cycle: %d" % (counts[-1] if counts else 0))

    # S5 canary debt
    owed = {}
    for c in cycles:
        for n, v in c["canary"].items():
            if v in ("OWED", "DUE", "PENDING"):
                owed.setdefault(n, c["date"])
            elif n in owed:
                del owed[n]
    if owed:
        trip("S5", "canary owed: %s" % ", ".join("%s since %s" % kv for kv in owed.items()))
    else:
        ok("S5", "no canary debt")

    # S6 success either way
    bad = []
    for n in names:
        s = series(cycles, n)[-3:]
        if len(s) == 3 and all(m["status"] == "COMPLETE" and (m["got"] or 0) == 0
                               for m in s):
            bad.append(n)
    if bad:
        trip("S6", "reporting COMPLETE at zero results 3 cycles running: %s"
             % ", ".join(bad))
    else:
        ok("S6", "no source reporting success either way")

    # S7 canary passes, query never does
    bad = []
    for n in names:
        s = series(cycles, n)[-4:]
        passes = [c["canary"].get(n) == "PASS" for c in cycles[-4:]]
        if len(s) == 4 and all((m["got"] or 0) == 0 for m in s) and any(passes):
            bad.append(n)
    if bad:
        trip("S7", "canary passes and the real query never returns: %s" % ", ".join(bad))
    else:
        ok("S7", "no source live-but-unqueried")


def cross_surface(cycles, tracking_text):
    if not cycles:
        blocked("S8", "no COVERAGE lines to compare against")
        return
    last = {m["name"]: (m["got"] or 0) for m in cycles[-1]["coverage"]}
    found = set()
    for member, host in ATS_HOSTS.items():
        if host in tracking_text and last.get(member) == 0:
            found.add("%s (a live row sits on %s)" % (member, host))
    if found:
        trip("S8", "swept and returned nothing, yet a tracked role lives there: %s"
             % "; ".join(sorted(found)))
    else:
        ok("S8", "no source contradicted by a tracked role's apply link")


def execution(project, prompt_path, budget_kb):
    section("4. EXECUTION INTEGRITY  (does what runs match what is written?)")
    meth = read(os.path.join(project, "Methodology.md"))

    # E1 documented stems present in the live query strings
    stems = []
    for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|", meth, re.M):
        stems.append(m.group(1).strip())
    queries = u" ".join(re.findall(r"```(.*?)```", meth, re.S))
    if not stems:
        blocked("E1", "no stem table in Methodology.md (rows shaped `| \\`stem\\` | ... |`)")
    elif not queries.strip():
        blocked("E1", "no fenced query strings in Methodology.md")
    else:
        missing = [s for s in stems if s.lower() not in queries.lower()]
        if missing:
            trip("E1", "documented and NOT in any query string: %s" % ", ".join(missing))
        else:
            ok("E1", "all %d documented stems present in the query strings" % len(stems))

    # E2 a figure stated in two files must agree
    claims = {}
    historical = ("Decisions_Log.md", "Audit_Log.md")
    for path in glob.glob(os.path.join(project, "*.md")):
        if os.path.basename(path) in historical:
            continue                      # superseded numbers there are the point
        text = read(path)
        for m in re.finditer(r"\b(\d+)\s+(hosts|boards|sources|tracks)\b", text):
            claims.setdefault(m.group(2), {}).setdefault(m.group(1), set()).add(
                os.path.basename(path))
    conflicts = ["%s: %s" % (noun, ", ".join("%s in %s" % (v, "/".join(sorted(f)))
                                             for v, f in vals.items()))
                 for noun, vals in claims.items() if len(vals) > 1]
    if conflicts:
        trip("E2", "the same count stated differently in different files: %s"
             % "; ".join(conflicts))
    elif claims:
        ok("E2", "%d cross-file counts agree" % len(claims))
    else:
        blocked("E2", "no cross-file counts to compare")

    # E3 the prompt states no rule it does not own
    if not prompt_path:
        blocked("E3", "no --prompt path given; the scheduled prompt is unchecked")
    else:
        ptext = read(os.path.expanduser(prompt_path))
        if not ptext:
            blocked("E3", "prompt not readable at %s" % prompt_path)
        else:
            leaks = []
            if re.search(r"\$\s?\d{2,3}[,kK]", ptext):
                leaks.append("a comp figure")
            if re.search(r"(?i)\b(mon|tues|wednes|thurs|fri|satur|sun)day\b.*\+", ptext):
                leaks.append("a cadence table")
            hosts = [h for h in set(ATS_HOSTS.values()) if h in ptext]
            if hosts:
                leaks.append("host names (%s)" % ", ".join(sorted(hosts)[:3]))
            if re.search(r'"[A-Z][A-Za-z ]{4,}"\s+OR\s+"', ptext):
                leaks.append("query stems")
            if leaks:
                trip("E3", "the prompt restates rules it does not own: %s"
                     % "; ".join(leaks))
            else:
                ok("E3", "the prompt states no rule it does not own")

    # E4 per-cycle read budget
    hot = ["Reference_Profile.md", "Methodology.md", "Operating_Procedures.md"]
    hot += [os.path.basename(p) for p in glob.glob(os.path.join(project, "Tracking_*.md"))]
    total = sum(os.path.getsize(os.path.join(project, f))
                for f in hot if os.path.exists(os.path.join(project, f)))
    kb = total / 1024.0
    if not total:
        blocked("E4", "none of the per-cycle files found in %s" % project)
    elif kb > budget_kb:
        trip("E4", "per-cycle read is %.0f KB against a %d KB budget; split the "
                   "largest tracking file (see scaffolding.md)" % (kb, budget_kb))
    else:
        ok("E4", "per-cycle read %.0f KB of %d KB" % (kb, budget_kb))

    # E5 open trials have a review date, and none is overdue
    log = read(os.path.join(project, "Decisions_Log.md"))
    m = re.search(r"^##\s+Open Trials\s*$(.*?)(?=^##\s|\Z)", log, re.M | re.S)
    if not m:
        blocked("E5", "no Open Trials section in Decisions_Log.md")
    else:
        rows = [r for r in m.group(1).splitlines()
                if r.strip().startswith("|") and "---" not in r]
        header = [c.strip().lower() for c in rows[0].strip().strip("|").split("|")] if rows else []
        due_col = next((i for i, h in enumerate(header) if "due" in h or "review" in h), None)
        rows = [r for r in rows[1:] if r.strip("| ").strip()]
        today = datetime.date.today()
        undated, overdue = [], []
        for r in rows:
            cells = [c.strip() for c in r.strip().strip("|").split("|")]
            name = cells[0] if cells else "?"
            search_in = ([cells[due_col]] if due_col is not None and due_col < len(cells)
                         else cells)
            due = None
            for c in search_in:
                d = re.search(r"(\d{4})-(\d{2})-(\d{2})", c)
                if d:
                    due = datetime.date(*(int(x) for x in d.groups()))
                    break
            if due is None:
                undated.append(name)
            elif due < today:
                overdue.append("%s (due %s)" % (name, due))
        if undated:
            trip("E5", "trial with no review date, which is a permanent rule "
                       "nobody voted for: %s" % ", ".join(undated))
        if overdue:
            trip("E5", "trial past its review date: %s" % ", ".join(overdue))
        if not undated and not overdue:
            ok("E5", "%d open trial(s), all dated and current" % len(rows))

    # E7 the reliability gate ran. A clean gate writes nothing, so a skipped
    # week and a quiet week produce the same tracking file. The GATE count in
    # the Search Notes log is the only artifact that separates them.
    notes, entries = [], []
    for path in glob.glob(os.path.join(project, "Tracking_*.md")):
        notes.append(read(path))
    for text in notes:
        entries += re.split(r"^###\s+", text, flags=re.M)[1:]
    scored = [e for e in entries if re.search(r"^COVERAGE:", e, re.M)]
    with_gate = [e for e in scored if re.search(r"^GATE:", e, re.M)]
    if not scored:
        blocked("E7", "no Search Notes entries found; nothing to check")
    elif not with_gate:
        blocked("E7", "no entry reports a GATE line yet; the gate is not in use "
                      "on this search (see search-techniques.md)")
    else:
        gaps = []
        for e in scored:
            head = e.splitlines()[0][:40] if e.splitlines() else "?"
            m = re.search(r"^EVENTS:.*?(\d+)\s+new", e, re.M)
            added = int(m.group(1)) if m else 0
            if added and not re.search(r"^GATE:", e, re.M):
                gaps.append(head)
        if gaps:
            trip("E7", "entr(ies) added rows with no GATE count, so a skipped gate "
                       "is indistinguishable from a clean one: %s" % ", ".join(gaps))
        else:
            ok("E7", "%d of %d entries report a gate count; every entry adding a "
                     "row has one" % (len(with_gate), len(scored)))

    # E8 the resolver ran. Same argument as E7 one surface over: a cycle
    # where every link resolved live and a cycle where the resolver never ran
    # produce identical tables. The RESOLVE count is the only separator.
    with_resolve = [e for e in scored if re.search(r"^RESOLVE:", e, re.M)]
    if not scored:
        blocked("E8", "no Search Notes entries found; nothing to check")
    elif not with_resolve:
        blocked("E8", "no entry reports a RESOLVE line yet; link resolution is "
                      "not in use on this search (see search-techniques.md)")
    else:
        gaps, untrusted = [], []
        for e in scored:
            head = e.splitlines()[0][:40] if e.splitlines() else "?"
            m = re.search(r"^EVENTS:.*?(\d+)\s+new", e, re.M)
            added = int(m.group(1)) if m else 0
            r = re.search(r"^RESOLVE:\s*(.+)$", e, re.M)
            if added and not r:
                gaps.append(head)
            elif r and re.search(r"canary\s*(fail|none)", r.group(1), re.I):
                untrusted.append(head)
        if gaps:
            trip("E8", "entr(ies) added rows with no RESOLVE count, so an "
                       "unrun resolver is indistinguishable from a clean one: "
                       "%s" % ", ".join(gaps))
        elif untrusted:
            trip("E8", "entr(ies) resolved without a passing canary, so no "
                       "expiry that cycle can be trusted: %s"
                       % ", ".join(untrusted))
        else:
            ok("E8", "%d of %d entries report a resolve count; every entry "
                     "adding a row has one" % (len(with_resolve), len(scored)))

    # E6 index and archive agree, once a tracking file has been split
    idx = glob.glob(os.path.join(project, "Index_*.md"))
    if not idx:
        blocked("E6", "no Index_*.md; the tracking file has not been split yet")
    else:
        for path in idx:
            track = os.path.basename(path).replace("Index_", "")
            arch = os.path.join(project, "Archived_" + track)
            if not os.path.exists(arch):
                trip("E6", "%s has no matching Archived_%s" % (os.path.basename(path), track))
                continue
            refs = set(re.findall(r"#([a-z0-9\-]{4,})", read(path)))
            anchors = set(re.findall(r'<a id="([a-z0-9\-]+)"', read(arch)))
            orphan_refs = refs - anchors
            orphan_anchors = anchors - refs
            if orphan_refs or orphan_anchors:
                trip("E6", "%s: %d index lines point at nothing, %d archived rows "
                           "have no index line" % (track, len(orphan_refs), len(orphan_anchors)))
            else:
                ok("E6", "%s: %d index lines, all resolving" % (track, len(refs)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".", help="the search's project folder")
    ap.add_argument("--prompt", help="path to the scheduled-task prompt file")
    ap.add_argument("--budget-kb", type=int, default=DEFAULT_READ_BUDGET_KB,
                    help="per-cycle read budget in KB (default %d)" % DEFAULT_READ_BUDGET_KB)
    args = ap.parse_args()
    project = os.path.abspath(args.project)

    print("QUALITY AUDIT  %s  %s" % (datetime.date.today().isoformat(), project))

    tracking = sorted(glob.glob(os.path.join(project, "Tracking_*.md")))
    text = u"".join(read(p) for p in tracking)
    cycles = parse_cycles(text)
    print("read %d tracking file(s), %d logged cycle(s)" % (len(tracking), len(cycles)))

    silent_failure(cycles)
    cross_surface(cycles, text)
    execution(project, args.prompt, args.budget_kb)

    section("RESULT")
    if trips:
        print("%d check(s) tripped:" % len(trips))
        for cid, msg in trips:
            print("  %s  %s" % (cid, msg))
        print("\nEach one becomes a decisions-log entry if it changes a rule, "
              "never a paragraph in the audit log.")
        return 1
    print("clean. Write one row in the audit log and stop.")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    sys.exit(main())
