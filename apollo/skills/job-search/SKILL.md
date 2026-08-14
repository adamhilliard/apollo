---
name: job-search
description: Apollo builds a recurring, self-running job search digest on Claude Code. A setup interview writes a candidate profile, scoring rubric, and tracking files; a scheduled task then sources roles from job boards, ATS site-search, and VC portfolio boards, verifies each posting, scores it against the rubric, and hands back a ranked digest. Use this whenever someone wants to automate, systematize, or keep track of a job search: setting up recurring job alerts, tracking applications, scoring or comparing roles, building a shortlist, or asking Claude to find them jobs on an ongoing basis rather than once. Also use it when maintaining a search already built this way, such as amending the profile, fixing a query that misses roles, adding or retiring a source, or recording a decision so a later cycle stops re-proposing it. Users name their own copy during setup, so treat a personal name they have given their job bot as referring to this skill.
---

# Apollo

A recurring job-search digest that runs itself. The search techniques here are battle-tested and portable; everything candidate-specific comes out of the setup interview.

> **Apollo is the tooling; the user's copy gets its own name.** The interview opens by asking for it, and every file the search writes uses their name from then on. Someone talking about "Scout" or "Wall-E" or just "the bot" means their own search, and this skill is what runs it. Reserve "Apollo" for the tooling itself, and never rename a search that already has a name.

**Works at any career level, from first job to executive search.** The mechanics don't change; the calibration does, and Q0 of the interview sets it.

## What you're building

Four moving pieces. Nothing else.

| Piece | What it is | Who writes it |
|---|---|---|
| **The profile** | Four markdown files holding background, criteria, scoring rubric, standing search rules, and the reasoning behind them. The bot's constitution. | Built once via the setup interview, then amended as rules are learned |
| **Tracking file(s)** | One file per search track. Holds the live results table plus a Search Notes log. | Written and re-sorted by the bot every run |
| **The cycle task** | A recurring Claude Code task that reads the profile, runs the cycle, updates the tracking files, and hands over a digest. | Created once during setup |
| **The weekly audit** | A second task that asks whether the search is mechanically doing what it claims. Scripted, so nothing is self-reported. | Created at setup, starts in week two |

**Why the split matters.** Criteria live in one place and results in another, so a rule change never means editing fifty table rows. The bot reads the profile fresh every run, so amending the profile is how the user steers it.

**Why the profile is four files and not one.** A single profile file grows by accretion: criteria, search mechanics, output conventions, and the origin story behind each rule all interleave, and within a couple of months no section is findable. Split it from day one, because splitting later is a migration and splitting now is free.

**The audit is not optional, and it is not a second digest.** Every silent-failure case this skill documents (a sweep pointed at the wrong host, an API that quietly started truncating, a stem adopted and never added to the query) looked exactly like a quiet week from the inside. **Nothing inside a normal cycle can tell those apart**, because a cycle only sees what its own sources returned.

**The four pieces are the same at every career level.** What changes is calibration: how many results a cycle returns, how deep the per-role research goes, and which questions are even answerable.

## Setting up a new bot

**Ask nothing before the interview starts.** It opens with a short letter and a five-part roadmap, and every question has a home inside it, including the resume, which Part 2 asks for because that is where it gets used. A question asked ahead of the roadmap arrives with no context and cannot be acted on yet.

1. **Run the setup interview.** Read `references/setup-interview.md` and work through it in order, one block at a time. **It opens with the author's letter and the roadmap**, then Part 1 covers the name, palette, cadence, rigor, digest channel, optional integrations, confidential mode, and locale. **None of that blocks setup and every row has a working default.** **Ask with the interactive picker wherever the answer is a small discrete set**, batching up to four questions per call; the interview's "How to ask" block states which questions those are and lists each one's options. Six answers stay free text on purpose, Q8's rubric conversation among them. A blank page produces vague answers, and vague answers produce a generic bot.
2. **Build the files and both scheduled tasks.** Read `references/scaffolding.md` for the folder layout, the four profile skeletons, the read contracts, the locked results-table format, and both task prompts.
3. **Say which answers were thin.** Those are the rules that will need correcting after the first two or three cycles, and naming them upfront sets the expectation that the bot is calibrated rather than born finished.
4. **State the known limitations out loud** from `references/feedback-loop.md`, so nobody mistakes them for bugs. Sourcing is not the bottleneck at every level, and saying so during setup beats letting the bot look ineffective for four cycles.

