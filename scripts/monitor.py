"""Deterministic monitor for the queue runner.

The monitor collects the checks that a coordinator used to run by hand. It is
read-only apart from ``monitor.json`` and ``monitor.md`` in the run notes
directory. Each check records its phase, level, state, message, and evidence.
A stop-level failure stops the run.

The runner calls the monitor at preflight, at phase boundaries, on a fixed
interval during a session, and after each session. The report is also the
replay input: ``replay`` feeds an observation fixture through the same checks.
"""
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

SCHEMA = "ghflow-monitor/1"
JSON_NAME = "monitor.json"
MARKDOWN_NAME = "monitor.md"
DEFAULT_INTERVAL_SECONDS = 300

STOP = "stop"
ALERT = "alert"
INFO = "info"

PASS = "pass"
FAIL = "alert"
UNKNOWN = "unknown"
SKIP = "skip"

def _iso(seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def _now(clock):
    return _iso(clock())


def make_check(name, phase, level, state, message, evidence=None, clock=time.time):
    """Build one report entry with a stable shape."""
    return {
        "name": name,
        "phase": phase,
        "level": level,
        "state": state,
        "message": message,
        "evidence": evidence or {},
        "at": _now(clock),
    }


def _state(ok, unknown=False):
    if unknown:
        return UNKNOWN
    return PASS if ok else FAIL


def _numbers(selection):
    """Return issue numbers from queue or parent records."""
    numbers = []
    for item in selection or []:
        if not isinstance(item, dict):
            continue
        number = item.get("number")
        if number is None:
            text = str(item.get("issue") or item.get("url") or "")
            match = re.search(r"(\d+)\s*$", text)
            number = int(match.group(1)) if match else None
        if number is not None:
            numbers.append(number)
    return numbers


def _issue_number(value):
    text = str(value or "")
    match = re.search(r"(\d+)\s*$", text)
    return int(match.group(1)) if match else None


def probe_model(model, opencode_cmd="opencode", timeout=20):
    """Return whether ``opencode models`` lists the requested model.

    ``None`` means the check could not run: OpenCode is missing, the command
    failed, or the output is unusable.
    """
    if not model:
        return None
    try:
        proc = subprocess.run([opencode_cmd, "models"], stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    names = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not names:
        return None
    return model in names or any(name.endswith(model) or model.endswith(name) for name in names)


def probe_endpoint(base_url, timeout=3):
    """Return whether a local model endpoint answers, or None when it is unset."""
    if not base_url:
        return None
    for suffix in ("/health", "/v1/models"):
        url = base_url.rstrip("/") + suffix
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                if 200 <= response.status < 300:
                    return True
        except urllib.error.HTTPError as error:
            if error.code < 500:
                return True
        except (urllib.error.URLError, OSError, ValueError):
            continue
    return False


class Monitor:
    """Collect checks and write the run's monitor report."""

    def __init__(self, notes_dir, clock=time.time, write=True):
        self.notes_dir = Path(notes_dir)
        self.clock = clock
        self.started = clock()
        self.checks = []
        self.events = []
        self.stopped = None
        self.phase = "preflight"
        self.context = {}
        self.counts = {}
        self.budget = {}
        self._write_enabled = write
        self._last_write = 0.0
        self._finished = False
        self.processed_numbers = set()

    # -- recording -----------------------------------------------------

    def add(self, name, phase, level, state, message, evidence=None):
        entry = make_check(name, phase, level, state, message, evidence, self.clock)
        self.checks.append(entry)
        if level == STOP and state == FAIL and not self.stopped:
            self.stopped = f"{name}: {message}"
        return entry

    def event(self, kind, **fields):
        entry = {"event": kind, "at": _now(self.clock)}
        entry.update(fields)
        self.events.append(entry)

    def alerts(self):
        return [check for check in self.checks if check["state"] == FAIL]

    # -- preflight -----------------------------------------------------

    def preflight(self, facts, identity=None, exec_login=None, lock=None, model=None,
                  model_available=None, model_map=None, endpoint_configured=None, endpoint_ok=None):
        """Record the checks that run before the first issue."""
        self.phase = "preflight"
        facts = facts or {}
        identity = identity if identity is not None else (facts.get("identity") or {})
        configured = identity.get("login") or identity.get("user")
        ready = identity.get("ready")
        if not identity:
            self.add("identity", "preflight", STOP, UNKNOWN,
                     "Identity facts are missing.")
        elif ready is None:
            self.add("identity", "preflight", ALERT, UNKNOWN,
                     "Identity readiness was not read.",
                     {"login": configured, "source": identity.get("source")})
        elif not ready:
            self.add("identity", "preflight", STOP, FAIL,
                     "The configured identity is not ready.",
                     {"login": configured, "source": identity.get("source")})
        elif exec_login and configured and exec_login != configured:
            self.add("identity", "preflight", STOP, FAIL,
                     f"`gh api user` returns {exec_login}, not {configured}.",
                     {"configured": configured, "effective": exec_login})
        elif exec_login:
            self.add("identity", "preflight", STOP, PASS,
                     f"`gh api user` returns {exec_login}.",
                     {"login": exec_login})
        else:
            self.add("identity", "preflight", ALERT, UNKNOWN,
                     "The `gh api user` login was not read.",
                     {"login": configured})

        if model_map:
            self.add("model", "preflight", ALERT, PASS,
                     f"Per-issue model map loaded from {model_map.get('path')}.",
                     {"path": model_map.get("path"),
                      "models": sorted(model_map.get("models") or {}),
                      "review": sorted(model_map.get("review") or {})})
        elif model:
            if model_available is None:
                self.add("model", "preflight", ALERT, UNKNOWN,
                         f"The requested model `{model}` was not checked.",
                         {"model": model})
            elif model_available:
                self.add("model", "preflight", ALERT, PASS,
                         f"The requested model `{model}` is installed.",
                         {"model": model})
            else:
                self.add("model", "preflight", ALERT, FAIL,
                         f"The requested model `{model}` is not listed by opencode.",
                         {"model": model})
        else:
            self.add("model", "preflight", ALERT, SKIP,
                     "No model was requested; the runtime default applies.")

        if lock is None:
            self.add("runner_lock", "preflight", STOP, UNKNOWN,
                     "The run lock holder is unknown.")
        elif lock.get("error"):
            # acquire_run_lock already refuses a live holder. A missing read
            # after acquisition is a reporting limit, not a stop.
            self.add("runner_lock", "preflight", ALERT, UNKNOWN,
                     f"The run lock holder could not be read: {lock['error']}.",
                     lock)
        elif not lock.get("pid"):
            self.add("runner_lock", "preflight", ALERT, UNKNOWN,
                     "The run lock holder is not named.", lock)
        else:
            holder = lock.get("pid")
            self.add("runner_lock", "preflight", STOP, PASS,
                     f"The run lock is held by pid {holder}.",
                     {key: lock.get(key) for key in ("pid", "started", "target", "notes_dir", "path")})

        checkout = facts.get("checkout") or {}
        dirty = checkout.get("dirty")
        if dirty is None:
            self.add("checkout", "preflight", ALERT, UNKNOWN,
                     "The primary checkout state is unknown.")
        elif dirty:
            self.add("checkout", "preflight", ALERT, FAIL,
                     "The primary checkout has uncommitted changes.",
                     {"dirty": dirty, "branch": checkout.get("branch")})
        else:
            self.add("checkout", "preflight", ALERT, PASS,
                     "The primary checkout is clean.",
                     {"branch": checkout.get("branch"), "head": checkout.get("head")})

        repository = facts.get("repository") or {}
        local = repository.get("local_default_head")
        remote = repository.get("origin_default_head")
        if not local or not remote:
            self.add("checkout_current", "preflight", ALERT, UNKNOWN,
                     "The local and origin default heads were not both read.")
        elif local != remote:
            self.add("checkout_current", "preflight", ALERT, FAIL,
                     "The local default branch is not at origin.",
                     {"local": local, "origin": remote})
        else:
            self.add("checkout_current", "preflight", ALERT, PASS,
                     "The local default branch is at origin.",
                     {"head": local})

        source = facts.get("skill_source") or {}
        up_to_date = source.get("up_to_date")
        if up_to_date is None:
            self.add("skill_source", "preflight", ALERT, UNKNOWN,
                     "The skill source state is unknown.")
        elif up_to_date:
            self.add("skill_source", "preflight", ALERT, PASS,
                     "The skill source is current.",
                     {"head": source.get("head")})
        else:
            self.add("skill_source", "preflight", ALERT, FAIL,
                     "The skill source is behind its remote.",
                     {"head": source.get("head"), "remote": source.get("remote_head")})

        base = facts.get("base_ci") or {}
        summary = str(base.get("summary") or "").lower()
        if summary in ("green", "passed", "passing"):
            self.add("base_ci", "preflight", STOP, PASS,
                     "Base CI is green.",
                     {"commit": base.get("commit"), "checks": base.get("checks")})
        elif summary in ("red", "failing", "failed", "error"):
            self.add("base_ci", "preflight", STOP, FAIL,
                     f"Base CI is {summary}; the run stops.",
                     {"commit": base.get("commit"), "checks": base.get("checks")})
        elif summary in ("missing", "none", ""):
            self.add("base_ci", "preflight", ALERT, FAIL,
                     f"Base CI is {summary or 'unread'}; no checks were reported.",
                     {"commit": base.get("commit"), "stale": base.get("stale")})
        else:
            self.add("base_ci", "preflight", ALERT, UNKNOWN,
                     f"Base CI is {summary}.",
                     {"commit": base.get("commit"), "stale": base.get("stale")})

        origin = ((facts.get("project_facts") or {}).get("origin") or {})
        stale = origin.get("stale_sources") or []
        if origin.get("present") is False:
            self.add("facts", "preflight", ALERT, SKIP,
                     "No project facts file is present on origin.")
        elif stale:
            paths = [source.get("path", "?") if isinstance(source, dict) else str(source)
                     for source in stale]
            self.add("facts", "preflight", ALERT, FAIL,
                     f"Project facts are stale on origin for: {', '.join(paths)}.",
                     {"stale_sources": paths})
        else:
            self.add("facts", "preflight", ALERT, PASS,
                     "Project facts are current on origin.")

        if endpoint_configured is None:
            self.add("model_endpoint", "preflight", ALERT, SKIP,
                     "No model endpoint probe was requested.")
        elif endpoint_ok is None:
            self.add("model_endpoint", "preflight", ALERT, UNKNOWN,
                     "The model endpoint was not checked.",
                     {"endpoint": endpoint_configured})
        else:
            self.add("model_endpoint", "preflight", ALERT, _state(endpoint_ok),
                     "The model endpoint answers." if endpoint_ok else "The model endpoint did not answer.",
                     {"endpoint": endpoint_configured})

    def selection(self, selection=None, required_labels=None, exclude_labels=None):
        """Record whether the selected issues match the requested labels."""
        items = list(selection or [])
        required = [label for label in (required_labels or []) if label]
        excluded = [label for label in (exclude_labels or []) if label]
        problems = []
        checked = 0
        for item in items:
            labels = item.get("labels") if isinstance(item, dict) else None
            if labels is None:
                continue
            checked += 1
            missing = [label for label in required if label not in labels]
            rejected = [label for label in excluded if label in labels]
            if missing or rejected:
                problems.append({"issue": item.get("number") or item.get("issue"),
                                 "missing": missing, "excluded": rejected})
        numbers = _numbers(items)
        evidence = {"issues": numbers, "checked_labels": checked}
        if problems:
            self.add("selection", "preflight", ALERT, FAIL,
                     "A selected issue does not match the requested labels.",
                     {**evidence, "problems": problems})
        else:
            self.add("selection", "preflight", ALERT, PASS,
                     f"{len(items)} selected issue(s) match the requested labels.",
                     evidence)

    # -- sessions ------------------------------------------------------

    def handoff_model(self, step, path, run_model):
        """Compare the model named in the handoff with the run model."""
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as error:
            self.add("handoff_model", "step", ALERT, UNKNOWN,
                     f"The handoff could not be read: {error}.",
                     {"step": step, "path": str(path)})
            return
        match = re.search(r"Review plan:\s*model\s+(\S+)", text)
        if not match:
            self.add("handoff_model", "step", ALERT, SKIP,
                     "The handoff names no model.",
                     {"step": step})
        elif not run_model:
            self.add("handoff_model", "step", ALERT, UNKNOWN,
                     "No run model is configured.",
                     {"step": step, "handoff_model": match.group(1)})
        elif match.group(1) == run_model:
            self.add("handoff_model", "step", ALERT, PASS,
                     f"The handoff names the run model `{run_model}`.",
                     {"step": step, "model": run_model})
        else:
            self.add("handoff_model", "step", ALERT, FAIL,
                     f"The handoff names `{match.group(1)}`, not the run model `{run_model}`.",
                     {"step": step, "handoff_model": match.group(1), "run_model": run_model})

    def session_sample(self, step, issue, session_id, alive, last_event_age,
                       context_tokens, turns, age, limits):
        """Record one periodic sample of a running session."""
        self.phase = "step"
        evidence = {"step": step, "issue": issue, "session": session_id,
                    "alive": alive, "last_event_age": last_event_age,
                    "context_tokens": context_tokens, "turns": turns, "age": age}
        self.add("session_alive", "step", ALERT, _state(alive),
                 "The session process is alive." if alive else "The session process is not alive.",
                 evidence)

        idle = limits.get("step_idle_timeout")
        if last_event_age is None or not idle:
            self.add("session_idle", "step", ALERT, UNKNOWN,
                     "The idle limit was not checked.", evidence)
        elif last_event_age > idle:
            self.add("session_idle", "step", ALERT, FAIL,
                     f"No event for {last_event_age:.0f}s; the idle limit is {idle}s.",
                     {**evidence, "idle_limit": idle})
        elif last_event_age > min(120, idle / 4):
            self.add("session_idle", "step", ALERT, FAIL,
                     f"No event for {last_event_age:.0f}s; the step is slow.",
                     {**evidence, "idle_limit": idle})
        else:
            self.add("session_idle", "step", ALERT, PASS,
                     "The last event is within the idle limit.",
                     {**evidence, "idle_limit": idle})

        warn = limits.get("context_warn_tokens")
        cap = limits.get("max_context_tokens")
        if context_tokens is None:
            self.add("session_context", "step", ALERT, UNKNOWN,
                     "The context size was not read.", evidence)
        elif cap and context_tokens >= cap:
            self.add("session_context", "step", ALERT, FAIL,
                     f"Context {context_tokens} reached the cap {cap}.",
                     {**evidence, "warn": warn, "cap": cap})
        elif warn and context_tokens >= warn:
            self.add("session_context", "step", ALERT, FAIL,
                     f"Context {context_tokens} reached the warning level {warn}.",
                     {**evidence, "warn": warn, "cap": cap})
        else:
            self.add("session_context", "step", ALERT, PASS,
                     f"Context {context_tokens} is below the warning level.",
                     {**evidence, "warn": warn, "cap": cap})

        max_turns = limits.get("max_turns")
        if turns is None or not max_turns:
            self.add("session_turns", "step", ALERT, UNKNOWN,
                     "The turn limit was not checked.", evidence)
        elif turns > max_turns:
            self.add("session_turns", "step", ALERT, FAIL,
                     f"{turns} turns exceeded the limit {max_turns}.",
                     {**evidence, "max_turns": max_turns})
        else:
            self.add("session_turns", "step", ALERT, PASS,
                     f"{turns} turns are within the limit {max_turns}.",
                     {**evidence, "max_turns": max_turns})

        timeout = limits.get("session_timeout")
        if age is None or not timeout:
            self.add("session_age", "step", ALERT, UNKNOWN,
                     "The session age limit was not checked.", evidence)
        elif age > timeout:
            self.add("session_age", "step", ALERT, FAIL,
                     f"The session age {age:.0f}s exceeds the limit {timeout}s.",
                     {**evidence, "timeout": timeout})
        else:
            self.add("session_age", "step", ALERT, PASS,
                     f"The session age {age:.0f}s is within the limit {timeout}s.",
                     {**evidence, "timeout": timeout})

    def session_end(self, step, success, reason, session_id, log_path):
        """Record the result of one session."""
        self.add("session_result", "step", ALERT, _state(bool(success)),
                 "The session completed." if success else f"The session failed: {reason}.",
                 {"step": step, "session": session_id, "log": str(log_path) if log_path else None})

    # -- phases and issues ---------------------------------------------

    def phase_start(self, name, issue=None, step=None, remaining_minutes=None):
        self.phase = name
        self.context.update({"issue": issue, "step": step})
        if remaining_minutes is not None:
            self.budget["remaining_minutes"] = round(remaining_minutes, 1)
        self.event("phase_start", name=name, issue=issue, step=step,
                   remaining_minutes=self.budget.get("remaining_minutes"))

    def phase_end(self, name, issue=None, step=None, state=None, remaining_minutes=None):
        self.phase = name
        if remaining_minutes is not None:
            self.budget["remaining_minutes"] = round(remaining_minutes, 1)
        self.event("phase_end", name=name, issue=issue, step=step,
                   remaining_minutes=self.budget.get("remaining_minutes"))
        pr = (state or {}).get("pr") or {}
        if pr.get("url") and pr.get("is_draft"):
            self.add("draft_at_boundary", name, ALERT, FAIL,
                     f"The draft PR {pr['url']} remains at the phase boundary.",
                     {"issue": (state or {}).get("issue") or issue, "step": step,
                      "pr": pr.get("url"), "head": pr.get("head")})

    def after_step(self, step, state, success=None, info=None, published=None, worktree=None):
        """Record the checks that follow one session."""
        state = state or {}
        pr = state.get("pr") or {}
        published = published if isinstance(published, dict) else {}
        url = pr.get("url") or published.get("url")
        head = pr.get("head") or published.get("head")
        issue = state.get("issue") or state.get("url")
        self.context.update({"issue": issue, "step": step, "head": head,
                             "ci": state.get("ci")})

        evidence = {"issue": issue, "step": step, "pr": url, "head": head,
                    "success": success, "info": info}

        if step in ("implement-issue", "address-pr-review"):
            self.add("published", "post-step", ALERT, _state(bool(url)),
                     "Committed work has a pull request." if url else "No pull request is visible after the step.",
                     evidence)
        elif url:
            self.add("published", "post-step", ALERT, PASS,
                     "The pull request is visible.", evidence)
        else:
            self.add("published", "post-step", ALERT, SKIP,
                     "No pull request applies to this step.", evidence)

        if not url:
            return

        ci = str(state.get("ci") or "").lower()
        checks = state.get("checks") or []
        missing = [check.get("name") for check in checks if check.get("state") == "missing"]
        if ci == "missing" or missing:
            self.add("checks", "post-step", ALERT, FAIL,
                     f"Required checks have no run at {head}.",
                     {**evidence, "ci": ci, "missing": [name for name in missing if name]})
        elif ci in ("failing", "failed", "error"):
            self.add("checks", "post-step", ALERT, FAIL,
                     f"CI is {ci} at {head}.", {**evidence, "ci": ci})
        elif ci in ("pending", "incomplete", ""):
            self.add("checks", "post-step", ALERT, UNKNOWN,
                     f"CI is {ci or 'unread'} at {head}.", {**evidence, "ci": ci})
        elif ci in ("green", "passed", "none"):
            self.add("checks", "post-step", ALERT, PASS,
                     f"CI is {ci} at {head}.", {**evidence, "ci": ci})
        else:
            self.add("checks", "post-step", ALERT, UNKNOWN,
                     f"CI is {ci}.", {**evidence, "ci": ci})

        verdicts = state.get("review_verdicts") or []
        reviews = state.get("reviews") or []
        head_verdict = next((entry for entry in reversed(verdicts)
                             if entry.get("head") == head), None)
        head_review = any(review.get("covers_head") or review.get("commit") == head
                          for review in reviews)
        review_state = PASS if (head_verdict or head_review) else (
            FAIL if step == "review-changes" else UNKNOWN)
        message = ("A review covers the current head." if review_state == PASS else
                   "No review covers the current head.")
        self.add("review", "post-step", ALERT, review_state, message,
                 {**evidence, "verdict": (head_verdict or {}).get("verdict"),
                  "reviews": len(reviews)})
        self.context["review"] = (head_verdict or {}).get("verdict") or (
            "review" if head_review else "none")

        if worktree is not None:
            dirty = worktree.get("dirty")
            if dirty is None:
                self.add("worktree", "post-step", ALERT, UNKNOWN,
                         "The worktree state is unknown.",
                         {**evidence, "path": worktree.get("path")})
            elif dirty:
                self.add("worktree", "post-step", ALERT, FAIL,
                         f"The worktree has {dirty} uncommitted path(s).",
                         {**evidence, "path": worktree.get("path"), "dirty": dirty})
            else:
                self.add("worktree", "post-step", ALERT, PASS,
                         "The worktree is clean.",
                         {**evidence, "path": worktree.get("path")})

    # -- final ---------------------------------------------------------

    def finish(self, records=None, selection=None, states=None, toil=None,
               phase_throughput=None, budget=None):
        """Record the phase and final checks, counts, and budget."""
        if self._finished:
            return
        self._finished = True
        self.phase = "final"
        records = list(records or [])
        selection = list(selection or [])
        states = list(states or [])
        if budget:
            self.budget.update(budget)

        record_numbers = {_issue_number(record.get("issue")) for record in records}
        record_numbers.discard(None)
        self.processed_numbers = set(record_numbers)
        selected_numbers = _numbers(selection)
        state_by_number = {_issue_number(state.get("issue") or state.get("number")): state
                           for state in states}
        missing = [number for number in selected_numbers if number not in record_numbers]
        for number in missing:
            state = state_by_number.get(number) or {}
            started = state.get("started", True)
            name = "issue_record" if started else "issue_not_started"
            self.add(name, "final", ALERT, FAIL,
                     (f"Selected issue #{number} has no endpoint record." if started
                      else f"Selected issue #{number} was not started."),
                     {"issue": number})

        counts = {"selected": len(selected_numbers), "open": 0, "merged": 0,
                  "parked": 0, "draft": 0, "done": 0, "not_started": 0}
        endpoints = {_issue_number(record.get("issue")): record.get("endpoint")
                     for record in records}
        for number, endpoint in endpoints.items():
            if endpoint in ("DONE", "merged"):
                counts["done"] += 1
            elif endpoint in ("parked", "time-park", "park-failed"):
                counts["parked"] += 1
        for state in states:
            pr = state.get("pr") or {}
            number = _issue_number(state.get("issue") or state.get("number"))
            endpoint = endpoints.get(number)
            if not pr.get("url"):
                if state.get("started") is False or endpoint in (None, "not-started"):
                    counts["not_started"] += 1
                continue
            if pr.get("state") == "MERGED":
                counts["merged"] += 1
            elif pr.get("is_draft"):
                counts["draft"] += 1
            elif pr.get("state", "OPEN") == "OPEN":
                counts["open"] += 1
        self.counts = counts

        if phase_throughput and len(phase_throughput) >= 2:
            first = phase_throughput[0]
            last = phase_throughput[-1]
            try:
                early = float(first.get("hours_per_done"))
                late = float(last.get("hours_per_done"))
            except (TypeError, ValueError):
                early = late = None
            if early is not None and late is not None:
                evidence = {"early": early, "late": late,
                            "early_phase": first.get("name"), "late_phase": last.get("name")}
                if late > early * 1.5 and late - early >= 0.25:
                    self.add("throughput", "final", ALERT, FAIL,
                             f"Hours per done issue rose from {early:.2f} to {late:.2f}.", evidence)
                else:
                    self.add("throughput", "final", ALERT, PASS,
                             f"Hours per done issue stayed near {early:.2f} (last {late:.2f}).", evidence)

        if toil is not None:
            patterns = toil.get("patterns") if isinstance(toil, dict) else toil
            count = len(patterns or [])
            self.add("toil", "final", INFO, PASS if count == 0 else FAIL,
                     "The toil audit found no pattern at Strike 3." if count == 0
                     else f"The toil audit found {count} pattern(s) at Strike 3.",
                     {"patterns": count})

        self.add("budget", "final", INFO, PASS if self.budget else UNKNOWN,
                 "The phase budget is recorded." if self.budget else "The phase budget was not recorded.",
                 self.budget)

    def summary_coverage(self, rows):
        """Record whether the queue summary names every processed issue."""
        if rows is None:
            self.add("summary_coverage", "final", ALERT, SKIP,
                     "The queue summary was not read.")
            return
        shown = {_issue_number(row.get("issue")) for row in rows
                 if isinstance(row, dict) and row.get("issue")}
        shown.discard(None)
        missing = sorted(number for number in self.processed_numbers if number not in shown)
        if missing:
            self.add("summary_coverage", "final", ALERT, FAIL,
                     f"The run summary omits {', '.join(f'#{number}' for number in missing)}.",
                     {"missing": missing, "rows": sorted(shown)})
        else:
            self.add("summary_coverage", "final", ALERT, PASS,
                     "The run summary names every processed issue.",
                     {"rows": sorted(shown)})

    # -- report --------------------------------------------------------

    def status_line(self):
        counts = self.counts
        parts = [f"phase={self.phase}",
                 f"issue={self.context.get('issue') or '-'}",
                 f"step={self.context.get('step') or '-'}",
                 f"head={(self.context.get('head') or '-')[:7] if self.context.get('head') else '-'}",
                 f"ci={self.context.get('ci') or '-'}",
                 f"review={self.context.get('review') or '-'}",
                 f"alerts={len(self.alerts())}"]
        if self.stopped:
            parts.append(f"stop={self.stopped}")
        if self.budget.get("remaining_minutes") is not None:
            parts.append(f"remaining={self.budget['remaining_minutes']}m")
        if counts:
            parts.append("counts=" + ",".join(f"{key}:{value}" for key, value in counts.items()))
        return "Monitor: " + " ".join(parts)

    def snapshot(self):
        alerts = self.alerts()
        return {
            "schema": SCHEMA,
            "started": _iso(self.started),
            "updated": _now(self.clock),
            "phase": self.phase,
            "issue": self.context.get("issue"),
            "step": self.context.get("step"),
            "head": self.context.get("head"),
            "ci": self.context.get("ci"),
            "review": self.context.get("review"),
            "remaining_minutes": self.budget.get("remaining_minutes"),
            "stopped": self.stopped,
            "counts": self.counts,
            "budget": self.budget,
            "alerts": alerts,
            "checks": self.checks,
            "events": self.events,
            "reports": {
                "json": str(self.notes_dir / JSON_NAME),
                "markdown": str(self.notes_dir / MARKDOWN_NAME),
            },
        }

    def render_markdown(self):
        snapshot = self.snapshot()
        lines = ["# Monitor", "",
                 f"Phase: `{snapshot['phase']}`  ",
                 f"Alerts: {len(snapshot['alerts'])}  ",
                 f"Stopped: {snapshot['stopped'] or 'no'}"]
        if snapshot["budget"]:
            lines.append(f"Budget: `{json.dumps(snapshot['budget'], sort_keys=True)}`")
        lines.append("")
        if snapshot["alerts"]:
            lines += ["## Alerts", ""]
            for alert in snapshot["alerts"]:
                lines.append(f"- **{alert['name']}** ({alert['phase']}, {alert['level']}): {alert['message']}")
                if alert["evidence"]:
                    lines.append(f"  Evidence: `{json.dumps(alert['evidence'], sort_keys=True)}`")
            lines.append("")
        lines += ["## Checks", ""]
        phases = []
        for check in self.checks:
            if check["phase"] not in phases:
                phases.append(check["phase"])
        for phase in phases:
            lines += [f"### {phase}", ""]
            for check in self.checks:
                if check["phase"] != phase:
                    continue
                lines.append(f"- {check['state'].upper()} **{check['name']}** ({check['level']}): {check['message']}")
                if check["evidence"]:
                    lines.append(f"  Evidence: `{json.dumps(check['evidence'], sort_keys=True)}`")
            lines.append("")
        if self.events:
            lines += ["## Phases", ""]
            for event in self.events:
                fields = {key: value for key, value in event.items()
                          if key not in ("event", "at") and value is not None}
                lines.append(f"- {event['at']} `{event['event']}` `{json.dumps(fields, sort_keys=True)}`")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write(self, force=False):
        """Write both report files, at most once a second unless forced."""
        if not self._write_enabled:
            return None
        now = self.clock()
        if not force and now - self._last_write < 1:
            return None
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        (self.notes_dir / JSON_NAME).write_text(
            json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        (self.notes_dir / MARKDOWN_NAME).write_text(self.render_markdown(), encoding="utf-8")
        self._last_write = now
        return str(self.notes_dir / JSON_NAME)


def replay(observations):
    """Run an observation fixture through the same checks as a live run.

    The fixture records what the runner observed. It does not call GitHub.
    """
    observations = observations or {}
    monitor = Monitor(Path("."), write=False)
    preflight = observations.get("preflight") or {}
    monitor.preflight(
        facts=preflight.get("facts") or {},
        identity=preflight.get("identity"),
        exec_login=preflight.get("exec_login"),
        lock=preflight.get("lock"),
        model=preflight.get("model"),
        model_available=preflight.get("model_available"),
        endpoint_configured=preflight.get("endpoint_configured"),
        endpoint_ok=preflight.get("endpoint_ok"),
    )
    monitor.selection(observations.get("selection"),
                      required_labels=observations.get("required_labels"),
                      exclude_labels=observations.get("exclude_labels"))
    for issue in observations.get("issues") or []:
        number = issue.get("number")
        url = issue.get("url") or (f"https://github.com/o/r/issues/{number}" if number else None)
        step = issue.get("step") or "implement-issue"
        monitor.phase_start("issue", issue=url, step=step)
        if issue.get("started", True):
            state = {
                "issue": url,
                "number": number,
                "labels": issue.get("labels") or [],
                "pr": issue.get("pr") or {},
                "ci": issue.get("ci"),
                "checks": issue.get("checks") or [],
                "review_verdicts": issue.get("review_verdicts") or [],
                "reviews": issue.get("reviews") or [],
            }
            monitor.after_step(step, state, success=issue.get("success", True),
                               published=issue.get("pr"),
                               worktree={"dirty": issue.get("worktree_dirty")})
        if issue.get("phase_end"):
            state = issue.get("state") or {
                "issue": url, "number": number, "pr": issue.get("pr") or {},
            }
            monitor.phase_end("issue", issue=url, step=step, state=state)
    monitor.finish(records=observations.get("records"),
                   selection=observations.get("selection"),
                   states=observations.get("states"),
                   toil=observations.get("toil"),
                   phase_throughput=observations.get("phase_throughput"),
                   budget=observations.get("budget"))
    monitor.summary_coverage(observations.get("summary_rows"))
    return monitor.snapshot()
