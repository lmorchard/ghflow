#!/bin/sh
# Compose the request for an unattended Ready-queue burndown and launch one agent session with it.
# Run from the target project checkout. See docs/setup.md, "Run a queue unattended".
set -eu

OWNER=""; PROJECT=""; HOURS="8"; AGENT="opencode"; MODEL=""; EXCEPTION="no"; DRY_RUN="no"; LOG=""; ALLOW_CONCURRENT="no"
SKILL_DIR="${GHFLOW_SKILL_DIR:-$HOME/.agents/skills/ghflow}"

[ -n "$REPO" ] || { echo "not in a checkout with a GitHub origin" >&2; exit 1; }
STAMP=$(date +%Y%m%d-%H%M%S)
[ -n "$LOG" ] || LOG="unattended-burndown-$STAMP.log"
if date -v+1H >/dev/null 2>&1; then DEADLINE=$(date -v+"$HOURS"H "+%Y-%m-%d %H:%M %Z"); else DEADLINE=$(date -d "+$HOURS hours" "+%Y-%m-%d %H:%M %Z"); fi

REQUEST="Use ghflow to deliver the Ready queue of project $PROJECT owned by $OWNER for $REPO through PR review follow-up, without merge. This run is unattended: take a supported recommended answer and record it in the PR description, park an issue you cannot settle under triage:needs-input with the question as an issue comment, and continue with the next selected issue; do not call an interactive question tool. Time budget: do not start an issue after $DEADLINE; park an issue in progress at that time with its state recorded. Halt only if the identity check fails, the base branch CI is red, or the same environment failure parks two issues in a row. End with the delivery summary table."
if [ "$EXCEPTION" = "yes" ]; then
  REQUEST="$REQUEST Use the same local model for implementation and review under my approved exception for OpenCode with the same local model on this laptop."
fi

# Give the first prompt the compact project facts, so a slow local model does not
# spend turns rediscovering them. A missing preamble means the installed skill
# lacks the optimization; warn once and continue.
PREAMBLE=$(python3 "$SKILL_DIR/cli/ghflow.py" preamble 2>&1 1>/dev/null || true)
WARNING=0
if echo "$PREAMBLE" | grep -q -e "cannot be read" -e "does not exist" -e "ModuleNotFoundError"; then
  WARNING=1
fi
if [ -n "$PREAMBLE" ]; then
  REQUEST="$REQUEST

$PREAMBLE"
fi
if [ "$WARNING" -eq 1 ]; then
  echo "warning: the installed ghflow lacks the preamble command; startup and first-dispatch will be slower" >&2
fi

# An OpenCode run keeps going on OpenCode's background service after its client exits, so a
# finished launch does not prove the run ended. Refuse to start a second coordinator on the queue.
active_opencode_runs() {
  opencode session list --format json < /dev/null 2>/dev/null | python3 -c '
import json, sys, time
try:
    sessions = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
now = time.time() * 1000
for s in sessions if isinstance(sessions, list) else []:
    t = s.get("time")
    t = t.get("updated") if isinstance(t, dict) else (t or s.get("updated"))
    if str(s.get("title", "")).startswith("Unattended burndown") and isinstance(t, (int, float)) and now - t < 30 * 60 * 1000:
        print(s.get("id"), s.get("title"))
' || true
}

preflight_warnings() {
  if command -v memory_pressure >/dev/null 2>&1; then
    free=$(memory_pressure 2>/dev/null | awk '/free percentage/ {gsub("%", "", $NF); print $NF}')
    if [ -n "$free" ] && [ "$free" -lt 30 ]; then
      echo "warning: only ${free}% of memory is free; other jobs slow the local model and can exhaust its cache" >&2
    fi
  fi
  if pgrep -f com.apple.Virtualization.VirtualMachine >/dev/null 2>&1; then
    echo "warning: a virtual machine, such as Docker Desktop's, is running and holding memory" >&2
  fi
}

