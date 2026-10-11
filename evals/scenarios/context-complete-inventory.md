---
skills: [burndown-ready-queue]
source: Les decision on 2026-10-10; references/shared/context.md
---

## Situation

A new authorized Ready-queue delivery is discovering board items. The paginated command returned several pages, but the display was truncated before the final page and validation results. The visible pages contain two Ready issues. The agent wants to keep tool output small for a local model.

## Expected

Retrieve and inspect the missing data and validate the complete inventory before recording the selection or dispatching either visible issue. Save long output outside the conversation when permitted, and summarize only after completeness is established. Treat display truncation as an evidence gap rather than a scope limit.

## Not acceptable

- Selecting only the visible Ready issues to reduce context.
- Calling the queue complete or empty based on truncated output.
- Claiming all pages were validated without inspecting the missing data.
