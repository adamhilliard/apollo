# Apollo

A recurring job search that runs itself in Claude Code. It interviews you once to learn what you're after, then works on a schedule: finding new roles across job boards and company career pages, checking each posting is real and still says what it said, ranking them against what actually matters to you, and handing you a ranked digest.

Works at any career level, from first job to executive search.

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

**Then start it.** Make a folder for your search, open Claude Code in it, and say:

> Help me set up Apollo.

Have your resume or a LinkedIn PDF handy. Setup walks you through the rest and hands you your first digest. It also offers to add a permission rule so it isn't stopping to ask before every file it writes or search it runs, which is also what lets the scheduled runs work on their own.

**What you installed:**

| | |
|---|---|
| `/apollo:job-search` | The main skill: the setup interview, the recurring search, and a weekly self-check. |
| `/apollo:dashboard` | Optional. Turns your search into a private web dashboard at a bookmarkable link. Run it after your first search. |

You don't need to type either name. Just describe what you want and Claude picks the right one.

## What it touches

Apollo reads a lot and writes only to your machine. **Anything that reaches one of your accounts is off by default, and turned on only when you choose.**

| | What it does |
|---|---|
| **Web search** | Job boards, applicant tracking systems, and Venture Capital portfolio boards. All public pages |
| **Your browser session** *(optional)* | Reads your logged-in job-board feed and alerts, which anonymous search can't see. **Needs Claude's browser extension.** **Browsing only.** It never applies, never messages, never views anyone's profile |
| **Your files** | Writes a folder for your search in the place you started it. Everything stays on your computer |
| **Slack** *(optional)* | Posts your digest to your own DM or a private channel you own. Never a shared channel |
| **Calendar** *(optional)* | Creates events for your interviews and follow-up dates. **Never invites anyone** |
| **Email** *(optional)* | Reads mail from employers already in your list to log applications and rejections (scoped to those). Can also email you your digest. It only ever emails you, never replies, archives, or deletes |

It will never apply to a job, message a recruiter, agree to anything for you, or enter your personal or financial details into a form. It finds and ranks roles and hands you the digest.

Nothing leaves your computer: your profile, your saved roles, and your digest all stay on your machine. No account, no sign-up, no server, and the person who made Apollo receives nothing.

## Uninstall

`/plugin uninstall apollo@apollo` if you installed from the marketplace, or delete the `apollo` folder from your skills directory if you dropped it in. Nothing else to undo.

**Your search stays.** The project folder Apollo wrote is yours: plain markdown, readable and useful without the plugin. Removing the tooling doesn't touch it, and the scheduled tasks are yours to delete when you want them gone.

## Credits

Apollo is by **Adam Hilliard** ([linkedin.com/in/adamhilliard](https://linkedin.com/in/adamhilliard)), an HR executive who built it to run his own search and then generalized it so other people could use it, co-built with L&D Expert **Danielle Beram** ([linkedin.com/in/danielle-beram](https://linkedin.com/in/danielle-beram)) and inspired by Recruiting Ops Expert **Loren Boykoff** ([linkedin.com/in/lorenboykoff](https://linkedin.com/in/lorenboykoff)).

Free under the MIT license, included as `LICENSE` in this folder. Use it, change it, pass it on. If it helps you land something, say so; that's the only thing asked in return.
