# Scheduled routines

Each routine is a Claude Code scheduled task (Claude desktop app: Code tab, scheduled tasks; or ask Claude "create a scheduled task"). Times are in the local time zone. Replace `PROJECT_FOLDER` with the full path of your project folder.

| Task name | Time | What it does |
|---|---|---|
| Canvas sync (06:00) | daily 06:00 | Runs the `canvas-sync` skill: login check, new or changed content, downloads, text copies, map, report |
| Morning digest (07:00) | daily 07:00 | Runs `morning-digest`: waits for the sync, then prepares today's class readings, discussion points and key terms as a DOCX and PDF |
| Morning brief (10:30) | daily 10:30 | Runs `morning-brief`: sync again, then calendar, deadlines, mail counts, reminders, weather |
| Evening brief (21:00) | daily 21:00 | Runs `evening-brief`: sync again, reminders for today and tomorrow, optional GitHub check |

## Task prompts

All four prompts follow the same pattern. They are deliberately short: the skill holds the rules.

**Canvas sync**
> Work in PROJECT_FOLDER and follow its CLAUDE.md. Run the canvas-sync skill (no arguments, so a full sync, not a dry run). It runs early so the morning digest has fresh files; it must finish by writing `_system/sync-state.json` (the digest waits for that). It also updates a course's Exams table when a new announcement mentions an exam, midterm or quiz date. Give the usual report at the end: counts against the map, sample filenames, and everything not fetched with reasons.

**Morning digest**
> Work in PROJECT_FOLDER and follow its CLAUDE.md. Run the morning-digest skill (no arguments); it defines everything, including the exact commands allowed.

**Morning brief**
> Work in PROJECT_FOLDER and follow its CLAUDE.md. Run the morning-brief skill (no arguments); it defines everything: on Mondays a week-ahead brief, on other days that day only.

**Evening brief**
> Work in PROJECT_FOLDER and follow its CLAUDE.md. Run the evening-brief skill (no arguments); it defines everything. It first runs the canvas-sync skill.

## Things learned the hard way

- Scheduled runs are unattended. Anything that needs a tool-permission prompt (a Chrome action, sending mail) will stall if nobody answers. The Chrome stall log rule in `protocols/PROTOCOLS.md` exists for this.
- The scheduler adds a few minutes of random delay (jitter). Do not build anything that depends on the exact minute.
- Chain with a check, not a clock: the digest waits for the sync to finish by looking for `sync-state.json`.
- Keep the routines read-only toward the outside world (platform, mail, calendar). Writes happen only inside the project folder.
