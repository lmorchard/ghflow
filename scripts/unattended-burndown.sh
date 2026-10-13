#!/bin/sh
# Compose the request for an unattended Ready-queue burndown and launch one agent session with it.
# Run from the target project checkout. See docs/setup.md, "Run a queue unattended".
set -eu

OWNER=""; PROJECT=""; HOURS="8"; AGENT="opencode"; MODEL=""; EXCEPTION="no"; DRY_RUN="no"; LOG=""
SKILL_DIR="${GHFLOW_SKILL_DIR:-$HOME/.agents/skills/ghflow}"

usage() {
  cat <<USAGE
usage: $0 --owner OWNER --project NUMBER [--hours N] [--agent opencode|claude|codex] [--model MODEL]
          [--same-model-exception] [--skill-dir DIR] [--log FILE] [--dry-run]
USAGE
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --owner) OWNER="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --hours) HOURS="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --same-model-exception) EXCEPTION="yes"; shift ;;
    --skill-dir) SKILL_DIR="$2"; shift 2 ;;
    --log) LOG="$2"; shift 2 ;;
    --dry-run) DRY_RUN="yes"; shift ;;
    *) usage ;;
  esac
done
[ -n "$OWNER" ] && [ -n "$PROJECT" ] || usage

REPO=$(git remote get-url origin 2>/dev/null | sed -E 's#.*github\.com[:/]([^/]+/[^/.]+)(\.git)?/?$#\1#') || true
[ -n "$REPO" ] || { echo "not in a checkout with a GitHub origin" >&2; exit 1; }
STAMP=$(date +%Y%m%d-%H%M%S)
[ -n "$LOG" ] || LOG="unattended-burndown-$STAMP.log"
if date -v+1H >/dev/null 2>&1; then DEADLINE=$(date -v+"$HOURS"H "+%Y-%m-%d %H:%M %Z"); else DEADLINE=$(date -d "+$HOURS hours" "+%Y-%m-%d %H:%M %Z"); fi

REQUEST="Use ghflow to deliver the Ready queue of project $PROJECT owned by $OWNER for $REPO through PR review follow-up, without merge. This run is unattended: take a supported recommended answer and record it in the PR description, park an issue you cannot settle under triage:needs-input with the question as an issue comment, and continue with the next selected issue; do not call an interactive question tool. Time budget: do not start an issue after $DEADLINE; park an issue in progress at that time with its state recorded. Halt only if the identity check fails, the base branch CI is red, or the same environment failure parks two issues in a row. End with the delivery summary table."
if [ "$EXCEPTION" = "yes" ]; then
  REQUEST="$REQUEST Use the same local model for implementation and review under my approved exception for OpenCode with the local model on this laptop."
fi

case "$AGENT" in
  opencode)
    [ -f "$SKILL_DIR/SKILL.md" ] || { echo "entry skill not found at $SKILL_DIR/SKILL.md" >&2; exit 1; }
    # Drop the YAML frontmatter: a message that starts with "---" is parsed as an option and prints help.
    SKILL_BODY=$(awk 'NR==1 && $0=="---" {skip=1; next} skip && $0=="---" {skip=0; next} !skip' "$SKILL_DIR/SKILL.md" | sed '/./,$!d')
    PROMPT="$SKILL_BODY

Base directory for this skill: $SKILL_DIR
Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.

$REQUEST"
    set -- opencode run --auto --format json --title "Unattended burndown $STAMP"
    [ -n "$MODEL" ] && set -- "$@" --model "$MODEL"
    set -- "$@" "$PROMPT" ;;
  claude)
    set -- claude -p --permission-mode acceptEdits
    [ -n "$MODEL" ] && set -- "$@" --model "$MODEL"
    set -- "$@" "$REQUEST" ;;
  codex)
    set -- codex exec
    [ -n "$MODEL" ] && set -- "$@" --model "$MODEL"
    set -- "$@" "$REQUEST" ;;
  *) usage ;;
esac

if command -v caffeinate >/dev/null 2>&1; then set -- caffeinate -i "$@"; fi

if [ "$DRY_RUN" = "yes" ]; then
  echo "--- request ---"; echo "$REQUEST"; echo "--- command ---"
  for arg in "$@"; do case "$arg" in *"$REQUEST"*) printf '%s ' "'<prompt>'" ;; *) printf '%s ' "'$arg'" ;; esac; done; echo
  echo "--- log: $LOG"
  exit 0
fi

case "$PROMPT" in -*) echo "composed prompt starts with '-'; refusing to launch" >&2; exit 1 ;; esac
echo "launching $AGENT at $(date); log $LOG; deadline $DEADLINE"
status=0
"$@" > "$LOG" 2>&1 || status=$?
echo "finished at $(date); exit $status"
if [ "$status" -ne 0 ]; then echo "$AGENT exited with status $status; see $LOG" >&2; exit "$status"; fi
