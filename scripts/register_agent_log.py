#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import REGISTRY_TEMPLATE


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "unknown-agent"


def build_log_file_content(
    agent_label: str,
    agent_id: str,
    tool_family: str,
    model: str,
    notes: str,
    today: str,
) -> str:
    return (
        f"# {agent_label}\n\n"
        "Per-agent execution log for this repo. This complements, and does not\n"
        "replace, `docs/code-base-ai-update-logs.md`.\n\n"
        "## Agent Profile\n\n"
        f"- Agent label: `{agent_label}`\n"
        f"- Agent id: `{agent_id}`\n"
        f"- Tool family: `{tool_family or 'unspecified'}`\n"
        f"- Model: `{model or 'unspecified'}`\n"
        f"- Registered: `{today}`\n"
        f"- Notes: `{notes or 'none'}`\n\n"
        "## Entry Template\n\n"
        "```md\n"
        "## YYYY-MM-DD — Short Title\n\n"
        "**Task:** 1-2 short sentences.\n\n"
        "**Files touched:**\n"
        "- `path/to/file` — what changed\n\n"
        "**Central log:** `docs/code-base-ai-update-logs.md`\n\n"
        "**Notes:** optional\n"
        "```\n"
    )


def id_already_registered(content: str, agent_id: str) -> bool:
    """True if agent_id already appears in the registry's ID column.

    Matches the canonical ID column only, so an id that happens to appear in
    another column (e.g. a Notes reference) cannot cause a false "already
    registered" that would skip adding the real row.
    """
    target = f"`{agent_id}`"
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        # Registry columns: Agent | ID | Log file | Notes
        if len(cells) >= 2 and cells[1] == target:
            return True
    return False


def ensure_registry_row(
    registry_path: Path,
    agent_label: str,
    agent_id: str,
    log_file_relative_to_docs: str,
    notes: str,
) -> None:
    if not registry_path.exists():
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(REGISTRY_TEMPLATE, encoding="utf-8")

    content = registry_path.read_text(encoding="utf-8")
    if id_already_registered(content, agent_id):
        return

    row = (
        f"| {agent_label} | `{agent_id}` | "
        f"[{log_file_relative_to_docs}](./{log_file_relative_to_docs}) | "
        f"{notes or 'Registered agent log'} |\n"
    )
    if not content.endswith("\n"):
        content += "\n"
    registry_path.write_text(content + row, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register a per-agent execution log for a repo."
    )
    parser.add_argument("--root", default=".", help="Repo root. Defaults to cwd.")
    parser.add_argument("--registry", default="docs/agent-execution-registry.md")
    parser.add_argument("--log-dir", default="docs/agent-logs")
    parser.add_argument("--agent-label", required=True)
    parser.add_argument("--agent-id")
    parser.add_argument("--tool-family", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    registry_path = root / args.registry
    log_dir = root / args.log_dir
    agent_id = args.agent_id or slugify(
        " ".join(part for part in [args.tool_family, args.model] if part).strip()
        or args.agent_label
    )

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{agent_id}.md"
    today = datetime.now(timezone.utc).date().isoformat()

    if not log_path.exists():
        log_path.write_text(
            encoding="utf-8",
            data=build_log_file_content(
                agent_label=args.agent_label,
                agent_id=agent_id,
                tool_family=args.tool_family,
                model=args.model,
                notes=args.notes,
                today=today,
            )
        )

    log_file_relative_to_docs = f"agent-logs/{log_path.name}"
    ensure_registry_row(
        registry_path=registry_path,
        agent_label=args.agent_label,
        agent_id=agent_id,
        log_file_relative_to_docs=log_file_relative_to_docs,
        notes=args.notes,
    )

    print(f"registered={agent_id}")
    print(f"registry={registry_path}")
    print(f"log_file={log_path}")


if __name__ == "__main__":
    main()
