#!/usr/bin/env python3
"""
STD-002 structural validator (CI).

Mirrors the structural checks in `.claude/commands/vkf/validate.md` that
don't require an LLM: directory layout, Core constitution presence,
`[REQUIRED]` placeholder detection, and presence of VKF command files.

Exit codes:
  0  PASS (or not-yet-initialized — informational only)
  1  FAIL (structural violations or placeholders in filled-in files)

The full /vkf/validate command (via Claude Code) additionally performs
freshness, amendment-history, and semantic checks. This CI check is
intentionally the subset that requires no LLM.
"""
from __future__ import annotations

import os
import sys
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# ────────────────────────── config (mirrors STD-002 defaults) ──────────────────────────

CORE_CONSTITUTION = ["index.md", "mission.md", "pmf-thesis.md", "principles.md"]
EXTENDED_CONSTITUTION = ["personas.md", "icps.md", "positioning.md", "governance.md"]
REQUIRED_DIRS = ["specs/constitution", "specs/features", "changes", "archive", ".claude/commands"]
PLACEHOLDER_PATTERN = re.compile(r"\[REQUIRED(?::[^\]]*)?\]")

# ────────────────────────── reporting ──────────────────────────

fails: list[str] = []
warns: list[str] = []
infos: list[str] = []


def record_fail(msg: str) -> None:
    fails.append(msg)


def record_warn(msg: str) -> None:
    warns.append(msg)


def record_info(msg: str) -> None:
    infos.append(msg)


# ────────────────────────── checks ──────────────────────────


def check_structure() -> None:
    for d in REQUIRED_DIRS:
        p = REPO / d
        if not p.exists():
            record_fail(f"[structure] required directory missing: {d}/")


def is_unfilled(path: Path) -> bool:
    """A constitution dir is 'unfilled' if it holds only .gitkeep or is empty.

    A freshly-forked template that has not run /vkf/init falls here.
    """
    if not path.exists() or not path.is_dir():
        return True
    md_files = [p for p in path.glob("*.md") if p.name != ".gitkeep"]
    return len(md_files) == 0


def check_constitution() -> None:
    const_dir = REPO / "specs" / "constitution"

    if is_unfilled(const_dir):
        record_info(
            "[constitution] not yet initialized — run /vkf/init in Claude Code "
            "to bootstrap. Skipping Core/Extended checks."
        )
        return

    # Core tier — FAIL if any missing or if placeholders remain
    for name in CORE_CONSTITUTION:
        f = const_dir / name
        if not f.exists():
            record_fail(f"[constitution] Core file missing: specs/constitution/{name}")
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        hits = PLACEHOLDER_PATTERN.findall(text)
        if hits:
            record_fail(
                f"[constitution] specs/constitution/{name} still has "
                f"{len(hits)} [REQUIRED] placeholder(s) — finish drafting via /vkf/constitution"
            )

    # Extended tier — WARN if missing; FAIL if present but still has placeholders
    for name in EXTENDED_CONSTITUTION:
        f = const_dir / name
        if not f.exists():
            record_warn(
                f"[constitution] Extended file absent: specs/constitution/{name} "
                f"(adopt when relevant — see docs/onboarding/04-bootstrap-your-venture.md)"
            )
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        hits = PLACEHOLDER_PATTERN.findall(text)
        if hits:
            record_fail(
                f"[constitution] specs/constitution/{name} exists but has "
                f"{len(hits)} [REQUIRED] placeholder(s) — finish it or delete it"
            )


def check_commands() -> None:
    cmd_dir = REPO / ".claude" / "commands"
    if not cmd_dir.exists():
        return  # already failed in structure check
    total = sum(1 for _ in cmd_dir.rglob("*.md"))
    if total == 0:
        record_fail("[workflows] .claude/commands/ exists but has no command files")
        return
    vkf_dir = cmd_dir / "vkf"
    if not vkf_dir.exists() or not any(vkf_dir.glob("*.md")):
        record_warn("[workflows] no VKF commands in .claude/commands/vkf/")
    sdd_dir = cmd_dir / "sdd"
    if not sdd_dir.exists() or not any(sdd_dir.glob("*.md")):
        record_warn("[workflows] no SDD commands in .claude/commands/sdd/")


def check_features_placeholders() -> None:
    """A canonical feature spec should never contain [REQUIRED] markers."""
    features = REPO / "specs" / "features"
    if not features.exists():
        return
    for spec in features.rglob("spec.md"):
        text = spec.read_text(encoding="utf-8", errors="replace")
        hits = PLACEHOLDER_PATTERN.findall(text)
        if hits:
            rel = spec.relative_to(REPO)
            record_fail(
                f"[features] {rel} has {len(hits)} [REQUIRED] placeholder(s) — "
                f"canonical feature specs should be complete"
            )


# ────────────────────────── main ──────────────────────────


def main() -> int:
    check_structure()
    check_constitution()
    check_commands()
    check_features_placeholders()

    # Render report
    print("STD-002 structural validation")
    print("=" * 60)
    if not (fails or warns or infos):
        print("✓ PASS — no issues detected")
    else:
        if fails:
            print(f"\nFAIL ({len(fails)}):")
            for msg in fails:
                print(f"  ✗ {msg}")
        if warns:
            print(f"\nWARN ({len(warns)}):")
            for msg in warns:
                print(f"  ⚠ {msg}")
        if infos:
            print(f"\nINFO ({len(infos)}):")
            for msg in infos:
                print(f"  ℹ {msg}")

    # GitHub Actions summary (when running in CI)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("## STD-002 structural validation\n\n")
            if not (fails or warns or infos):
                fh.write("**PASS** — no issues detected.\n")
            else:
                if fails:
                    fh.write(f"### FAIL ({len(fails)})\n\n")
                    for msg in fails:
                        fh.write(f"- {msg}\n")
                    fh.write("\n")
                if warns:
                    fh.write(f"### WARN ({len(warns)})\n\n")
                    for msg in warns:
                        fh.write(f"- {msg}\n")
                    fh.write("\n")
                if infos:
                    fh.write(f"### INFO ({len(infos)})\n\n")
                    for msg in infos:
                        fh.write(f"- {msg}\n")
                    fh.write("\n")
            fh.write(
                "\n---\nThis is the CI subset of `/vkf/validate`. "
                "For full validation (freshness, amendment history, semantic checks), "
                "run `/vkf/validate` in Claude Code locally.\n"
            )

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
