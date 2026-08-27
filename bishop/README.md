# Bishop

A recurring job search that runs itself in Claude. It interviews you once to learn what you're after, then works on a schedule: finding new roles across job boards and company career pages, checking each posting is real and still says what it said, ranking them against what actually matters to you, and handing you a ranked digest.

Works at any career level, from first job to executive search.

## Install

**About a minute, and the only typing is one paste.**

1. Open the Claude app on your computer.
2. Click **Customize** in the left sidebar, then **Plugins**. (Plugins are free add-ons for Claude. Bishop is one of them.)
3. Click **Add plugin**, then **Add marketplace**, then **Add from repo**. Nothing here costs anything.
4. Paste `adamhilliard/bishop` into the box. That's Bishop's address.
5. Click **Sync**, then click **Install** on **Bishop Job Search**.
6. Start a **new conversation**. Bishop won't show up in one that's already open.
7. Say: *"Help me set up a job search."*

**Stuck?** Close Claude, open it again, and try step 6.

**To update later:** open that same Plugins screen and click **Sync**.

<details>
<summary><b>Prefer to type? Two lines instead of the clicks.</b></summary>

In Claude Code, type these into the chat box and press enter after each:

```
/plugin marketplace add adamhilliard/bishop
```

```
/plugin install bishop@bishop
```

The odd-looking `bishop@bishop` is correct: it's the plugin's name, then where it came from. If the summary says `Run /reload-plugins to activate`, run that. Update later with `/plugin marketplace update`.

</details>

<details>
<summary><b>Installing without the plugin screen (advanced).</b></summary>

Download `bishop.zip` from the [latest release](https://github.com/adamhilliard/bishop/releases) and unzip it into your skills directory:

| | Path |
|---|---|
| **macOS / Linux** | `~/.claude/skills/` |
| **Windows** | `%USERPROFILE%\.claude\skills\` |

You should end up with `.claude/skills/bishop/.claude-plugin/plugin.json`. Restart Claude Code and it loads with no install step.

Or, to try it for one session without writing anything to your skills directory:

```bash
claude --plugin-dir bishop.zip
```

</details>

## Then start it

Open a new conversation and say:

> Help me set up a job search.

Have your resume or a LinkedIn PDF handy. Bishop asks where to save your files, then walks you through the rest and hands you your first digest.

It'll also ask for a one-time OK so it doesn't have to interrupt you at every step, and so your searches can keep running on schedule while you're away.

**What you installed:**

| | |
|---|---|
| `/bishop:job-search` | The main skill: the setup interview, the recurring search, and a weekly self-check. |
| `/bishop:dashboard` | Optional. Turns your search into a private web dashboard at a bookmarkable link. Run it after your first search. |

You don't need to type either name. Just describe what you want and Claude picks the right one.

## What it touches

Bishop reads a lot and writes only to your machine. **Anything that reaches one of your accounts is off by default, and turned on only when you choose.**

| | What it does |
|---|---|
| **Web search** | Job boards, the hiring systems companies post to directly, and the job pages startup investors keep for their companies. All public pages |
| **Your browser session** *(optional)* | Reads your logged-in job-board feed and alerts, which anonymous search can't see. **Needs Claude's browser extension.** **Browsing only.** It never applies, never messages, never views anyone's profile |
| **Your files** | Writes a folder for your search in the place you started it. Everything stays on your computer |
| **Slack** *(optional)* | Posts your digest to your own DM or a private channel you own. Never a shared channel |
| **Calendar** *(optional)* | Creates events for your interviews and follow-up dates. **Never invites anyone** |
| **Email** *(optional)* | Reads mail from employers already in your list to log applications and rejections (scoped to those). Can also email you your digest. It only ever emails you, never replies, archives, or deletes |

It will never apply to a job, message a recruiter, agree to anything for you, or enter your personal or financial details into a form. It finds and ranks roles and hands you the digest.

Nothing leaves your computer: your profile, your saved roles, and your digest all stay on your machine. No account, no sign-up, no server, and the person who made Bishop receives nothing.

## Uninstall

Open the same Plugins screen where you installed it and click **Uninstall**. Nothing else to undo.

(If you installed by typing, `/plugin uninstall bishop@bishop` does the same thing. If you dropped the folder in by hand, delete the `bishop` folder you unzipped.)

**Your search stays.** The project folder Bishop wrote is yours: plain markdown, readable and useful without the plugin. Removing the tooling doesn't touch it, and the scheduled tasks are yours to delete when you want them gone.

## Credits

Bishop is by **Adam Hilliard** ([linkedin.com/in/adamhilliard](https://linkedin.com/in/adamhilliard)), an HR executive who built it to run his own search and then generalized it so other people could use it, co-built with L&D Expert **Danielle Beram** ([linkedin.com/in/danielle-beram](https://linkedin.com/in/danielle-beram)) and inspired by Recruiting Ops Expert **Loren Boykoff** ([linkedin.com/in/lorenboykoff](https://linkedin.com/in/lorenboykoff)).

Free under the MIT license, included as `LICENSE` in this folder. Use it, change it, pass it on. If it helps you land something, say so; that's the only thing asked in return.

