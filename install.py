#!/usr/bin/env python3
"""Install sprout.

    python3 install.py /path/to/project   vendor the tool and skills into a project
    python3 install.py --global           link the skills into your agent paths

Project mode copies .sprout/ and .agents/skills/ into the target, wires up the
agent entry points, and creates INVENTORY.csv. Safe to re-run: existing files
are left alone unless --force is given, so upgrading never clobbers your specs.

Global mode symlinks each skill out of this repository into ~/.claude/skills
and ~/.agents/skills, so `git pull` here updates every agent on the machine
with no re-install. The tool itself stays vendored per project on purpose: a
checkout must carry its own checks, or CI and a teammate's clone cannot run
them.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent

# Agents read skills from different paths. .agents/skills is the widest-read
# location (Codex CLI, Cursor, Gemini CLI); the rest are thin links to it.
SKILL_LINKS = (".claude/skills", ".cursor/skills", ".gemini/skills")

# Global mode needs only two: ~/.claude/skills for Claude Code, and
# ~/.agents/skills which Codex CLI, Cursor and Gemini CLI all read.
GLOBAL_SKILL_DIRS = (".claude/skills", ".agents/skills")


def link_or_copy(target, link_path, rel):
    """Symlink link_path -> rel, falling back to a copy where links are not
    available (Windows without developer mode)."""
    full = target / link_path
    if full.exists() or full.is_symlink():
        return f"skip   {link_path} (exists)"
    full.parent.mkdir(parents=True, exist_ok=True)
    try:
        full.symlink_to(Path(rel), target_is_directory=True)
        return f"link   {link_path} -> {rel}"
    except (OSError, NotImplementedError):
        shutil.copytree(target / ".agents" / "skills", full)
        return f"copy   {link_path} (symlinks unavailable)"


def install_global(home):
    """Symlink each skill into the user's agent directories.

    Links, never copies: a copy would have to be re-installed to update, which
    is the entire problem this mode exists to solve.
    """
    source = SRC / ".agents" / "skills"
    skills = sorted(d for d in source.iterdir() if d.is_dir())
    if not skills:
        print(f"install: no skills found in {source}", file=sys.stderr)
        return 2

    log, conflicts = [], 0
    for rel in GLOBAL_SKILL_DIRS:
        base = home / rel
        base.mkdir(parents=True, exist_ok=True)
        for skill in skills:
            link = base / skill.name
            if link.is_symlink():
                if link.resolve() == skill.resolve():
                    log.append(f"current {rel}/{skill.name}")
                    continue
                log.append(f"CONFLICT {rel}/{skill.name} -> {link.resolve()} "
                           f"(left alone)")
                conflicts += 1
                continue
            if link.exists():
                log.append(f"CONFLICT {rel}/{skill.name} exists and is not a link "
                           f"(left alone)")
                conflicts += 1
                continue
            try:
                link.symlink_to(skill.resolve(), target_is_directory=True)
                log.append(f"link    {rel}/{skill.name}")
            except (OSError, NotImplementedError) as exc:
                log.append(f"FAILED  {rel}/{skill.name}: {exc}")
                conflicts += 1

    for line in log:
        print(line)
    print(f"\nsprout skills linked from {SRC}")
    print("Update them with:  git -C " + str(SRC) + " pull")
    if conflicts:
        print(f"\n{conflicts} path(s) left alone - remove them by hand to link sprout there")
    print("\nThe tool stays per project. In each project run:")
    print(f"  python3 {SRC / 'install.py'} /path/to/project")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", type=Path, nargs="?",
                    help="project directory to install into")
    ap.add_argument("--force", action="store_true",
                    help="overwrite .sprout/ and skills (never touches specs or INVENTORY.csv)")
    ap.add_argument("--global", dest="globally", action="store_true",
                    help="link the skills into your agent paths instead")
    ap.add_argument("--home", type=Path, default=None,
                    help="home directory for --global (default: your home)")
    args = ap.parse_args()

    if args.globally:
        if args.target:
            ap.error("--global takes no target; it installs into your home directory")
        return install_global((args.home or Path.home()).resolve())
    if not args.target:
        ap.error("give a project directory, or --global to link the skills")

    target = args.target.resolve()
    if target == SRC:
        print("install: target is the sprout repo itself; nothing to do", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)
    log = []

    # --- tooling and skills: replaceable, so --force is meaningful here ---
    for rel in (".sprout", ".agents/skills"):
        dest = target / rel
        if dest.exists() and not args.force:
            log.append(f"skip   {rel}/ (exists; --force to update)")
            continue
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SRC / rel, dest)
        log.append(f"{'update' if args.force else 'copy  '} {rel}/")

    for link in SKILL_LINKS:
        depth = len(Path(link).parts) - 1
        log.append(link_or_copy(target, link, "../" * depth + ".agents/skills"))

    # --- project state: never overwritten, even with --force ---
    inventory = target / "INVENTORY.csv"
    if inventory.exists():
        log.append("skip   INVENTORY.csv (exists)")
    else:
        shutil.copy2(SRC / ".sprout" / "templates" / "INVENTORY.csv", inventory)
        log.append("create INVENTORY.csv")

    for d in ("specs", "exploded-specs", "slices", "spikes", "verify"):
        (target / d).mkdir(exist_ok=True)
    log.append("create specs/ exploded-specs/ slices/ spikes/ verify/")

    block = (SRC / ".sprout" / "templates" / "AGENTS-block.md").read_text(encoding="utf-8")
    # Strip whole comment blocks. Matching line prefixes is not enough: the
    # guidance comment spans lines, so its closing tail survives a line filter.
    body = re.sub(r"<!--.*?-->", "", block, flags=re.DOTALL)
    agents = target / "AGENTS.md"
    existing = agents.read_text(encoding="utf-8") if agents.exists() else ""
    if "How work happens here (sprout)" in existing:
        log.append("skip   AGENTS.md (sprout block already present)")
    else:
        sep = "\n\n" if existing.strip() else ""
        agents.write_text(existing.rstrip() + sep + body.strip() + "\n", encoding="utf-8")
        log.append("append AGENTS.md" if existing.strip() else "create AGENTS.md")

    claude_md = target / "CLAUDE.md"
    if not (claude_md.exists() or claude_md.is_symlink()):
        try:
            claude_md.symlink_to("AGENTS.md")
            log.append("link   CLAUDE.md -> AGENTS.md")
        except (OSError, NotImplementedError):
            claude_md.write_text("See @AGENTS.md\n", encoding="utf-8")
            log.append("create CLAUDE.md (pointer)")
    else:
        log.append("skip   CLAUDE.md (exists)")

    for line in log:
        print(line)
    print(f"\nsprout installed into {target}")
    print("Next: start the sprout-spec skill, or run  python3 .sprout/sprout.py check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
