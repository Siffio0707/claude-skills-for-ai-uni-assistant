#!/bin/bash
# Read-only gather for the morning-digest skill. No arguments.
# Waits up to 7 minutes if this morning's sync has not finished yet.
# Prints labelled sections; a failing section never stops the others.
# Writes nothing and makes no network call.
cd "$(dirname "$0")/../.." || exit 1

section() { printf '\n=== %s ===\n' "$1"; }

section "NOW (YOUR_TIMEZONE)"
TZ=YOUR_TIMEZONE date '+%Y-%m-%d %H:%M %A'

section "TODAY (YOUR_TIMEZONE), with its window in UTC for the Canvas calendar tool"
today=$(TZ=YOUR_TIMEZONE date '+%Y-%m-%d')
start=$(TZ=YOUR_TIMEZONE date -j -f '%Y-%m-%d %H:%M:%S' "$today 00:00:00" '+%s')
end=$(TZ=YOUR_TIMEZONE date -j -f '%Y-%m-%d %H:%M:%S' "$today 23:59:59" '+%s')
echo "date=$today"
echo "long=$(TZ=YOUR_TIMEZONE date -r "$start" '+%A %-d %B %Y')"
echo "since=$(date -u -r "$start" '+%Y-%m-%dT%H:%M:%SZ')"
echo "until=$(date -u -r "$end" '+%Y-%m-%dT%H:%M:%SZ')"
echo "local_utc_offset=$(TZ=YOUR_TIMEZONE date -r "$((start + 43200))" '+%z')"

# Has this morning's 06:00 sync finished? It writes last_run / last_result to sync-state.json at its end.
# "Finished" = last_run (UTC) is at or after 05:30 your city today. A login_failure_at after that means it stopped.
epoch_of() { date -j -u -f '%Y-%m-%dT%H:%M:%S' "${1%%.*}" '+%s' 2>/dev/null; }
sync_status() {
  local threshold lr lf lr_e lf_e
  threshold=$(TZ=YOUR_TIMEZONE date -j -f '%Y-%m-%d %H:%M:%S' "$today 05:30:00" '+%s')
  lr=$(sed -n 's/.*"last_run": *"\([^"]*\)".*/\1/p' _system/sync-state.json | head -1)
  lf=$(sed -n 's/.*"login_failure_at": *"\([^"]*\)".*/\1/p' _system/sync-state.json | head -1)
  lr_e=$(epoch_of "$lr"); lf_e=$(epoch_of "$lf")
  if [ -n "$lf_e" ] && [ "$lf_e" -ge "$threshold" ]; then echo "failed (Canvas login expired at $lf UTC)"
  elif [ -n "$lr_e" ] && [ "$lr_e" -ge "$threshold" ]; then echo "done (last_run $lr UTC)"
  else echo "pending (last_run $lr UTC is before 05:30 your city today)"; fi
}

section "THIS MORNING'S SYNC (06:00): finished?"
st=$(sync_status)
case "$st" in
  pending*)
    echo "first check: $st"
    echo "waiting 7 minutes for the sync to finish, then checking once more"
    sleep 420
    st=$(sync_status) ;;
esac
echo "sync_status=$st"
echo "(sync_status starts with done, pending or failed; pending after this wait means: run this script again, up to 3 more times)"

section "THIS MORNING'S SYNC (top of whats-new.md, then sync-state)"
sed -n '5,22p' whats-new.md 2>&1
grep -E '"last_(run|result|summary)"' _system/sync-state.json 2>&1

section "SUMMARIES (FRESH = newer than its source and text copy)"
find . -path './_system' -prune -o -path '*/_summaries/*.summary.md' -type f -print 2>/dev/null | sort | while IFS= read -r s; do
  s=${s#./}
  src=$(sed -n 's/^- Source: //p' "$s" | head -1)
  txt=$(sed -n 's/^- Text copy: //p' "$s" | head -1)
  pages=$(sed -n 's/^- Pages covered: //p' "$s" | head -1)
  if [ -z "$src" ] || [ ! -f "$src" ]; then state="SOURCE MISSING"
  elif [ "$src" -nt "$s" ] || { [ -n "$txt" ] && [ -f "$txt" ] && [ "$txt" -nt "$s" ]; }; then state="STALE"
  else state="FRESH"; fi
  printf '%s | %s | source: %s | pages: %s\n' "$state" "$s" "$src" "$pages"
done
echo "(end of summaries)"

section "morning-digest folder"
ls -1 morning-digest 2>&1

section "morning-digest/_log.md (last 5 lines)"
tail -5 morning-digest/_log.md 2>&1

section "_inbox (files YOUR_NAME may have downloaded by hand)"
find _inbox -type f ! -name '.DS_Store' 2>/dev/null | sort
echo "(end of _inbox)"
