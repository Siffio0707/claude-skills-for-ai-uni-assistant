#!/bin/bash
# Read-only gather for the evening-brief skill. No arguments.
# Prints labelled sections; a failing section never stops the others.
# Writes nothing. Network: only read-only GETs to api.github.com through `gh` (repo below), plus weather-free.
cd "$(dirname "$0")/../.." || exit 1

REPO="OWNER/REPO"
FRIEND="GITHUB_USER"

section() { printf '\n=== %s ===\n' "$1"; }

section "NOW (YOUR_TIMEZONE)"
TZ=YOUR_TIMEZONE date '+%Y-%m-%d %H:%M %A'
echo "tomorrow: $(TZ=YOUR_TIMEZONE date -v+1d '+%Y-%m-%d %A')"

section "TODAY'S MORNING SYNC ENTRY AND NEWEST whats-new ENTRY (heading and status lines; newest first)"
awk '/^## /{n++} n<=2' whats-new.md 2>&1 | grep -E '^## |New files|Changed|New announcements|Pending|Not fetched|Teacher-linked|Not checked|Exam changes|Chrome|Counts'

section "SYNC-STATE"
cat _system/sync-state.json 2>&1

section "PREVIOUS EVENING BRIEF (GitHub cutoff)"
today=$(TZ=YOUR_TIMEZONE date '+%Y-%m-%d')
prev=""
for f in $(ls -t evening-briefings/*.md 2>/dev/null); do
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
# never look back more than 72 hours
floor=$(TZ=UTC date -v-72H '+%Y-%m-%dT%H:%M:%SZ')
[[ "$since" < "$floor" ]] && since="$floor" && echo "capped to 72 hours  since_utc=$since"

section "GITHUB $REPO (read-only; YOUR_FRIEND = $FRIEND; times UTC)"
if ! command -v gh >/dev/null 2>&1; then
  echo "not checked: gh not found"
elif ! gh auth status >/dev/null 2>&1; then
  echo "not checked: gh is not signed in"
else
  echo "-- branches"
  branches=$(gh api "repos/$REPO/branches?per_page=100" --jq '.[].name' 2>&1)
  if [ $? -ne 0 ]; then
    echo "not checked: $branches"
  else
    echo "$branches" | grep -v '^dependabot/' | tr '\n' ' '; echo
    echo "-- YOUR_FRIEND's commits since $since (branch | time | sha | first line | files)"
    for b in $(echo "$branches" | grep -v '^dependabot/'); do
      gh api -X GET "repos/$REPO/commits" -f sha="$b" -f since="$since" -f author="$FRIEND" -f per_page=30 \
        --jq '.[] | [.sha[0:7], .commit.author.date, (.commit.message | split("\n")[0])] | @tsv' 2>/dev/null |
      while IFS=$'\t' read -r sha when msg; do
        files=$(gh api "repos/$REPO/commits/$sha" --jq '[.files[].filename] | .[0:6] | join(", ")' 2>/dev/null)
        echo "$b | $when | $sha | $msg | $files"
      done
    done | sort -u -t'|' -k3,3
    echo "-- pull requests updated since $since (number | state | author | branch | updated | title)"
    gh pr list -R "$REPO" --state all --limit 30 --json number,title,author,updatedAt,state,headRefName \
      --jq ".[] | select(.updatedAt > \"$since\") | [.number, .state, .author.login, .headRefName, .updatedAt, .title] | join(\" | \")" 2>&1
    echo "-- issues updated since $since"
    gh issue list -R "$REPO" --state all --limit 30 --json number,title,author,updatedAt,state \
      --jq ".[] | select(.updatedAt > \"$since\") | [.number, .state, .author.login, .updatedAt, .title] | join(\" | \")" 2>&1
    echo "-- YOUR_FRIEND's comments, reviews and other events since $since (time | type | detail)"
    gh api "repos/$REPO/events?per_page=100" \
      --jq ".[] | select(.actor.login == \"$FRIEND\" and .created_at > \"$since\" and .type != \"PushEvent\") | [.created_at, .type, (.payload.action // .payload.ref // \"\")] | join(\" | \")" 2>&1
    echo "(end of GitHub)"
  fi
fi

section "REMINDERS (Apple Reminders, open, overdue or due in 7 days; read-only)"
osascript -l JavaScript _system/tools/reminders.js > /tmp/.ebrief_reminders.$$ 2>&1 &
rpid=$!
( sleep 60; kill "$rpid" 2>/dev/null ) &
wpid=$!
if wait "$rpid" 2>/dev/null; then cat /tmp/.ebrief_reminders.$$; else echo "not checked: Reminders did not answer in 60 s or access is not allowed"; fi
kill "$wpid" 2>/dev/null
{ wait "$wpid"; } 2>/dev/null
rm -f /tmp/.ebrief_reminders.$$
