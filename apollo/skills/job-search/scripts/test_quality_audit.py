# -*- coding: utf-8 -*-
"""Tests for quality_audit.py.  Apollo, by Adam Hilliard (MIT).

    python test_quality_audit.py

Each case builds a throwaway project folder that contains exactly one defect,
then asserts the matching check trips and that a clean folder trips nothing.
The audit exists to catch a broken recipe reporting success, so an audit that
silently stops checking is the same failure one level up.
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, "quality_audit.py")

CLEAN_CYCLES = u"""
### 2026-08-04 · cycle 1
COVERAGE: linkedin COMPLETE 933 · lever 6 · icims 3
CANARY: icims PASS

### 2026-08-05 · cycle 2
COVERAGE: linkedin COMPLETE 901 · lever 7 · icims 4
CANARY: icims PASS

### 2026-08-06 · cycle 3
COVERAGE: linkedin COMPLETE 880 · lever 5 · icims 2
CANARY: icims PASS
"""

GATE_CYCLES = u"""
### 2026-08-04 · cycle 1
COVERAGE: linkedin COMPLETE 933 · lever 6 · icims 3
CANARY: icims PASS
EVENTS: 2 new · 0 expired
GATE: 2 assessed · 0 flagged

### 2026-08-05 · cycle 2
COVERAGE: linkedin COMPLETE 901 · lever 7 · icims 4
CANARY: icims PASS
EVENTS: 3 new · 1 expired
"""

RESOLVE_CYCLES = u"""
### 2026-08-04 · cycle 1
COVERAGE: linkedin COMPLETE 933 · lever 6 · icims 3
CANARY: icims PASS
EVENTS: 2 new · 0 expired
GATE: 2 assessed · 0 flagged
RESOLVE: 12 read · 10 live · 2 expired · 0 unverified · canary PASS

### 2026-08-05 · cycle 2
COVERAGE: linkedin COMPLETE 901 · lever 7 · icims 4
CANARY: icims PASS
EVENTS: 3 new · 1 expired
GATE: 3 assessed · 0 flagged
"""

RESOLVE_LINE = (u"RESOLVE: 12 read · 10 live · 2 expired · 0 unverified"
                u" · canary PASS\n")

METHODOLOGY = u"""# Methodology

### Queries

| Stem | Filter to | State |
|---|---|---|
| `"Operations Manager"` | mid | live |

```
"Operations Manager"
```
"""

DECISIONS = u"""# Decisions Log

## Open Trials

| Trial | Opened | Review due | Kill criteria | Status |
|---|---|---|---|---|
| A stem family | 2026-08-01 | 2099-01-01 | flood | open |

## T · Targets and Scope
"""


def build(tmp, cycles=CLEAN_CYCLES, methodology=METHODOLOGY, decisions=DECISIONS,
          apply_link=u"https://boards.greenhouse.io/acme/jobs/1"):
    def w(name, text):
        io.open(os.path.join(tmp, name), "w", encoding="utf-8").write(text)
    w("Reference_Profile.md", u"# Profile\n")
    w("Operating_Procedures.md", u"# Procedures\n")
    w("Methodology.md", methodology)
    w("Decisions_Log.md", decisions)
    w("Tracking_HR.md", u"# Tracking\n\n## ACTIVE/ROLLING\n\n| Score | Apply |\n"
                        u"|---|---|\n| 4/6 | %s |\n\n## Search Notes\n%s"
                        % (apply_link, cycles))


def run(tmp, *extra):
    p = subprocess.run([sys.executable, AUDIT, "--project", tmp] + list(extra),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def case(name, expect_trip, **kw):
    tmp = tempfile.mkdtemp()
    try:
        extra = kw.pop("extra", ())
        build(tmp, **kw)
        code, out = run(tmp, *extra)
        tripped = [ln.split("]")[0].split()[-1] for ln in out.splitlines() if "[TRIP" in ln]
        if expect_trip is None:
            assert code == 0, "%s: expected clean, got trips %s\n%s" % (name, tripped, out)
        else:
            assert expect_trip in tripped, ("%s: expected %s to trip, got %s\n%s"
                                            % (name, expect_trip, tripped, out))
            assert code == 1, "%s: trips must exit 1" % name
        print("  ok  %-28s %s" % (name, expect_trip or "clean"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("quality_audit self-test")

    case("clean project", None)

    case("member dark 3 cycles", "S1", cycles=CLEAN_CYCLES.replace(
        u"icims 3", u"icims 0").replace(u"icims 4", u"icims 0").replace(u"icims 2", u"icims 0"),
        apply_link=u"https://example.com/1")

    case("round-number count", "S2",
         cycles=CLEAN_CYCLES.replace(u"linkedin COMPLETE 880", u"getro 20/25000"))

    # Owed on the most recent cycle. Owed-then-passed is debt cleared, not debt.
    head, _, tail = CLEAN_CYCLES.rpartition(u"CANARY: icims PASS")
    case("canary owed", "S5", cycles=head + u"CANARY: icims OWED" + tail)

    case("COMPLETE at zero", "S6", cycles=CLEAN_CYCLES
         .replace(u"icims 3", u"icims 0 COMPLETE")
         .replace(u"icims 4", u"icims 0 COMPLETE")
         .replace(u"icims 2", u"icims 0 COMPLETE"),
         apply_link=u"https://example.com/1")

    case("role on a source that swept empty", "S8", cycles=CLEAN_CYCLES
         .replace(u"lever 6", u"greenhouse 0").replace(u"lever 7", u"greenhouse 0")
         .replace(u"lever 5", u"greenhouse 0"))

    case("stem documented, not in query", "E1", methodology=METHODOLOGY.replace(
        u'```\n"Operations Manager"\n```', u'```\n"Director of Operations"\n```'))

    case("trial with no review date", "E5", decisions=DECISIONS.replace(
        u"2099-01-01", u"after two cycles"))

    case("trial overdue", "E5", decisions=DECISIONS.replace(u"2099-01-01", u"2020-01-01"))

    # E7: cycle 2 added rows and reported no gate count, while cycle 1 did.
    # A gate that finds nothing and a gate that never ran write the same file.
    case("gate not reported on a cycle that added rows", "E7", cycles=GATE_CYCLES)

    # ...but a search that has never adopted the gate is blocked, not failed.
    case("gate never adopted", None, cycles=GATE_CYCLES.replace(
        u"GATE: 2 assessed · 0 flagged\n", u""))

    # E8: cycle 2 added rows and reported no resolve count. Same argument as
    # E7 one surface over: an unrun resolver and a clean one write the same
    # table, and the table is the thing the user clicks.
    case("resolver not reported on a cycle that added rows", "E8",
         cycles=RESOLVE_CYCLES)

    # A search that has never adopted the resolver is blocked, not failed.
    case("resolver never adopted", None,
         cycles=RESOLVE_CYCLES.replace(RESOLVE_LINE, u""))

    # An expiry behind a failed canary is a reachability problem wearing a
    # market event's clothes, so a reported-but-untrusted run still trips.
    case("resolver ran without a passing canary", "E8",
         cycles=RESOLVE_CYCLES.replace(
             u"GATE: 3 assessed · 0 flagged",
             u"GATE: 3 assessed · 0 flagged\n"
             u"RESOLVE: 9 read · 0 live · 0 expired · 9 unverified"
             u" · canary FAIL"))

    print("all cases passed")


if __name__ == "__main__":
    main()
