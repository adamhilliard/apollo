# The Quality Audit

**Is the search mechanically doing what it claims to be doing?** Runs once a week, on its own schedule. **No daily cycle reads this file.**

> **The target is one thing: a broken recipe that reports success.** Every case below looked exactly like a clean nil from the inside, and every one survived for weeks or months.

| Case | How long it reported success |
|---|---|
| An ATS host sweeping the vendor's own marketing site | Unknown, many cycles |
| Three more hosts pointed at vendor pages, logged as dead markets | Unknown |
| A board API returning 20 rows against boards carrying 25,000 | Until instrumented |
| A title stem documented, adopted, and never added to the query string | Two weeks, cost the best-paying role on the board |
| A scheduled prompt reverting a cadence decision hours after it was made | Until measured |

> **This is not a documentation review.** That kind of audit asks whether the files are tidy. **A perfectly formatted file set sweeping the wrong host passes that audit and fails this one.**

---

## 1. What counts as a failure

**Three things look similar in the files and are completely different. Conflating them makes the audit punish a working search.**

| Category | Example | Verdict |
|---|---|---|
| **Market movement** | A requisition closes. A role is filled. The user applies elsewhere first | **Not a failure.** No threshold, no finding |
| **Learning** | A posting reveals a title form no stem matched, and the stem gets added | **Progress.** Logged as a gain, never as a miss |
| **Mechanical failure** | A source reports `COMPLETE` while reading the wrong host | **The entire point of this file** |

- **A stem added because a real posting revealed it is the taxonomy working as designed.** The query set is built to grow a stem at a time.
- **The one recall case that is a defect is a rule that existed and did not execute.** The stem wasn't missing. It was missing from the thing that runs.
- **Expiry gets no failure threshold.** Penalising a requisition that closes days after it was found pushes the search toward surfacing fewer, staler roles, and recruiter-anonymous postings can close in two days. **The one exception is severe:** a freshness pass that vouched for a requisition later found already dead at that date is the same defect class as a broken sweep.

---

## 2. How it runs

**Its own weekly task, on the main thread.**

| Step | What |
|---|---|
| 1 | Run `scripts/quality_audit.py`, which computes every scripted check from the files |
| 2 | Run the live probe in §4, which needs the network and can't be scripted |
| 3 | Append one row to the audit log. Write prose only where a check tripped |
| 4 | Anything that changes a rule becomes a decisions-log entry, **never a paragraph here** |

- **The script is the point, not the file.** A prose audit is a rule that doesn't execute wearing a new hat, so every check is computed from the files and none is self-reported. It exits nonzero when a check trips.
- **Never delegate this to a sub-agent.** Detecting self-reported success is the job, and a sub-agent reporting "coverage looks good" is the thing being detected.
- **A clean week writes one row and stops.** No recap, no narrative.
- **If a check can't be computed from the files, it isn't a check yet.** Park it, and say why.

---

## 3. Silent-failure checks

**Every check here exists to distinguish *nothing was there* from *I didn't look*.** They all read the per-source status lines and per-member counts that `search-techniques.md` rules 2 and 4 require in the cycle notes. **Without those lines none of this computes**, which is why the logging rule comes first.

| ID | Check | Trips when | Catches |
|---|---|---|---|
| **S1** | **Per-member liveness.** Cycles since each member of a grouped source last returned any parseable result | 3+ cycles at zero while peers return results | A wrong address reading as a dead market |
| **S2** | **Round-number counts.** Any reported count of exactly 20, 25, 50, 100, 250, 500, 750, 1000 | Any | Pagination caps reported as exhaustion |
| **S3** | **Trend break.** A source averaging above zero for 4+ weeks that drops to exactly zero | Any | Recipe decay. Markets decline; they don't hit exactly zero |
| **S4** | **Unvouched nils.** Nils reported with no canary behind them | Rising two weeks running | Accumulating unverifiable claims |
| **S5** | **Canary debt.** Canaries owed, and for how long | Older than 14 days | A source whose nils nobody can vouch for |
| **S6** | **Success either way.** A source reporting `COMPLETE` at zero parseable results 3+ weeks running | Any | The defect that reports success regardless of outcome |
| **S7** | **Canary passes, query never does.** Source live 4+ weeks with a passing canary and an always-empty real query | Any | The source works and the query is wrong. Different fix from S1 |
| **S8** | **Cross-surface contradiction.** A role found on one surface whose host was swept the same cycle and returned nothing | Any | Direct proof a sweep is blind |

> **S8 is the strongest test available and the cheapest to overlook.** Any role another source surfaced that lives on a host the ATS sweep claims to cover is, by definition, invisible to that sweep. **The two observations contradict each other, and nothing in a normal cycle ever compares them.**

> **S1 measures liveness, not yield.** A healthy source can produce zero *tracked roles* for months; that's a market fact, and source tiering handles it. A source producing zero *parseable results* is broken. Conflating those is how a working source gets demoted and a broken one survives.

### Execution-integrity checks

**These hunt the rule that exists and doesn't run.**

| ID | Check | Trips when |
|---|---|---|
| **E1** | Every stem documented in the methodology appears in the actual query string | Any documented stem is absent |
| **E2** | Any figure stated in more than one file agrees across all copies | Two copies disagree |
| **E3** | The scheduled-task prompt restates no rule it doesn't own | The prompt contains a threshold, cadence table, or host list |
| **E4** | Every file's stated read budget matches its actual size | A per-cycle file exceeds its budget |
| **E5** | Every trial in the decisions log has a review date, and none is overdue | A trial is past due, or has no date |
| **E6** | Every tracking-file row has an index line, and every index line a row | Either side is orphaned |

> **E1 is the check that would have caught the two-week miss.** "Every documented stem is in the query string" is a reading exercise against prose and a mechanical diff against a table. **Keep stem families in a table for that reason alone.**

---

## 4. The live probe

**Per-source canaries prove a source answers. They do not prove the query set would find a role the user wants.** Budget ten minutes.

1. **Pick 3 qualifying roles the search did not source**, from this week or the past month. The user's own manual finds are the best material.
2. **Run the current query set at them.**
3. **Record `n/3 reached`, and classify every miss:**

| Classification | Meaning | Action |
|---|---|---|
| **Reached** | The query set works. It was timing | None |
| **Reachable, wrong cadence** | A source that covers it ran on a different day | Check the tier |
| **No stem matches** | A title form nothing in the query set can reach | **Learning.** Add the stem, log it as a gain |
| **Source not covered** | Nothing in the source list carries this employer's postings | Candidate for a new source |
| **Structurally unreachable** | The employer's ATS gates every requisition | **State the gap.** Don't chase it |

---

## 5. The audit log

One row per week. **Prose only where something tripped.**

```markdown
| Date | Checks run | Tripped | Probe | Note |
|---|---|---|---|---|
| {{DATE}} | 14 | S5, E1 | 2/3 | Canary owed 3 weeks on two hosts; one stem missing from the query string |
```

- **A finding that changes a rule leaves as a decisions-log entry**, and this row keeps only the pointer.
- **Never write a conclusion the script didn't compute.** "Coverage looks healthy" is the sentence this whole file exists to distrust.
