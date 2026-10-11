"""Usage: write_announcement.py "<Course folder>" "<Course name>" <courseId> <createdUTC ISO> "<title>" <body-file>
Writes <Course folder>/Announcements/YYYY-MM-DD <title>.md in the same format as Course A (YOUR_TIMEZONE time)."""
import re, sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
folder, cname, cid, iso, title, bodyf = sys.argv[1:7]
title = title.strip()
t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZoneInfo("YOUR_TIMEZONE"))
safe = re.sub(r'[\\/:*?"<>|]+', "-", title).strip()
d = Path(folder) / "Announcements"; d.mkdir(parents=True, exist_ok=True)
p = d / f"{t:%Y-%m-%d} {safe}.md"
assert not p.exists(), p
body = Path(bodyf).read_text().strip()
p.write_text(f"# {title}\n\n- Course: {cname} (`{cid}`)\n- Posted: {t.day} {t:%b %Y, %H:%M} (YOUR_TIMEZONE)\n- Source: Canvas announcement\n\n---\n\n{body}\n")
print(p)
