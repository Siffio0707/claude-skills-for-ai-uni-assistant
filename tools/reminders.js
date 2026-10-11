// Read-only: lists open Apple Reminders that are overdue or due in the next 7 days (your city dates).
// Run by brief_gather.sh via osascript -l JavaScript. Never creates, changes, completes or deletes anything.
// Output lines: "<YYYY-MM-DD>|<HH:MM or all-day>|<list>|<title>" (flagged ones end with " [flagged]").
// Reminders with no due date are not listed (they are not "for the day").
function run() {
  const R = Application("Reminders");
  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: "YOUR_TIMEZONE", year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  });
  const parts = (d) => Object.fromEntries(fmt.formatToParts(d).map((p) => [p.type, p.value]));
  const now = new Date();
  const horizon = new Date(now.getTime() + 8 * 24 * 3600 * 1000);
  const rows = [];
  for (const list of R.lists()) {
    const open = list.reminders.whose({ completed: false });
    const titles = open.name();
    const dues = open.dueDate();
    const alldays = open.alldayDueDate ? open.alldayDueDate() : [];
    const flags = open.flagged();
    for (let i = 0; i < titles.length; i++) {
      const due = dues[i] || alldays[i];
      if (!due || due > horizon) continue;
      const p = parts(due);
      const allDay = p.hour === "00" && p.minute === "00";
      rows.push([
        `${p.year}-${p.month}-${p.day}`,
        allDay ? "all-day" : `${p.hour}:${p.minute}`,
        list.name(),
        titles[i] + (flags[i] ? " [flagged]" : ""),
      ].join("|"));
    }
  }
  rows.sort();
  return rows.length ? rows.join("\n") : "(none due or overdue)";
}
