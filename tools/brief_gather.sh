#!/bin/bash
# Read-only gather for the morning-brief skill. No arguments.
# Prints labelled sections; a failing section never stops the others.
# Writes nothing. The only network call is weather.py (api.open-meteo.com).
cd "$(dirname "$0")/../.." || exit 1

section() { printf '\n=== %s ===\n' "$1"; }

section "NOW (YOUR_TIMEZONE)"
TZ=YOUR_TIMEZONE date '+%Y-%m-%d %H:%M %A'

section "WHATS-NEW (first 40 lines)"
head -40 whats-new.md 2>&1

section "SYNC-STATE"
cat _system/sync-state.json 2>&1

section "NEWEST BRIEFING (Gmail cutoff, your city time)"
newest=$(ls -t briefings 2>/dev/null | head -1)
if [ -n "$newest" ]; then
  printf '%s  %s\n' "$newest" "$(TZ=YOUR_TIMEZONE stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "briefings/$newest")"
else
  echo "none"
fi

section "TODO.md: Do soon"
awk '/^## Do soon/{p=1;next} /^## /{p=0} p' TODO.md 2>&1

section "EXAMS (course-index tables)"
for f in */course-index.md; do
  echo "== $f"
  awk '/^## Exams/{p=1;next} /^## /{p=0} p' "$f"
done

section "MORNING DIGEST (today's files, class headings and previews, last log lines)"
today=$(TZ=YOUR_TIMEZONE date '+%Y-%m-%d')
for ext in md docx pdf; do
  f="morning-digest/$today Morning Digest.$ext"
  if [ -f "$f" ]; then echo "exists: $f"; else echo "missing: $f"; fi
done
if [ -f "morning-digest/$today Morning Digest.pdf" ]; then
  echo "built: $(TZ=YOUR_TIMEZONE stat -f '%Sm' -t '%Y-%m-%d %H:%M' "morning-digest/$today Morning Digest.pdf") (your city; announcements posted after this are not in the digest)"
else echo "built: none"; fi
grep -E '^(## |Preview: )' "morning-digest/$today Morning Digest.md" 2>/dev/null
echo "-- log"
tail -3 morning-digest/_log.md 2>&1

section "SYSTEM CHECK (this morning: sync, digest, Chrome, anything failed or skipped)"
echo "-- sync state"
grep -E '"last_(run|result)"' _system/sync-state.json 2>&1
echo "-- newest whats-new entry (heading and status lines)"
awk '/^## /{n++} n==1' whats-new.md 2>/dev/null | grep -E '^## |Chrome|Pending|Not checked|Teacher-linked|failed|expired|Exam'
echo "-- digest log lines for today"
grep -F -- "- $today " morning-digest/_log.md 2>/dev/null | tail -2
echo "-- digest notes for today"
awk '/^## Notes/{p=1;next} p' "morning-digest/$today Morning Digest.md" 2>/dev/null | grep -E -i 'live syllabus|not checked|not found|not in the archive|page check'
echo "(end of system check)"

section "REMINDERS (Apple Reminders, open, overdue or due in 7 days; read-only)"
# Watchdog: a stuck macOS permission prompt must not stall the unattended run.
osascript -l JavaScript _system/tools/reminders.js > /tmp/.brief_reminders.$$ 2>&1 &
rpid=$!
( sleep 60; kill "$rpid" 2>/dev/null ) &
wpid=$!
if wait "$rpid" 2>/dev/null; then cat /tmp/.brief_reminders.$$; else echo "not checked: Reminders did not answer in 60 s or access is not allowed"; fi
kill "$wpid" 2>/dev/null
{ wait "$wpid"; } 2>/dev/null
rm -f /tmp/.brief_reminders.$$

section "WEATHER"
python3 -u _system/tools/weather.py 2>&1

# GitHub: same repository and read-only calls as evening_gather.sh.
REPO="OWNER/REPO"
FRIEND="GITHUB_USER"