> **Propose once, then record the answer.** This skill has opinions, and several of its defaults are ones a given user will reject. When they do, write the rejection into their decisions log with their reasoning and stop raising it. A default re-proposed every few cycles is the single most common way this system wastes attention.

## Running a cycle

The scheduled task built in step 2 carries its own prompt. When executing a cycle, read `references/search-techniques.md` for the sourcing and verification rules, and the user's own profile files for what they want.

**Where the two disagree, the user's files win.** They carry that search's vetted verdicts: which sources paid off, which queries were cut and why, which defaults were declined. This skill carries only what generalizes.

**Every cycle reports coverage per source**, in the vocabulary in `search-techniques.md`, with a result count per member of any grouped source and a canary behind any nil. **That logging is not bookkeeping**; it is the only input the weekly audit has, and without it every check in `quality-audit.md` reports blocked.

## Correcting a bot after a cycle

The bot gets meaningfully better around cycle three or four, and only if the loop is closed. Read `references/feedback-loop.md` for the three-tier note-taking split and how a decisions log keeps a decision decided.

**Route the correction by whether it generalizes:**

- **Generic technique** (a source that works, a search operator, a failure mode) belongs in this skill's `references/search-techniques.md`, so every search already running gets the fix.
- **Anything tied to this person** (a threshold, a company, a screening judgment, a comp figure) belongs in their profile, methodology, or procedures, with the reasoning in their decisions log.
- **The test:** would this help a stranger with a different career, in a different field, at a different level? If no, it goes in their files, not here.

## Reference map

Load these as needed; there is no reason to read all of them for a single task.

| File | Read it when | Size |
|---|---|---|
| `references/setup-interview.md` | Setting up a new bot. The picker convention, the customization block, then Q0 through Q12, each naming what it configures. | ~1,440 lines |
| `references/scaffolding.md` | Writing the files and the two task prompts, read contracts, or changing the table format. | ~440 lines |
| `references/search-techniques.md` | Running a cycle, or fixing a search that is missing roles. Integrity rules, sourcing, verification. | ~590 lines |
| `references/quality-audit.md` | The weekly audit only. **No daily cycle reads this.** | ~120 lines |
| `references/feedback-loop.md` | Correcting the bot, writing a decisions-log entry, opening a trial, or stating limitations. | ~85 lines |

## Bundled scripts

| Script | What it does |
|---|---|
| `scripts/linkedin_sweep.py` | Paginates a job-board sweep to exhaustion, dedupes by job ID, and ends with an explicit `COMPLETE` or `INCOMPLETE` status naming what it could not reach. Use it rather than hand-rolling pagination, and surface an `INCOMPLETE` in the digest the way a failed source is surfaced. |
| `scripts/employer_sweep.py` | Sweeps named employers' boards directly, reading its sets out of the user's `Employer_Index.md`. Carries no employer list of its own. |
| `scripts/vc_sweep.py` | Sweeps the Getro-platform VC portfolio boards through the API that actually paginates, and prints a canary line that fails loudly if pagination breaks again. **The documented HTML recipe silently caps at 20 jobs per board**, against boards carrying up to 25,000. |
| `scripts/resolve_boards.py` | Turns a list of company names into confirmed board endpoints, so a named-employer list built at Q6d becomes sweepable without hand-probing dozens of slugs. Verifies employer identity where the platform exposes it. |
| `scripts/quality_audit.py` | The weekly audit. Computes every check in `quality-audit.md` from the user's own files and exits nonzero on a trip. `test_quality_audit.py` covers it. |
| `scripts/jd2pdf.py` | Saves a job description to PDF, so a posting survives being taken down. |

**Prefer a committed script over prose instructions wherever pagination is involved.** Both of the pagination bugs documented in `search-techniques.md` happened to hand-rolled loops written from careful instructions, in a single day. A script that cannot silently truncate is worth more than a rule saying not to.

## Maintaining this skill

**This skill is generic. Nothing about any individual search belongs in it.**

- **Add general improvements only:** a new source, a search operator that works, a technique that generalizes, a failure mode worth warning about.
- **Never add candidate-specific context:** no company names, role titles, scores, comp figures, screening thresholds, or decisions. Those live in the user's own project folder.
- **Illustrative examples are fine when the lesson is general and the detail is incidental** ("a posting that lived 48 hours"), but strip the identifying specifics.

## Related

`/apollo:dashboard` turns the tracking files into a private, self-refreshing web dashboard. Run it after setup and at least one completed cycle. It reads the name from the profile and puts it on the page, so it should run after setup, never before.
