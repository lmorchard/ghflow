---
skills: [prepare-project-facts]
source: references/tasks/prepare-project-facts.md write one screen of stable facts
---

## Situation

You are writing `.ghflow/project.md` for a project. You have the worktree setup commands, the gates, the generated files, and the notes convention from the instructions and the Makefile. You are considering adding the current head of `origin/main`, the open PRs, the board status of the issue you were reading, and the configured identity login, so that the next worker has them without a lookup.

## Expected

Leave the live state out: the head, branches, PRs, board status, worktrees, and identity change between sessions, and `facts --issue` reads them on demand. End the file with that command as the way to get live state. Record only stable facts, list each source file with its blob hash in the frontmatter, and keep the file to about one screen.

## Not acceptable

- Recording the current head, open PRs, board status, worktrees, or identity in the file.
- Omitting the source hashes, so that `facts` cannot report stale sources.
- Writing procedures that the ghflow task references already own.
- Letting the file grow past about one screen to hold everything.
