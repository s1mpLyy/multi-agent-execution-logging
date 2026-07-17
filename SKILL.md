---
name: agent-execution-logging
description: Use when multiple AI agents (Codex, Cursor, Claude Code, Claude CLI, or others) edit the same repository and code changes need a consistent, auditable trail — or before finishing any file-editing task in a repo that already keeps AI execution logs.
---

# Agent Execution Logging

Use this skill when the user wants every AI agent that edits a repository to
leave a clear, repeatable execution trail.

## What This Skill Solves

- Multiple AI tools touch the same repo
- Different model variants need a shared logging contract
- Teams want one central AI change log plus optional per-agent logs
- New agent or model identities should be added without hand-editing multiple
  instruction files every time

## When NOT to Use

- Read-only exploration, questions, or reviews that change no files
- Repos with an existing, enforced changelog/ADR process that already covers
  AI changes — extend that instead of layering a second system
- Single-developer scratch repos where no audit trail is wanted

## Default Layout

If the repo does not already define a logging structure, use:

- Central log: `docs/code-base-ai-update-logs.md`
- Agent registry: `docs/agent-execution-registry.md`
- Per-agent logs: `docs/agent-logs/<agent-id>.md`

If the repo already has an equivalent structure, follow the repo's existing
contract instead of forcing these defaults.

## Workflow

### 1. Discover the repo contract

Read the instruction surface first:

- `AGENTS.md`
- `AGENT.md`
- `CLAUDE.md`
- Cursor rule files under `.cursor/rules/`

Resolve:

- whether a central log already exists
- whether per-agent logs are enabled
- whether the repo already names specific agent or model files

### 2. Resolve the current agent identity

Prefer, in this order:

1. User-provided agent label
2. Repo-defined label
3. Tool family plus model name
4. Safe fallback slug

Stable examples (match what `register_agent_log.py` emits when both
`--tool-family` and `--model` are passed):

- `cursor-composer-2-0`
- `claude-code-opus-4-7`
- `codex-gpt-5-4`

### 3. Bootstrap the repo if needed

If the repo has no central log or registry yet, run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/bootstrap_logging_structure.py --root .
```

That creates the default `docs/` logging structure. It does not rewrite the
repo's instruction files for you; use the integration snippets in
`${CLAUDE_PLUGIN_ROOT:-.}/references/integration-snippets.md` for that one-time
setup.

### 4. Register new agents when needed

If the repo uses per-agent logs and the current agent is missing from the
registry, run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/register_agent_log.py \
  --root . \
  --agent-label "Claude Opus 4.7" \
  --tool-family "Claude Code" \
  --model "Opus 4.7"
```

This creates the per-agent file and adds the registry row.

### 5. Log before closing any write task

For any task that edits files, append a dated entry. Use the helper so the
format and date are consistent:

```bash
python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/add_log_entry.py \
  --root . \
  --title "Short title" \
  --summary "1-3 sentences on what changed." \
  --file "path/to/file::what changed" \
  --file "path/to/other::what changed" \
  --agent-id claude-code-opus-4-7
```

- The central entry is always written.
- Pass `--agent-id` only if the repo uses per-agent logs; it appends a matching
  entry to that agent's file (the agent must already be registered).
- Also update instruction or plan docs that would otherwise become misleading.

Read-only exploration does not require log entries.

## Handling Concurrent Writes

The central log is a single append-only file, so two agents working in
parallel branches will both append and hit a merge conflict.

- **Never delete another agent's entry to resolve a conflict.** Keep both.
- When resolving a conflict by hand, keep entries oldest-first within a date,
  with newest dates at the bottom. `add_log_entry.py` only appends in the order
  entries are added — it does not sort by `--date`, so a back-dated entry lands
  at the end until you move it.
- If two entries collide on the same task, merge them into one entry rather
  than dropping either side.
- Append entries as the *last* action before finishing, so the conflict window
  stays small.

## Central Log Format

Use the repo's existing format when present. Otherwise use:

```md
## YYYY-MM-DD — Short Title

**What changed:** 1-3 short sentences.

**Files touched:**
- `path/to/file` — what changed
- `path/to/other` — what changed

**Follow-ups:** optional
```

## Per-Agent Log Format

Use:

```md
## YYYY-MM-DD — Short Title

**Task:** 1-2 short sentences.

**Files touched:**
- `path/to/file` — what changed

**Central log:** `docs/code-base-ai-update-logs.md`

**Notes:** optional
```

## Resources

- Read `${CLAUDE_PLUGIN_ROOT:-.}/references/integration-snippets.md` for
  AGENTS/CLAUDE/Cursor setup text.
- Run `${CLAUDE_PLUGIN_ROOT:-.}/scripts/bootstrap_logging_structure.py` to
  scaffold the default docs layout in a repo.
- Run `${CLAUDE_PLUGIN_ROOT:-.}/scripts/register_agent_log.py` to add a new
  per-agent log file and registry entry.
- Run `${CLAUDE_PLUGIN_ROOT:-.}/scripts/add_log_entry.py` to append a
  consistently formatted entry to the central (and per-agent) log.

## Common Mistakes

- Logging only in the per-agent file and skipping the central log. The central
  log is the one source humans scan — it is never optional.
- Writing one entry per file instead of one entry per task.
- Vague entries ("updated code"). Name the files and what changed in each.
- Adding a new model to `CLAUDE.md` and `AGENTS.md` separately instead of
  registering it once.
- Logging read-only exploration. Only file-editing tasks need entries.

## Guardrails

- Never treat logging as optional for code edits.
- Never replace the central log with per-agent files.
- Never keep a manual list of model files in multiple instruction documents if
  a single registry file can own that mapping.
- Keep entries short, concrete, and file-referenced.
