# Apollo

A recurring job search that runs itself in Claude Code. It interviews you once, writes your profile and scoring rubric to disk, then runs on a schedule: sourcing roles from job boards, applicant tracking systems, and VC portfolio boards, checking each posting is real and still says what it said, scoring it against what you actually want, and handing you a ranked digest.

Works at any career level, from first job to executive search.

**You name your own copy.** Apollo is the tooling. The first thing setup asks is what you want to call your search, and everything it writes from then on uses your name instead of Apollo.

## Install

**Recommended, two commands in Claude Code:**

```
/plugin marketplace add adamhilliard/apollo
```

```
/plugin install apollo@apollo
```

If the install summary says `Run /reload-plugins to activate`, run that. Otherwise you're done. You'll get updates when you run `/plugin marketplace update`.

**No marketplace? Drop the folder in instead.** Download `apollo.zip` from the [latest release](https://github.com/adamhilliard/apollo/releases) and unzip it into your skills directory:

| | Path |
|---|---|
| **macOS / Linux** | `~/.claude/skills/` |
| **Windows** | `%USERPROFILE%\.claude\skills\` |

You should end up with `.claude/skills/apollo/.claude-plugin/plugin.json`. Restart Claude Code and it loads as `apollo@skills-dir`, no install step.

**Just want to try it?** Point Claude Code at the zip for one session, with nothing written to your skills directory:

```bash
claude --plugin-dir apollo.zip
```

## Use it

Make a folder for your search, start Claude Code in it, and say:

> Help me set up Apollo.

Have your resume or a PDF of your LinkedIn profile handy, it makes the interview much shorter. No resume yet is fine; it has a path for that.

**It opens by asking what you want to call it,** then a short customization step: the dashboard's color, where the digest should reach you, and whether to wire in your calendar or your email. **Everything there is optional and every default works**, so "defaults are fine" is a valid answer.

Then you'll answer thirteen questions. **Most are click-to-pick**, so you're choosing and adjusting rather than writing from scratch. The handful that are open-ended are the ones where a menu would give you a worse profile: your background, your target titles, your comp numbers, and what actually motivates you. Then it writes your files and sets up two recurring tasks: the search cycle, and a weekly self-check.

**Searching while employed? Say so.** It sets one switch that keeps the search off your work Slack, off a shared calendar, and out of your commit messages.

## What to expect

- **The interview is the setup.** Answer it properly. Five of the questions are where a generic bot becomes yours, and it will tell you which ones those are.
- **It gets good around cycle three or four,** not cycle one. Tell it what it got wrong in plain conversation and it writes the corrected rule into your files. That feedback loop is most of the value.
- **Volume depends on your level.** An executive search returning nothing some weeks is working correctly. An early-career search returning two hundred roles is also working correctly. It calibrates to your answer on the first question.
- **It finds and ranks roles. It doesn't apply to them,** and it won't message anyone on your behalf.
- **The weekly self-check is the boring feature that matters most.** A job search bot's worst failure isn't a bad recommendation, it's a source that quietly breaks and reports a normal-looking quiet week for two months. The audit exists to catch exactly that, and it reports what it computed rather than what the cycle claimed.

## What it touches

Apollo reads a lot and writes only to your machine. **Everything that reaches an account of yours is off by default and turned on one at a time during setup.**

| | What it does |
|---|---|
| **Web search** | Job boards, applicant tracking systems, and VC portfolio boards. All public pages |
| **Your browser session** *(optional)* | Reads your logged-in job-board feed and alerts, which anonymous search can't see. **Browsing only.** It never applies, never messages, never views anyone's profile |
| **Your files** | Writes a project folder in the directory you start it in, and commits there if you use git |
| **Slack** *(optional)* | Posts your digest to your own DM or a private channel you own. Never a shared channel |
| **Calendar** *(optional)* | Creates events for your interviews and follow-up dates. **Never invites anyone** |
| **Email** *(optional)* | **Read-only, and scoped** to mail from employers already in your tracker. It records that an application landed or was rejected. It never sends, replies, archives, or deletes |

**What it will not do, at any setting:** apply to a job, message a recruiter, accept terms on your behalf, or enter personal or financial details into a form. It finds and ranks roles and hands the list to you.

**Nothing is sent anywhere.** Your profile, your tracked roles, and your digest stay on your machine and in your own repo. There is no account, no telemetry, and no server. The author receives nothing.

**Searching while employed?** Say so at setup. One switch keeps the search off your work Slack, off a shared calendar, out of your commit messages, and excludes your current employer from results.

## What's in the box

| | |
|---|---|
| `/apollo:job-search` | The main skill. Setup interview, search techniques, verification rules, the recurring cycle, and the weekly quality audit. |
| `/apollo:dashboard` | Optional. Turns your tracking files into a private web dashboard at a bookmarkable link that refreshes every cycle. Run it after your first cycle. |

You don't need to type either name. Just describe what you want, or use the name you gave your search, and Claude picks the right one.

## Removing it

`/plugin uninstall apollo@apollo` if you installed from the marketplace, or delete the `apollo` folder from your skills directory if you dropped it in. Nothing else to undo.

**Your search stays.** The project folder Apollo wrote is yours: plain markdown, readable and useful without the plugin. Removing the tooling doesn't touch it, and the scheduled tasks are yours to delete when you want them gone.

---

## Who made this

Apollo is by **Adam Hilliard** ([linkedin.com/in/adamhilliard](https://linkedin.com/in/adamhilliard)), an HR executive who built it to run his own search and then generalized it so other people could use it.

Free under the MIT license, included as `LICENSE` in this folder. Use it, change it, pass it on. If it helps you land something, say so; that's the only thing asked in return.

