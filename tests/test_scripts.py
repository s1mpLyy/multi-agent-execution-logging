from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO / "scripts" / "bootstrap_logging_structure.py"
REGISTER = REPO / "scripts" / "register_agent_log.py"
ADD_ENTRY = REPO / "scripts" / "add_log_entry.py"

sys.path.insert(0, str(REPO / "scripts"))
from register_agent_log import slugify  # noqa: E402


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def run_nocheck(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_bootstrap_creates_structure(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    assert (tmp_path / "docs" / "code-base-ai-update-logs.md").exists()
    assert (tmp_path / "docs" / "agent-execution-registry.md").exists()
    assert (tmp_path / "docs" / "agent-logs").is_dir()


def test_bootstrap_is_idempotent(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    central = tmp_path / "docs" / "code-base-ai-update-logs.md"
    central.write_text("custom content")
    run(BOOTSTRAP, "--root", str(tmp_path))
    assert central.read_text() == "custom content"


def test_register_produces_expected_id(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    result = run(
        REGISTER,
        "--root", str(tmp_path),
        "--agent-label", "Claude Opus 4.7",
        "--tool-family", "Claude Code",
        "--model", "Opus 4.7",
    )
    assert "registered=claude-code-opus-4-7" in result.stdout
    log = tmp_path / "docs" / "agent-logs" / "claude-code-opus-4-7.md"
    assert log.exists()


def test_register_is_idempotent(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    args = [
        "--root", str(tmp_path),
        "--agent-label", "Claude Opus 4.7",
        "--tool-family", "Claude Code",
        "--model", "Opus 4.7",
    ]
    run(REGISTER, *args)
    run(REGISTER, *args)
    registry = (tmp_path / "docs" / "agent-execution-registry.md").read_text()
    assert registry.count("`claude-code-opus-4-7`") == 1


def test_register_label_drift_no_duplicate(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    run(
        REGISTER,
        "--root", str(tmp_path),
        "--agent-label", "Claude Opus 4.7",
        "--agent-id", "claude-code-opus-4-7",
    )
    run(
        REGISTER,
        "--root", str(tmp_path),
        "--agent-label", "Claude Opus 4.7 ",
        "--agent-id", "claude-code-opus-4-7",
    )
    registry = (tmp_path / "docs" / "agent-execution-registry.md").read_text()
    assert registry.count("`claude-code-opus-4-7`") == 1


def test_slugify_edge_cases() -> None:
    assert slugify("") == "unknown-agent"
    assert slugify("   ") == "unknown-agent"
    assert slugify("Claude Code") == "claude-code"
    assert slugify("  Claude   Code!!  ") == "claude-code"
    assert slugify("GPT-5.4") == "gpt-5-4"


def test_add_entry_appends_central(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    run(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "Fix login redirect",
        "--summary", "Corrected the post-login redirect target.",
        "--file", "src/auth.py::fixed redirect URL",
        "--date", "2026-05-17",
    )
    central = (tmp_path / "docs" / "code-base-ai-update-logs.md").read_text()
    assert "## 2026-05-17 — Fix login redirect" in central
    assert "**What changed:** Corrected the post-login redirect target." in central
    assert "- `src/auth.py` — fixed redirect URL" in central


def test_add_entry_requires_central(tmp_path: Path) -> None:
    result = run_nocheck(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "T",
        "--summary", "S",
        "--file", "a.py",
    )
    assert result.returncode != 0
    assert "bootstrap" in result.stderr.lower()


def test_add_entry_appends_per_agent(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    run(
        REGISTER,
        "--root", str(tmp_path),
        "--agent-label", "Claude Opus 4.7",
        "--tool-family", "Claude Code",
        "--model", "Opus 4.7",
    )
    run(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "Add tests",
        "--summary", "Added coverage for the parser.",
        "--file", "tests/test_parser.py",
        "--agent-id", "claude-code-opus-4-7",
        "--date", "2026-05-17",
    )
    agent_log = (
        tmp_path / "docs" / "agent-logs" / "claude-code-opus-4-7.md"
    ).read_text()
    assert "## 2026-05-17 — Add tests" in agent_log
    assert "**Task:** Added coverage for the parser." in agent_log
    central = (tmp_path / "docs" / "code-base-ai-update-logs.md").read_text()
    assert "## 2026-05-17 — Add tests" in central


def test_add_entry_unknown_agent_errors(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    result = run_nocheck(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "T",
        "--summary", "S",
        "--file", "a.py",
        "--agent-id", "ghost-agent",
    )
    assert result.returncode != 0
    assert "ghost-agent" in result.stderr
    assert "register" in result.stderr.lower()


def test_add_entry_default_description(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    run(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "T",
        "--summary", "S",
        "--file", "a.py",
        "--date", "2026-05-17",
    )
    central = (tmp_path / "docs" / "code-base-ai-update-logs.md").read_text()
    assert "- `a.py` — updated" in central


def test_add_entry_follow_ups_and_notes(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    run(
        REGISTER,
        "--root", str(tmp_path),
        "--agent-label", "Claude Opus 4.7",
        "--tool-family", "Claude Code",
        "--model", "Opus 4.7",
    )
    run(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "T",
        "--summary", "S",
        "--file", "a.py::changed::twice",
        "--follow-ups", "ship the migration",
        "--notes", "ran locally",
        "--agent-id", "claude-code-opus-4-7",
        "--date", "2026-05-17",
    )
    central = (tmp_path / "docs" / "code-base-ai-update-logs.md").read_text()
    assert "**Follow-ups:** ship the migration" in central
    assert "- `a.py` — changed::twice" in central
    agent_log = (
        tmp_path / "docs" / "agent-logs" / "claude-code-opus-4-7.md"
    ).read_text()
    assert "**Notes:** ran locally" in agent_log


def test_skill_md_files_in_sync() -> None:
    root_skill = (REPO / "SKILL.md").read_text()
    plugin_skill = (
        REPO / "skills" / "agent-execution-logging" / "SKILL.md"
    ).read_text()
    assert root_skill == plugin_skill, (
        "SKILL.md and skills/agent-execution-logging/SKILL.md must be "
        "byte-identical; edit both or sync them."
    )


def test_add_entry_rejects_empty_file_path(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    for spec in ("::only desc", ""):
        result = run_nocheck(
            ADD_ENTRY,
            "--root", str(tmp_path),
            "--title", "T",
            "--summary", "S",
            "--file", spec,
            "--date", "2026-05-17",
        )
        assert result.returncode != 0
        assert "empty file path" in result.stderr.lower()
    central = (tmp_path / "docs" / "code-base-ai-update-logs.md").read_text()
    assert "`` —" not in central


def test_add_entry_rejects_invalid_date(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    result = run_nocheck(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "T",
        "--summary", "S",
        "--file", "a.py",
        "--date", "2026-13-40",
    )
    assert result.returncode != 0
    assert "date" in result.stderr.lower()


def test_register_id_in_notes_does_not_false_match(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    registry = tmp_path / "docs" / "agent-execution-registry.md"
    # Seed a row whose Notes column references another agent's id in backticks.
    registry.write_text(
        registry.read_text()
        + "| Other | `other-agent` | "
        "[agent-logs/other-agent.md](./agent-logs/other-agent.md) | "
        "see `claude-code-opus-4-7` |\n"
    )
    result = run(
        REGISTER,
        "--root", str(tmp_path),
        "--agent-label", "Claude Opus 4.7",
        "--agent-id", "claude-code-opus-4-7",
    )
    assert "registered=claude-code-opus-4-7" in result.stdout
    id_cells = [
        [c.strip() for c in line.strip().strip("|").split("|")][1]
        for line in registry.read_text().splitlines()
        if line.strip().startswith("|")
    ]
    assert id_cells.count("`claude-code-opus-4-7`") == 1


def test_scripts_handle_non_ascii(tmp_path: Path) -> None:
    run(BOOTSTRAP, "--root", str(tmp_path))
    run(
        ADD_ENTRY,
        "--root", str(tmp_path),
        "--title", "Café — déjà vu 日本語",
        "--summary", "Handled non-ASCII summary.",
        "--file", "src/café.py::renommé",
        "--date", "2026-05-17",
    )
    central = (tmp_path / "docs" / "code-base-ai-update-logs.md").read_text(
        encoding="utf-8"
    )
    assert "## 2026-05-17 — Café — déjà vu 日本語" in central
    assert "- `src/café.py` — renommé" in central