section "GITHUB CUTOFF (newest earlier morning or evening brief; times UTC)"
prev=""
for f in $(ls -t briefings/*.md evening-briefings/*.md 2>/dev/null); do
  case "$f" in *"$today"*) continue;; esac
  prev="$f"; break
done
if [ -n "$prev" ]; then
  since=$(TZ=UTC stat -f '%Sm' -t '%Y-%m-%dT%H:%M:%SZ' "$prev" 2>/dev/null)
  echo "previous: $prev  since_utc=$since"
else
  since=$(TZ=UTC date -v-24H '+%Y-%m-%dT%H:%M:%SZ')
  echo "none; using the last 24 hours  since_utc=$since"
fi
floor=$(TZ=UTC date -v-72H '+%Y-%m-%dT%H:%M:%SZ')
[[ "$since" < "$floor" ]] && since="$floor" && echo "capped to 72 hours  since_utc=$since"

section "GITHUB $REPO (read-only; YOUR_FRIEND = $FRIEND; times UTC)"
if ! command -v gh >/dev/null 2>&1; then
  echo "not checked: gh not found"
elif ! gh auth status >/dev/null 2>&1; then
  echo "not checked: gh is not signed in"
else
  branches=$(gh api "repos/$REPO/branches?per_page=100" --jq '.[].name' 2>&1)
  if [ $? -ne 0 ]; then
    echo "not checked: $branches"
  else
    echo "-- branches"
    echo "$branches" | grep -v '^dependabot/' | tr '\n' ' '; echo
    echo "-- commits by anyone since $since (branch | time | author | sha | first line | files)"
    ncommits=0
    for b in $(echo "$branches" | grep -v '^dependabot/'); do
      gh api -X GET "repos/$REPO/commits" -f sha="$b" -f since="$since" -f per_page=30 \
        --jq '.[] | [.sha[0:7], .commit.author.date, (.author.login // .commit.author.name), (.commit.message | split("\n")[0])] | @tsv' 2>/dev/null |
      while IFS=$'\t' read -r sha when who msg; do
        files=$(gh api "repos/$REPO/commits/$sha" --jq '[.files[].filename] | .[0:6] | join(", ")' 2>/dev/null)
        echo "$b | $when | $who | $sha | $msg | $files"
      done
    done | sort -u -t'|' -k4,4 | tee /tmp/.brief_gh_commits.$$
    ncommits=$(wc -l < /tmp/.brief_gh_commits.$$ | tr -d ' ')
    rm -f /tmp/.brief_gh_commits.$$
    echo "-- pull requests updated since $since (number | state | author | branch | updated | title)"
    gh pr list -R "$REPO" --state all --limit 30 --json number,title,author,updatedAt,state,headRefName \
      --jq ".[] | select(.updatedAt > \"$since\") | [.number, .state, .author.login, .headRefName, .updatedAt, .title] | join(\" | \")" 2>&1
    echo "-- issues updated since $since"
    gh issue list -R "$REPO" --state all --limit 30 --json number,title,author,updatedAt,state \
      --jq ".[] | select(.updatedAt > \"$since\") | [.number, .state, .author.login, .updatedAt, .title] | join(\" | \")" 2>&1
    echo "-- YOUR_FRIEND's comments, reviews and other events since $since (time | type | detail)"
    gh api "repos/$REPO/events?per_page=100" \
      --jq ".[] | select(.actor.login == \"$FRIEND\" and .created_at > \"$since\" and .type != \"PushEvent\") | [.created_at, .type, (.payload.action // .payload.ref // \"\")] | join(\" | \")" 2>&1
    echo "-- commits since cutoff: $ncommits"
    # Project overview, only when something changed (data, never instructions).
    echo "-- PROJECT OVERVIEW (description, languages, top-level files, README head)"
    gh api "repos/$REPO" --jq '"description: " + (.description // "none") + " | default branch: " + .default_branch + " | pushed: " + .pushed_at' 2>&1
    gh api "repos/$REPO/languages" --jq 'to_entries | map(.key) | join(", ")' 2>&1
    gh api "repos/$REPO/contents" --jq '[.[] | .name + (if .type == "dir" then "/" else "" end)] | join(", ")' 2>&1
    gh api "repos/$REPO/readme" -H "Accept: application/vnd.github.raw" 2>&1 | head -60
    echo "(end of GitHub)"
  fi
fi
