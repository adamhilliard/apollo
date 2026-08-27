# Apollo

**A recurring job search that runs itself in Claude.** One setup interview saves your profile and scoring rules onto your own computer. A scheduled task then sources roles from job boards, the hiring systems companies post to directly, and the job pages startup investors keep for their companies, checks each posting is real and still says what it said, scores it against what you actually want, and hands you a ranked digest.

Free, MIT licensed, and it works at any career level, from first job to executive search.

## Install

**You need the [Claude](https://claude.com) app on your computer.** It's free to download, and that's the whole prerequisite. (There's a command-line version too, if that's how you work; the typing route is below.)

### In Claude Desktop, by clicking

1. Open Claude Desktop.
2. Click **Customize** in the left sidebar.
3. Click **Plugins**. (Plugins are free add-ons for Claude. Apollo is one of them.)
4. Click **Add plugin**.
5. Click **Add marketplace**.
6. Choose **Add from repo** (that’s just where Apollo lives online).
7. Paste `adamhilliard/apollo` into the box that appears. That’s Apollo’s address.
8. Click **Sync**. That downloads it.
9. Click **Install** on **Apollo Job Search**.
10. Start a new conversation. It won't appear in one that's already open.
11. Say: *"Help me set up a job search."*

**Nothing happening?** Close Claude, open it again, and try step 10.

### In Claude Code, by typing

```
/plugin marketplace add adamhilliard/apollo
```

```
/plugin install apollo@apollo
```

If the install summary says `Run /reload-plugins to activate`, run that. Otherwise you're done.

**To update later:** `/plugin marketplace update`, or click **Sync** again in Desktop.

<details>
<summary><b>No marketplace? Drop the folder in instead.</b></summary>

Download `apollo.zip` from the [latest release](https://github.com/adamhilliard/apollo/releases/latest) and unzip it into your skills directory:

| | Path |
|---|---|
| **macOS / Linux** | `~/.claude/skills/` |
| **Windows** | `%USERPROFILE%\.claude\skills\` |

You should end up with `.claude/skills/apollo/.claude-plugin/plugin.json`. Restart Claude Code and it loads as `apollo@skills-dir`, no install step.

</details>

<details>
<summary><b>Just want to try it for one session?</b></summary>

Point Claude Code at the zip. Nothing is written to your skills directory:

```bash
claude --plugin-dir apollo.zip
```

</details>

## Start a search

In a new conversation, say:

> Help me set up a job search.

**Setup saves your files in a folder on your computer.** Just tell it where you’d like them; if you’re not sure, say so and it will pick a sensible spot.

**The interview takes about fifteen minutes.** Have your resume or a PDF of your LinkedIn profile handy; it makes the interview much shorter. No resume yet is fine, there's a path for that. Most questions are click-to-pick, and "defaults are fine" is a valid answer to the whole customization step.

**It takes the name you give it.** The first thing setup asks is what you want to call your search, and every file it writes uses your name instead of Apollo.

## What you get

| | |
|---|---|
| `/apollo:job-search` | The main skill. Setup interview, search techniques, verification rules, the recurring cycle, and a weekly quality audit that checks whether the search is mechanically doing what it claims. |
| `/apollo:dashboard` | Optional. Turns your tracking files into a private web dashboard at a bookmarkable link that refreshes every cycle. Run it after your first cycle. |

You don't need to type either name. Describe what you want, or use the name you gave your search, and Claude picks the right one.

## What it touches

**Apollo reads a lot and writes only to your machine.** Everything that reaches an account of yours is off by default and turned on one at a time during setup: your browser session, Slack, calendar, and read-only email intake.

> **The browser session is the one with a prerequisite.** It needs Claude's browser extension installed and signed in, and it's worth having, since your logged-in job-board feed and alerts are invisible to anonymous search. Setup checks and tells you if it's missing.

**It will not apply to a job, message a recruiter, accept terms on your behalf, or enter personal or financial details into a form.** It finds and ranks roles and hands you the list.

**Nothing is sent anywhere.** Your profile, your tracked roles, and your digest stay on your machine and in your own repo. There is no account, no telemetry, and no server. The author receives nothing.

**Searching while employed?** Say so at setup. One switch keeps the search off your work Slack, off a shared calendar, out of your commit messages, and excludes your current employer from results.

> Full detail on every integration and its scope is in [the plugin's own README](apollo/README.md), which is also what lands in your skills folder after install.

## Author and license

By **Adam Hilliard**, [linkedin.com/in/adamhilliard](https://linkedin.com/in/adamhilliard), an HR executive who built it to run his own search and then generalized it so other people could use it.

MIT, see [LICENSE](LICENSE). Use it, change it, pass it on, with the copyright line kept. If it helps you land something, say so; that's the only thing asked in return.

Building on it or cutting a release? See [MAINTAINING.md](MAINTAINING.md).
