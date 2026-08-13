# Apollo

A Claude Code plugin that builds and runs a recurring job search: a setup interview writes the candidate's profile and scoring rubric, then a scheduled task sources roles, verifies each posting, scores it, and hands back a ranked digest. Ships with an optional private web dashboard.

Free to use. Intended for job seekers at any career level.

**Apollo names the tooling, not the user's search.** The setup interview opens by asking each user what to call their copy, before any configuration question, and every file the search writes uses that name. This matters more than it sounds: without it, "the bot" means both the product and their instance of it, and every later conversation has to disambiguate.

## Layout

```
.claude-plugin/marketplace.json      makes this repo an installable marketplace
apollo/                              the plugin
├── .claude-plugin/plugin.json
├── LICENSE                          a copy; marketplace installs only copy the plugin dir
├── README.md                        what recipients read
└── skills/
    ├── job-search/                  /apollo:job-search
    │   ├── SKILL.md
    │   ├── references/              interview, scaffolding, techniques, quality audit, feedback loop
    │   └── scripts/                 sweep, audit, and capture tooling
    └── dashboard/                   /apollo:dashboard
        └── SKILL.md
build_package.py                     builds the handoff zip
```

## Distribution

**The repo is the marketplace.** `.claude-plugin/marketplace.json` at the root points at `./apollo`, so users run:

```bash
/plugin marketplace add adamhilliard/apollo
```

then `/plugin install apollo@apollo`. Updates reach them when they run `/plugin marketplace update`, gated on the `version` field in `plugin.json`, so **bump it on every release or nobody gets the change.**

**`python build_package.py` still builds `apollo.zip`**, which stays useful for two things: attaching to a GitHub Release for people not installing from a marketplace, and `claude --plugin-dir apollo.zip` for a one-session trial. The zip is not committed; it's a release asset.

> **Verify before announcing.** `claude plugin validate ./apollo`, then `/plugin marketplace add .` from the repo root and confirm both skills load as `/apollo:job-search` and `/apollo:dashboard`.

## Where this came from

Extracted from a live executive job search that has been running daily since July 2026. Nearly every technique in `references/search-techniques.md` started as a correction after a real cycle got something wrong: a sweep that silently returned 6% of its result set, a posting that gained a hard credential requirement without notice, an ATS API that reported a live requisition as missing.

**That search is a separate repository and this one does not read from it.** Fixes flow here as releases rather than as a live dependency, so a lagging copy here means an unreleased change, not a broken link.

## Releasing

1. Port whatever the live search has learned that generalizes. The test: would this help a stranger with a different career, in a different field, at a different level?
2. Bump `version` in `apollo/.claude-plugin/plugin.json`.
3. `python build_package.py`.

Candidate-specific detail never lands here: no company names, role titles, scores, comp figures, or screening thresholds. Illustrative examples are fine when the lesson is general and the identifying detail is stripped.

## What 1.2.0 changed

Ported from the live search after five weeks of corrections. Three of these are fixes to recipes that had gone wrong in the wild, not improvements:

- **Four ATS hostnames were pointed at the vendors' own marketing sites** and returned clean-looking nils for months. `site:` is replaced by the search tool's `allowed_domains` parameter, which makes chain length free, and the host list is rebuilt to 25 measured hosts.
- **Both VC-board recipes broke.** Getro's `?page=N` went inert and caps a hand-rolled read at 20 jobs against boards carrying 25,000; `scripts/vc_sweep.py` now drives the API that actually paginates. Consider replaced its API with a signed-token path and is browser-only.
- **A new weekly quality audit**, `references/quality-audit.md` plus `scripts/quality_audit.py`, whose whole target is a broken recipe that reports success. Every case in the file looked exactly like a quiet week from inside a cycle.
- **Search Integrity grew from five rules to seven**, around one idea: anything that can return "nothing" has to distinguish *nothing was there* from *I didn't look*. Per-source status vocabulary, canaries, per-member result counts, and address verification.
- **Read contracts and a split threshold** in `scaffolding.md`, so a tracking file's growth is a measurement rather than a judgment call, plus a character cap on the free-text table column and a fixed shape for the notes log.
- **A customization block at the front of setup.** Naming moves into it, the dashboard palette moves up from the dashboard skill so it's asked once, and it adds the optional integrations: digest delivery including Slack, calendar events for review blocks and dated commitments, read-only email intake that keeps the tracker honest, locale, and pause windows. **Everything is optional and every default works.**
- **Confidential mode**, one switch for anyone searching while employed. It governs the Slack workspace, calendar event titles, dashboard sharing, commit messages, browser profile, and whether their current employer is excluded. A leaked search is the only failure here with consequences outside the search.
- **The scheduled prompt now states no rule it does not own.** A stale cadence table inside a prompt reverted a decision hours after it was made, and no repo-wide search reaches a file that lives outside the project.

## Status

**Public history starts at 1.2.0.** The earlier development commits are not published: they carried the maintainer's own employer target lists, scoring rubric, and worked examples, extracted from the live search this was generalized from. Nothing candidate-specific ships in the plugin, and the pre-publication history is kept locally rather than rewritten in place.

## Author and license

By **Adam Hilliard**, [linkedin.com/in/adamhilliard](https://linkedin.com/in/adamhilliard).

MIT, see [LICENSE](LICENSE). Free for anyone to use, modify, and redistribute, with the copyright line kept.

**Attribution lives in five places, and nowhere else on purpose:** this file, the plugin README recipients read at install, the `author` field in `plugin.json`, a one-line header in each bundled script, and **a short signed letter shown once at the top of setup**. Setup also writes a single credit line into the profile it generates, which lands once in each user's own repo.

**The letter is the only verbatim block in the setup interview**, and the only place the tool speaks in the author's voice rather than the user's search's. It runs once, at setup. **Never on a cycle, never in a digest, never on the dashboard**, because a credit that reappears every run reads as an ad.

Deliberately not watermarked: the reference files, because Claude loads them into context every cycle and a credit line there is noise inside search instructions; and the digest, because it's someone's private job search and a recurring credit reads as an ad.
