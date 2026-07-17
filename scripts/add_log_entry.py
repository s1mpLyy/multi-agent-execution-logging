#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path


def parse_file(spec: str) -> tuple[str, str]:
    path, sep, desc = spec.partition("::")
    path = path.strip()
    desc = desc.strip() if sep else ""
    return path, desc or "updated"


def files_block(specs: list[str]) -> str:
    lines = ["**Files touched:**"]
    for spec in specs:
        path, desc = parse_file(spec)
        lines.append(f"- `{path}` — {desc}")
    return "\n".join(lines)


def central_entry(date_str: str, title: str, summary: str,
                  files: list[str], follow_ups: str) -> str:
    parts = [
        f"## {date_str} — {title}",
        "",
        f"**What changed:** {summary}",
        "",
        files_block(files),
    ]
    if follow_ups:
        parts += ["", f"**Follow-ups:** {follow_ups}"]
    return "\n".join(parts) + "\n"


def agent_entry(date_str: str, title: str, summary: str, files: list[str],
                central: str, notes: str) -> str:
    parts = [
        f"## {date_str} — {title}",
        "",
        f"**Task:** {summary}",
        "",
        files_block(files),
        "",
        f"**Central log:** `{central}`",
    ]
    if notes:
        parts += ["", f"**Notes:** {notes}"]
    return "\n".join(parts) + "\n"


def append_entry(path: Path, entry: str) -> None:
    existing = path.read_text(encoding="utf-8")
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + "\n" + entry, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Append a dated entry to the central AI change log "
        "(and an optional per-agent log)."
    )
    parser.add_argument("--root", default=".", help="Repo root. Defaults to cwd.")
    parser.add_argument("--central", default="docs/code-base-ai-update-logs.md")
    parser.add_argument("--log-dir", default="docs/agent-logs")
    parser.add_argument("--title", required=True, help="Short entry title.")
    parser.add_argument("--summary", required=True,
                        help="1-3 sentences on what changed.")
    parser.add_argument("--file", dest="files", action="append", required=True,
                        metavar="PATH[::DESCRIPTION]",
                        help="Touched file; repeatable. Description after '::'.")
    parser.add_argument("--follow-ups", default="")
    parser.add_argument("--notes", default="", help="Per-agent log note.")
    parser.add_argument("--agent-id", default="",
                        help="If set, also append to that per-agent log.")
    parser.add_argument("--date", default=date.today().isoformat(),
                        help="Entry date (YYYY-MM-DD). Defaults to today.")
    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        sys.exit(f"Invalid --date {args.date!r}; expected YYYY-MM-DD.")

    for spec in args.files:
        if not parse_file(spec)[0]:
            sys.exit(f"Empty file path in --file spec: {spec!r}")

    root = Path(args.root).resolve()
    central_path = root / args.central
    if not central_path.exists():
        sys.exit(
            f"Central log not found at {central_path}. "
            "Run bootstrap_logging_structure.py first."
        )

    append_entry(
        central_path,
        central_entry(args.date, args.title, args.summary,
                      args.files, args.follow_ups),
    )
    print(f"central_entry_appended={central_path}")

    if args.agent_id:
        agent_path = root / args.log_dir / f"{args.agent_id}.md"
        if not agent_path.exists():
            sys.exit(
                f"Per-agent log for '{args.agent_id}' not found at "
                f"{agent_path}. Run register_agent_log.py first."
            )
        append_entry(
            agent_path,
            agent_entry(args.date, args.title, args.summary,
                        args.files, args.central, args.notes),
        )
        print(f"agent_entry_appended={agent_path}")


if __name__ == "__main__":
    main()
