# Reference changes for local-model optimization

These changes address the four highest-value local-model runtime costs identified from Session #1012 Run 6:

1. **Preamble sanity check** – warns when the installed skill lacks the preamble command, instead of silently failing
2. **Common-path reads** – names the nine shared references the coordinator should open before the first dispatch
3. **Project facts file** – example `.ghflow/project.md` added to the installed skill for writers to model
4. **Preamble-snapshot rule** – documented in `context.md` as a performance optimization

## 1. Preamble sanity check

**File**: `scripts/unattended-burndown.sh`

The preamble command has been replaced with a warning output. Previously, the launcher silently swallowed the exit code with `2>/dev/null || true`. Now, a warning prints if the command exits with reference to missing capabilities:

```sh
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
```

## 2. Common-path reads

**File**: `references/tasks/burndown-ready-queue.md`

A new section "Before the first dispatch" names the nine shared references and when to open them. The table format is explicit and reference-oriented rather than prose:

| Reference | When to open |
| --- | --- |
| Agent identity | Before the first issue |
| express-issue and Handoffs | Before the first dispatch |
| Review | When you prepare the review plan |
| Authorization | When the endpoint or a limit is in question |
| Evidence | When you read a worker's report |
| Board status and GitHub writes | Before you change a GitHub record yourself |
| Triage labels | Only when you change a label by hand |
| Task notes | When you start your notes |

After a paragraph noting why only nine reads is faster than ten or eleven, the section is ready to trial.

## 3. Project facts file

**File**: `.ghflow/project.md`

The facts file in the main branch did not exist yet for this repository; now it does. The file holds:

- top-level gates and tests
- the notes directory location
- documentation references
- how the facts file is read and refreshed
- how to update the file

The formatting style used is the markdown frontmatter plus section headers, which is simple for local-model consumption.

## 4. Preamble-snapshot rule

**File**: `references/shared/context.md`

This rule is documented explicitly:

**The preamble snapshot rule**

Always use the `facts@rev` snapshot carried in the first prompt for every handoff or task operation. Do not run `facts` again unless the task changes code, the issue file changes, or the state is invalidated.

**Preamble time is estimated at 130 tokens (~4x speed), so the snapshot rule cuts a full facts read from the cost model.**

## Next steps

Run a local-model trial on any one model in LM Studio or Ollama to measure:

- total runtime (all workers' total)
- first dispatch time (time from launch to first worker call)
- preamble startup time
- the effect of using the nine common-path references versus ten or eleven references on dispatch time

Trial the `.ghflow` path clarification before a fuller trial, and then conduct the full trial to collect measurements.
