# Agent Ledger

> Consistent AI execution logs across every agent — Claude Code, Codex, Cursor,
> and anything else that edits your repo.

[![npm](https://img.shields.io/npm/v/agent-execution-logging.svg)](https://www.npmjs.com/package/agent-execution-logging)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

The problem: multiple AI tools touch the same repo, each with its own idea of
what "leaving a trail" means. This skill fixes that with one shared contract:

- **One mandatory central AI change log** — every agent appends to the same file
- **Optional per-agent logs** — for teams that want a paper trail per model
- **A registry** — new agent/model identities get added in one place, not
  scattered across `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, etc.
- **A log-entry helper** — append correctly-formatted, dated entries instead
  of hand-editing markdown

## Install

Pick whichever matches your environment — all three install paths use the same
underlying skill.

### Claude Code (plugin marketplace)

```bash
/plugin marketplace add s1mpLyy/agent-ledger
/plugin install agent-execution-logging@agent-ledger
```

### Any agent (npx — no install required)

```bash
npx agent-execution-logging bootstrap --root .
npx agent-execution-logging register \
  --agent-label "Claude Opus 4.7" \
  --tool-family "Claude Code" \
  --model "Opus 4.7"
npx agent-execution-logging snippets
```

Requires Node ≥ 16 and Python 3.

### Codex

Place this repo at `$CODEX_HOME/skills/agent-execution-logging` or
`~/.codex/skills/agent-execution-logging`. Codex picks it up from
[`agents/openai.yaml`](./agents/openai.yaml).

### Cursor / generic

Copy the snippets from
[`references/integration-snippets.md`](./references/integration-snippets.md)
into `.cursor/rules/` or any instruction file your agent reads.

## What You Get

| File | Purpose |
| --- | --- |
| [`SKILL.md`](./SKILL.md) | Skill definition (frontmatter + workflow) |
| [`skills/agent-execution-logging/SKILL.md`](./skills/agent-execution-logging/SKILL.md) | Claude Code plugin copy — kept byte-identical to `SKILL.md` (CI-checked) |
| [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) | Claude Code marketplace manifest |
| [`agents/openai.yaml`](./agents/openai.yaml) | Codex skill metadata |
| [`scripts/bootstrap_logging_structure.py`](./scripts/bootstrap_logging_structure.py) | Scaffolds the default `docs/` layout |
| [`scripts/register_agent_log.py`](./scripts/register_agent_log.py) | Registers a new agent/model |
| [`scripts/add_log_entry.py`](./scripts/add_log_entry.py) | Appends a formatted entry to the central/per-agent log |
| [`references/integration-snippets.md`](./references/integration-snippets.md) | Paste-ready rules for AGENTS / CLAUDE / Cursor |
| [`bin/cli.js`](./bin/cli.js) | Universal Node CLI wrapper |

## Default Logging Structure

```text
docs/
  code-base-ai-update-logs.md     # central log (mandatory)
  agent-execution-registry.md      # registry of all known agents
  agent-logs/
    <agent-id>.md                  # optional per-agent logs
```

If the repo already has an equivalent structure, the skill follows that instead
of forcing these defaults.

## Quick Start

```bash
# 1. Bootstrap the logging structure in your repo
npx agent-execution-logging bootstrap --root .

# 2. Register each agent/model that will touch the repo
npx agent-execution-logging register \
  --agent-label "Claude Opus 4.7" \
  --tool-family "Claude Code" \
  --model "Opus 4.7"

# 3. Paste the instruction snippets into AGENTS.md / CLAUDE.md / .cursor/rules/
npx agent-execution-logging snippets

# 4. Append a log entry at the end of any task that edits files
npx agent-execution-logging entry \
  --title "Fix login redirect" \
  --summary "Corrected the post-login redirect target." \
  --file "src/auth.py::fixed redirect URL" \
  --agent-id claude-code-opus-4-7
```

From that point on, every AI agent that edits code appends to
`docs/code-base-ai-update-logs.md` before finishing a task.

## Log Formats

### Central log entry

```md
## YYYY-MM-DD — Short Title

**What changed:** 1-3 short sentences.

**Files touched:**
- `path/to/file` — what changed

**Follow-ups:** optional
```

### Per-agent log entry

```md
## YYYY-MM-DD — Short Title

**Task:** 1-2 short sentences.

**Files touched:**
- `path/to/file` — what changed

**Central log:** `docs/code-base-ai-update-logs.md`

**Notes:** optional
```

## How Agent IDs Are Generated

When you register with `--tool-family` and `--model`, the script produces a
slug like:

- `claude-code-opus-4-7`
- `cursor-composer-2-0`
- `codex-gpt-5-4`

You can override with `--agent-id` if you want a specific slug. The ID shows
up in the registry row and is the filename under `docs/agent-logs/`.

## Design Notes

- The central log is **mandatory** even when per-agent logs are optional — it's
  the one source of truth humans scan.
- The registry exists to avoid maintaining duplicated model lists across
  `CLAUDE.md`, `AGENTS.md`, Cursor rules, etc. Add a model once, reference it
  everywhere.
- `bootstrap_logging_structure.py` and `register_agent_log.py` are
  **idempotent** — safe to re-run after a bad edit. `add_log_entry.py` is
  intentionally **append-only**: run it once per task, since re-running adds a
  duplicate entry rather than being a no-op.

## Development

```bash
python3 -m pytest -q      # run tests
claude plugin validate .  # validate marketplace manifest
npm pack --dry-run        # preview the npm package
```

## License

[MIT](./LICENSE)
