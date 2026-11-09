# ghflow root-package setup trial

Les selected a repository-root skill package for PR #17.
This trial repeats [issue #16](https://github.com/lmorchard/gh-project-workflow/issues/16) setup checks after that change.
The earlier [nested-package trial](2026-10-07-ghflow-setup.md) remains a historical record.

## Local checks

Commit `ff0be9cd57fcfe8241e3fdd6a020272d84eed29f` moves the entry and references to the source checkout root.
Installation links point to that root. The gateway uses `cli/ghflow.py` directly, with the target project as the current directory.
The redundant launcher is removed.

`make check` passes 103 tests, structure, local links, scenario source paths, and whitespace against the empty Git tree.
Tests establish repeated installation, refusal of conflicts, live source edits, and CLI access through a root link from another directory.
They also establish caller-relative identity configuration and exclusion of ignored worktrees from repository structure checks.
The structure check does not establish native agent discovery behavior.

## Native sources and models

Fresh fixtures are in `/tmp/ghflow-root-trial-hs2x_kl6`.
The source is `/Users/lmorchard/devel/mine/gh-project-workflow/.claude/worktrees/issue-16-ghflow`.
Each target is a new Git repository with `README.md` and `request.txt` about optional task due dates.

Six fresh sessions requested drafts and separate read-only delivery assessments.
The prompts supplied no expected answers. Each process completed with exit status 0.

| Client | Version | Model evidence |
|---|---|---|
| Claude Code | `2.1.293` | Runtime startup and assistant metadata: `claude-opus-5-5` |
| Codex | `0.161.0` | Configuration selected `gpt-6-astra`, effort `high`; returned model identity unavailable |
| OpenCode | `1.18.35` | Sanitized export: provider `opencode`, model `big-pickle`, agent `plan` |

Codex reported an unknown enterprise requirement, `ultrafast_mode`. Both requests still completed.
OpenCode used the supported model selected in the earlier trial, rather than its invalid configured Ollama model.
Its session export is `opencode-draft-export.json`, for `ses_ee74f61c5ffe60Hd82rWFGcD1Z`.

## Discovery and dependency access

Claude's `.claude/skills/ghflow` and Codex's `.agents/skills/ghflow` point directly to the source checkout root.
OpenCode has both compatible links to that root.
All three resolve root `SKILL.md`, task and shared references, `docs/writing.md`, and direct `cli/ghflow.py`.
All three execute CLI help successfully from the target project.

Claude's startup inventory contains one workflow skill. References do not become separate skills.
Codex discovers and reads `ghflow`, but its JSON interface does not report a complete skill inventory.
OpenCode's clean-source inventory contains exactly one project `ghflow` and no separately registered references.

OpenCode selected the `.claude` link in this trial. The earlier trial selected `.agents`.
The result establishes duplicate removal, rather than stable precedence.
A separate fixture with only `.claude` also discovers one `ghflow`.

## Draft and delivery behavior

All three select `define-issue`, read task, shared, and writing references, and produce drafts in the response.
They identify missing application code and revision evidence. They do not publish or implement.
Writing-guidance access does not establish full ASD-STE100 compliance.

All three select `express-issue` for the delivery assessment.
They retain review-follow-up with an open PR and fresh, different-model independent review with recorded identities.
They retain explicit merge authorization. They perform no dispatch or delivery writes.

Claude lacks dispatch tools in the restricted harness.
Codex reports available dispatch and model tools, but the prompt prohibits dispatch.
OpenCode's Task interface lacks a model argument, so reviewer selection remains unverified through that interface.
These assessments do not establish complete implementation or delivery.

## OpenCode subject-resolution deviation

The selected issue was missing from the assessment fixture.
OpenCode read source-checkout Git metadata and used the source remote as the task repository.
It then searched live repository, project, and owner-wide issue inventories.
It claimed that the due-date issue did not exist. The supplied fixture did not establish that claim.

The original prompt authorized only a read-only routing assessment.
This behavior crossed the intended subject boundary, although no GitHub write occurred.
Its identity read reported metadata and token presence, without a token value.

Commit `5bc76033443adaf58bb4313ae9b15022a6033e2d` clarifies the gateway's subject rule.
The source supplies instructions and tools. The user or target checkout identifies the subject.
Missing selected subjects return an input request before GitHub searches or dispatch.
A fresh OpenCode retest used the unchanged delivery prompt and completed with exit status 0.
It selected `express-issue` and retained the open-PR endpoint and different-model review requirement.
It returned missing repository and issue inputs before searching or dispatching.
It made no issue, repository, project, or owner-wide searches, and no issue-absence claim.

The retest ran CLI help through direct and symlink paths from the target directory.
It also read `gh` version, authentication status, and identity metadata for capability assessment.
It read the existing setup trial record as additional context.
The result establishes corrected behavior in this session, rather than an evaluation without prior trial evidence.

## Nested worktree discovery

An isolated source fixture contains root `SKILL.md` and `.claude/worktrees/demo/SKILL.md`.
The nested skill is named `nested-trial-sentinel`.
The fixture's `.gitignore` ignores `.claude/worktrees/`. `git check-ignore -v` confirms that exclusion.
OpenCode nevertheless discovers both skills through the root symlink.

A `watcher.ignore` rule did not prevent discovery.
A skill-name deny rule also left both entries in raw `debug skill` output.
No model session assessed the denied skill's visibility in the tool description.

[OpenCode skill permissions](https://opencode.ai/docs/skills/#configure-permissions) support denial by skill name.
The [configuration schema](https://opencode.ai/config.json) provides additional skill paths and URLs, with no skill path exclusion.
[Watcher configuration](https://opencode.ai/docs/config/#watcher) controls file watching.

Clean-source discovery succeeds, but ignored nested worktrees can expose additional skills in OpenCode `1.18.35`.
Les selected a document-only policy for this limitation on 2026-10-07.
Root checkout links remain permitted for a clean source checkout. The installer does not reject nested skill packages.
Inspect and maintain source worktrees through authorized cleanup.
Preserve worktrees with uncommitted changes or an open PR.
If unwanted skills appear, use a separate source checkout without nested skill packages.
No installer guard, permission workaround, or worktree removal was applied.

On 2026-11-09, the OpenCode installation at `~/.agents/skills/ghflow` changed from a symbolic link to a separate checkout.
OpenCode had selected a worktree copy of the skill through the root link.
The separate checkout has no worktrees, so native discovery sees one copy.
The tradeoff is a stale checkout. Refresh it after skill changes with `git -C ~/.agents/skills/ghflow pull --ff-only`.
[Setup](../../setup.md#opencode-separate-checkout) records the procedure.

## Review decision for PR #17

The original implementation model identity remains unknown.
Independent reviewer `gpt-6-astra` reviewed head `883786d5bb3fea2514ee41c267460d986d0a6faa` with no new actionable findings.
This review does not prove that the reviewer used a different model from the implementer.
Les accepted this review for PR #17 on 2026-10-07.
The exception applies only to this task and permits progress after checks of the current head.
It does not change the shared review policy or authorize merge.

## Source permissions and limits

Claude uses `--add-dir` for source access.
OpenCode's temporary project configuration denies edits and permits only the source checkout as an external directory.
All three read source writing guidance successfully.
The installer changes no permissions.

Claude's draft session initially denied a compound help command under restricted Bash rules.
Its separate delivery session ran standalone CLI help successfully.
Codex's initial here-document read hit its read-only sandbox. A later read succeeded.
These are harness limits, rather than root-path failures.

No personal installation, global configuration change, copied credentials, or source edit occurred in the native trials.
The agents changed no target application files, GitHub records, commits, or branches.
Existing runtime directories can retain logs, sessions, and caches.
The trial setup added only temporary links and scoped configuration.

## Command shapes

Claude, from fixture/claude:

```sh
/Users/lmorchard/.local/bin/claude -p --no-session-persistence --output-format stream-json --verbose --permission-mode dontAsk --tools Read,Bash,Skill --allowedTools 'Read' 'Skill' 'Bash(python3 *)' 'Bash(realpath *)' 'Bash(pwd)' 'Bash(echo *)' --strict-mcp-config --setting-sources project --add-dir /Users/lmorchard/devel/mine/gh-project-workflow/.claude/worktrees/issue-16-ghflow < /tmp/ghflow-root-trial-hs2x_kl6/draft-prompt.txt
```

Codex:

```sh
/Users/lmorchard/.local/bin/codex exec --ephemeral --sandbox read-only --json -C /tmp/ghflow-root-trial-hs2x_kl6/codex - < /tmp/ghflow-root-trial-hs2x_kl6/draft-prompt.txt
```

Both delivery sessions substitute delivery-prompt.txt.

OpenCode:

```sh
/Users/lmorchard/.opencode/bin/opencode run --pure --agent plan --format json -m opencode/big-pickle --dir /tmp/ghflow-root-trial-hs2x_kl6/opencode '<read-only draft or delivery prompt>'
```

Exact prompts and JSONL logs remain beside the temporary report.
Native discovery runs `opencode debug skill` from the fixture directory.
The tool resolves to `SOURCE/cli/ghflow.py` and runs from the target directory.
Runtime access uses narrow execution escalation. Codex commands remain in a read-only sandbox.
OpenCode uses the plan agent and denies edits.
The focused retest uses the same OpenCode command with the original delivery prompt.
Its stream is `opencode-delivery-correction.jsonl`.
