// OpenCode plugin: refuse a subagent dispatch or resume whose prompt is a placeholder.
//
// Three of three local-model delivery runs sent a `task` call with a prompt such as
// "placeholder" or "x" at a resume step, then spent 10 to 20 minutes recovering.
// Skill text fixed the recovery and did not prevent the slip. This hook makes the
// call fail before it reaches the worker, so the coordinator writes the handoff
// and calls again.
//
// Install: symlink or copy this file into ~/.config/opencode/plugins/ (global) or
// .opencode/plugins/ in a project. See docs/setup.md, "Dispatch guard".
// Self-test: node scripts/opencode-plugins/ghflow-dispatch-guard.js --self-test

export const MIN_PROMPT_CHARS = 120;

// Return a reason to refuse, or null to allow. Exported so the rule is testable.
export function refusal(tool, args, minChars = MIN_PROMPT_CHARS) {
  if (tool !== "task") return null;
  const prompt = typeof args?.prompt === "string" ? args.prompt.trim() : "";
  if (prompt.length >= minChars) return null;
  const shown = prompt.length ? JSON.stringify(prompt.slice(0, 40)) : "an empty prompt";
  return (
    `ghflow dispatch guard: the task prompt is ${prompt.length} characters (${shown}); ` +
    `a handoff is at least ${minChars}. Write the full handoff and call task again.`
  );
}

export const GhflowDispatchGuard = async () => ({
  "tool.execute.before": async (input, output) => {
    const reason = refusal(input?.tool, output?.args);
    if (reason) throw new Error(reason);
  },
});

if (process.argv.includes("--self-test")) {
  const cases = [
    ["task", { prompt: "placeholder" }, true],
    ["task", { prompt: "x" }, true],
    ["task", {}, true],
    ["task", { prompt: " ".repeat(200) }, true],
    ["task", { prompt: "Operation: submit-pr. ".repeat(10) }, false],
    ["bash", { command: "ls" }, false],
    ["read", { filePath: "x" }, false],
  ];
  let failed = 0;
  for (const [tool, args, expectRefuse] of cases) {
    const got = refusal(tool, args) !== null;
    if (got !== expectRefuse) {
      failed += 1;
      console.error(`FAIL ${tool} ${JSON.stringify(args).slice(0, 40)}: refused=${got}, expected ${expectRefuse}`);
    }
  }
  console.log(failed ? `${failed} self-test case(s) failed` : `self-test passed (${cases.length} cases)`);
  process.exit(failed ? 1 : 0);
}
