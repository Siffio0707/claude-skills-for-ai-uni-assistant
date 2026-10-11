# Plugins, tools and GitHub repos that were useful

Everything here was used in the original setup. Each entry says what it does and where it comes from. A few things could not be fully verified; they are marked.

**Rule for your Claude:** do not install any of these without asking the user first, and say exactly what will be installed and from where.

## Connectors and built-in features (no GitHub download)

| What | What it does | How to get it |
|---|---|---|
| Gmail connector | Search and read mail, create drafts. Sending only after the user has seen the full draft | Connect it in your Claude account settings (Connectors) |
| Google Calendar connector | Read the calendar for the briefs | Same place |
| Claude in Chrome | Lets Claude read pages and download files in a browser profile you choose. Used for the university platform files the API can't give | Install the Claude in Chrome extension in one dedicated Chrome profile |
| Scheduled tasks | Runs a skill every day at a set time (the routines in `routines/ROUTINES.md`) | Built into the Claude desktop app, or ask Claude to create a scheduled task |
| Claude Code skills | Each folder in `skills/` goes in `.claude/skills/<name>/SKILL.md` in your project | Copy the folder |

## GitHub repos and packages

| Repo or package | What it does | Install | Notes |
|---|---|---|---|
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | Turns DOCX, PPTX, HTML, EPUB and other files into Markdown so Claude can read them cheaply | Python package, installed in a virtual environment with the pdf, docx, pptx and xlsx extras | Used 0.1.8. Local files only. Never turn on its plugins, OCR add-ons or Document Intelligence options: they send content to cloud services. PDFs are better read with a tool that keeps page numbers, which citations need |
| [AeternaLabsHQ/pullmd](https://github.com/AeternaLabsHQ/pullmd) | A self-hosted web reader that returns clean Markdown for a URL, exposed to Claude as an MCP server (`read_url`, `get_share`, `list_recent`) | Self-host it, then `claude mcp add --transport http pullmd <your-url>/mcp`. See its README | Used as the only way Claude reads web pages, so every source is logged and cited. |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | A design-guidance skill for building web interfaces | Its README lists a Claude Code plugin route and an npm CLI route | Used for the website project, not for studying. Found through search, not opened on GitHub itself, so read its README before installing |
| `frontend-design` plugin (from the official `claude-plugins-official` marketplace) | Helps Claude produce good-looking front-end code | Install with Claude Code's `/plugin` command from the official marketplace | Used for the website project, not for studying |
| `gh` (GitHub CLI) | Read-only GitHub checks inside the briefs (only if you have a shared project) | Install the GitHub CLI and run `gh auth login` yourself | Optional. Skip unless you share a repo with someone |
| A **read-only Canvas MCP server** | Gives Claude read access to Canvas: courses, modules, files, announcements, assignments, grades | Pick one, read its README, set it up with a Canvas access token that you create yourself | **I have not tested any Canvas server.** A web search turned up several student-focused, read-only ones; verify each in its own repo before installing (see the checklist below). The original Blackboard version used a different tool, which is why the `canvas-sync` skill has a tool table to fill in instead of fixed tool names |

## Checklist for choosing a Canvas MCP server

- It says it is **read-only** (no tool that submits, posts, sends messages or edits). Avoid any server that "reads and writes course content".
- It uses a personal access token you create yourself in Canvas (Account > Settings > New Access Token), or your own session. Never paste the token into chat; let the tool read it from its own config.
- Some schools switch off student access tokens. If yours does, ask your Claude to look at servers that work from your logged-in session instead, and read what they do with your login first.
- It lists courses, modules, files, announcements, assignments and the calendar.
- It has a real GitHub repo with recent commits and a licence. Read the code's tool list and put every write tool in the `deny` list in `.claude/settings.json`.
- Leads from a web search (unverified; names only): `mcp-server-canvas-lms`, `canvas-mcp-server`, `canvas-scholar-mcp`, `canvas-student-mcp`. Source of the leads: https://glama.ai/mcp/servers/rpmgpua09j and other Glama listings, found 11 Oct 2026.

## Optional extras

- ElevenLabs text-to-speech for spoken briefings. The key must live only in the macOS Keychain, and no script or chat may ever print it. The scripts were left out of this repo; ask your Claude to write one following the key rules in `protocols/PROTOCOLS.md`.
- Apple Reminders reading (`tools/reminders.js`) for the briefs.

## Order I would adopt things in

1. `protocols/PROTOCOLS.md` and the deny list (safety first).
2. MarkItDown and PullMD (they make reading cheaper and sourced).
3. The Canvas connector, then `canvas-sync` as a dry run.
4. `morning-digest` and `quiz-me`.
5. The two briefs and the scheduled routines.
