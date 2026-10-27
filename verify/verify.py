#!/usr/bin/env python3
"""Black-box verification of sprout's own capabilities.

    python3 verify/verify.py <capability-id>
    python3 verify/verify.py --all
    python3 verify/verify.py --list

Every test drives the CLI as a subprocess in a throwaway project and asserts on
exit codes and output. Nothing here imports sprout.py: these are black-box
tests of the shipped interface, which is what the method requires of everyone
else.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = {}


def test(name):
    def deco(fn):
        TESTS[name] = fn
        return fn
    return deco


# --------------------------------------------------------------------------
# harness
# --------------------------------------------------------------------------

def sprout(project, *args):
    return subprocess.run(
        [sys.executable, str(project / ".sprout" / "sprout.py"), *args],
        cwd=project, capture_output=True, text=True,
    )


INV_HEADER = (
    "# Inventory\n\n"
    "| ID | Capability | Status | Spec | Ver | Verify |\n"
    "|---|---|---|---|---|---|\n"
)


class Project:
    """A throwaway sprout project."""

    def __init__(self, tmp):
        self.path = Path(tmp)
        shutil.copytree(ROOT / ".sprout", self.path / ".sprout")
        for d in ("specs", "exploded-specs", "slices", "spikes", "verify"):
            (self.path / d).mkdir()
        self.inventory([])

    def spec(self, name, version=1, kind="spec", sub="specs", status="active"):
        p = self.path / sub / f"{name}.md"
        p.write_text(
            f"---\nid: {name}\nkind: {kind}\nversion: {version}\nstatus: {status}\n---\n\n# {name}\n",
            encoding="utf-8",
        )
        return p

    def slice_doc(self, name, status="planned", subsystems=()):
        table = ""
        if subsystems:
            rows = "".join(
                f"| {s} | exploded-specs/{s}.md | New |\n" for s in subsystems)
            table = ("\n## Subsystems touched\n\n"
                     "| Subsystem | Exploded spec | New or changed |\n|---|---|---|\n" + rows)
        p = self.path / "slices" / f"{name}.md"
        p.write_text(
            f"---\nid: {name}\nkind: slice\nversion: 1\nstatus: {status}\n---\n\n"
            f"# {name}\n{table}",
            encoding="utf-8",
        )
        return p

    def next_json(self, *args):
        r = self.run("next", "--json", *args)
        try:
            return r, json.loads(r.stdout)
        except json.JSONDecodeError:
            return r, None

    def inventory(self, rows):
        body = INV_HEADER + "".join(f"| {' | '.join(r)} |\n" for r in rows)
        (self.path / "INVENTORY.md").write_text(body, encoding="utf-8")

    def script(self, name, exit_code):
        p = self.path / "verify" / name
        p.write_text(f"import sys\nsys.exit({exit_code})\n", encoding="utf-8")
        return f"python3 verify/{name}"

    def run(self, *args):
        return sprout(self.path, *args)


def project():
    tmp = tempfile.mkdtemp(prefix="sprout-verify-")
    return Project(tmp), tmp


def expect(cond, msg):
    if not cond:
        raise AssertionError(msg)


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

@test("cli-check-requires-versioned-specs")
def _():
    """check fails when a spec lacks a version, passes when it has one."""
    p, tmp = project()
    try:
        p.spec("overview", version=1)
        r = p.run("check")
        expect(r.returncode == 0, f"valid spec should pass, got {r.returncode}\n{r.stdout}")

        (p.path / "specs" / "overview.md").write_text(
            "---\nid: overview\nkind: spec\nstatus: active\n---\n\n# x\n", encoding="utf-8")
        r = p.run("check")
        expect(r.returncode == 1, "unversioned spec must fail check")
        expect("version" in r.stdout, f"error should name the missing field:\n{r.stdout}")

        (p.path / "specs" / "overview.md").write_text(
            "# no frontmatter\n", encoding="utf-8")
        r = p.run("check")
        expect(r.returncode == 1, "spec without frontmatter must fail check")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cli-check-detects-spec-drift")
def _():
    """A row pinned to an older spec version fails until re-pinned."""
    p, tmp = project()
    try:
        p.spec("auth", version=1, kind="exploded-spec", sub="exploded-specs")
        cmd = p.script("ok.py", 0)
        p.inventory([("auth-login", "User can log in", "built",
                      "exploded-specs/auth.md", "1", f"`{cmd}`")])
        r = p.run("check")
        expect(r.returncode == 0, f"correctly pinned row should pass:\n{r.stdout}")

        p.spec("auth", version=2, kind="exploded-spec", sub="exploded-specs")
        r = p.run("check")
        expect(r.returncode == 1, "stale pin must fail check")
        expect("DRIFT" in r.stdout, f"failure should be reported as drift:\n{r.stdout}")

        p.inventory([("auth-login", "User can log in", "built",
                      "exploded-specs/auth.md", "2", f"`{cmd}`")])
        r = p.run("check")
        expect(r.returncode == 0, f"re-pinned row should pass:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cli-check-rejects-unverifiable-capabilities")
def _():
    """Built rows need a real verify command; planned rows do not."""
    p, tmp = project()
    try:
        p.spec("overview")
        for placeholder in ("-", "none", "TODO", ""):
            p.inventory([("thing", "A thing", "built", "specs/overview.md", "1", placeholder)])
            r = p.run("check")
            expect(r.returncode == 1, f"built row with verify={placeholder!r} must fail")
            expect("unverifiable" in r.stdout or "no verify" in r.stdout,
                   f"error should explain the rule, got:\n{r.stdout}")

        p.inventory([("thing", "A thing", "planned", "specs/overview.md", "1", "-")])
        expect(p.run("check").returncode == 0, "planned row may lack a verify command")

        cmd = p.script("ok.py", 0)
        p.inventory([("thing", "A thing", "built", "specs/overview.md", "1", f"`{cmd}`")])
        expect(p.run("check").returncode == 0, "built row with command should pass")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cli-check-rejects-shell-metacharacters")
def _():
    """Verify commands must be single invocations, not pipelines."""
    p, tmp = project()
    try:
        p.spec("overview")
        for bad in ("make test > out.txt", "a && b", "x ; y"):
            p.inventory([("thing", "A thing", "built", "specs/overview.md", "1", f"`{bad}`")])
            r = p.run("check")
            expect(r.returncode == 1, f"verify {bad!r} must be rejected")
            expect("metacharacter" in r.stdout, f"error should name the reason:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cli-check-rejects-duplicate-and-missing-refs")
def _():
    """Duplicate IDs and dangling spec references are caught."""
    p, tmp = project()
    try:
        p.spec("overview")
        cmd = p.script("ok.py", 0)
        p.inventory([
            ("thing", "A thing", "built", "specs/overview.md", "1", f"`{cmd}`"),
            ("thing", "Another", "built", "specs/overview.md", "1", f"`{cmd}`"),
        ])
        r = p.run("check")
        expect(r.returncode == 1, "duplicate IDs must fail")
        expect("duplicate" in r.stdout, f"error should say duplicate:\n{r.stdout}")

        p.inventory([("thing", "A thing", "built", "specs/ghost.md", "1", f"`{cmd}`")])
        r = p.run("check")
        expect(r.returncode == 1, "dangling spec ref must fail")
        expect("does not exist" in r.stdout, f"error should say missing:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cli-verify-executes-commands")
def _():
    """verify runs each built row's command and reports pass/fail honestly."""
    p, tmp = project()
    try:
        p.spec("overview")
        good = p.script("ok.py", 0)
        bad = p.script("bad.py", 3)

        p.inventory([("good", "Works", "built", "specs/overview.md", "1", f"`{good}`")])
        r = p.run("verify")
        expect(r.returncode == 0, f"passing command should exit 0:\n{r.stdout}")
        expect("PASS" in r.stdout, f"should report PASS:\n{r.stdout}")

        p.inventory([("bad", "Broken", "built", "specs/overview.md", "1", f"`{bad}`")])
        r = p.run("verify")
        expect(r.returncode == 1, f"failing command must exit 1, got {r.returncode}")
        expect("FAIL" in r.stdout, f"should report FAIL:\n{r.stdout}")

        p.inventory([
            ("good", "Works", "built", "specs/overview.md", "1", f"`{good}`"),
            ("later", "Not yet", "planned", "specs/overview.md", "1", "-"),
        ])
        r = p.run("verify")
        expect(r.returncode == 0, "planned rows must not be executed")
        expect("later" not in r.stdout, "planned rows should be skipped silently")

        r = p.run("verify", "--id", "good")
        expect(r.returncode == 0 and "good" in r.stdout, "--id should target one row")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cli-new-scaffolds-documents")
def _():
    """new creates a templated doc with its id filled in, and refuses to clobber."""
    p, tmp = project()
    try:
        for kind, sub in (("spec", "specs"), ("slice", "slices"),
                          ("exploded-spec", "exploded-specs"), ("spike", "spikes")):
            r = p.run("new", kind, "my-thing")
            expect(r.returncode == 0, f"new {kind} failed:\n{r.stdout}{r.stderr}")
            created = p.path / sub / "my-thing.md"
            expect(created.exists(), f"new {kind} did not create {sub}/my-thing.md")
            text = created.read_text(encoding="utf-8")
            expect("id: my-thing" in text, f"{kind}: id not substituted")
            expect(f"kind: {kind}" in text, f"{kind}: wrong kind in frontmatter")
            expect("{{" not in text, f"{kind}: unsubstituted placeholder remains")

        r = p.run("new", "spec", "my-thing")
        expect(r.returncode == 2, "new must refuse to overwrite an existing doc")

        r = p.run("new", "spec", "Bad Name")
        expect(r.returncode == 2, "new must reject non-kebab-case names")

        expect(p.run("check").returncode == 0, "scaffolded docs must pass check")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cli-status-reports-progress")
def _():
    """status groups capabilities by state and counts what is built."""
    p, tmp = project()
    try:
        p.spec("overview")
        cmd = p.script("ok.py", 0)
        p.inventory([
            ("done", "Shipped thing", "built", "specs/overview.md", "1", f"`{cmd}`"),
            ("wip", "In progress", "building", "specs/overview.md", "1", "-"),
            ("todo", "Future thing", "planned", "specs/overview.md", "1", "-"),
        ])
        r = p.run("status")
        expect(r.returncode == 0, f"status failed:\n{r.stderr}")
        for token in ("BUILT", "BUILDING", "PLANNED", "done", "wip", "todo", "1/3 built"):
            expect(token in r.stdout, f"status output missing {token!r}:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("skills-are-cross-agent-portable")
def _():
    """Every shipped skill obeys the Agent Skills open standard."""
    skills_dir = ROOT / ".agents" / "skills"
    dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    expect(len(dirs) >= 6, f"expected at least 6 skills, found {len(dirs)}")

    for d in dirs:
        names = [p.name for p in d.iterdir() if p.name.lower() == "skill.md"]
        expect(names == ["SKILL.md"],
               f"{d.name}: must contain exactly 'SKILL.md' (found {names}); "
               f"case-sensitive filesystems ignore other spellings")

        lines = (d / "SKILL.md").read_text(encoding="utf-8").splitlines()
        expect(lines[0].strip() == "---", f"{d.name}: must open with frontmatter")
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
        fm = {}
        for line in lines[1:end]:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()

        expect(set(fm) == {"name", "description"},
               f"{d.name}: portable skills use only name and description, found {sorted(fm)}")
        expect(fm["name"] == d.name, f"{d.name}: name {fm['name']!r} must match directory")
        expect(len(fm["description"]) <= 1024, f"{d.name}: description over 1024 chars")
        expect(len(fm["description"]) >= 40,
               f"{d.name}: description too vague for semantic activation")
        expect(fm["description"].lower().startswith(
            ("write", "define", "implement", "fold", "demonstrate", "investigate")),
            f"{d.name}: description should open with an action verb")
        expect(any(t in fm["description"] for t in ("Use when", "Use after", "Use whenever")),
               f"{d.name}: description must state a trigger condition "
               f"('Use when/after/whenever ...') so agents can activate it semantically")
        expect(len(lines) <= 500, f"{d.name}: {len(lines)} lines, over the 500-line guidance")
    return len(dirs)


@test("install-bootstraps-a-project")
def _():
    """install.py produces a working project that passes its own checks."""
    tmp = tempfile.mkdtemp(prefix="sprout-install-")
    try:
        target = Path(tmp) / "newproj"
        r = subprocess.run([sys.executable, str(ROOT / "install.py"), str(target)],
                           capture_output=True, text=True)
        expect(r.returncode == 0, f"install failed:\n{r.stdout}{r.stderr}")

        for rel in (".sprout/sprout.py", ".agents/skills/sprout-build/SKILL.md",
                    "INVENTORY.md", "AGENTS.md", "specs", "verify"):
            expect((target / rel).exists(), f"install did not create {rel}")

        claude = target / ".claude" / "skills"
        expect(claude.exists(), "install did not wire .claude/skills")
        expect((claude / "sprout-build" / "SKILL.md").exists(),
               ".claude/skills does not resolve to the skills")

        agents = (target / "AGENTS.md").read_text(encoding="utf-8")
        expect("sprout" in agents.lower(), "AGENTS.md has no sprout block")
        expect("<!--" not in agents and "-->" not in agents,
               f"AGENTS.md still contains comment markup:\n{agents[:400]}")
        expect("sprout.py next" in agents,
               "AGENTS.md should tell a resuming agent to ask where it is")

        expect(sprout(target, "check").returncode == 0,
               f"fresh install should pass check:\n{sprout(target, 'check').stdout}")
        expect(sprout(target, "status").returncode == 0, "fresh install should report status")

        # re-running must not clobber project state
        (target / "specs" / "overview.md").write_text(
            "---\nid: overview\nkind: spec\nversion: 7\nstatus: active\n---\n\n# Mine\n",
            encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "install.py"), str(target), "--force"],
                           capture_output=True, text=True)
        expect(r.returncode == 0, f"re-install failed:\n{r.stdout}{r.stderr}")
        expect("version: 7" in (target / "specs" / "overview.md").read_text(encoding="utf-8"),
               "--force must never overwrite specs")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- slice: know-where-you-are ---------------------------------------------

@test("slice-lifecycle-is-representable")
def _():
    """A slice carries a delivery lifecycle, distinct from editorial status."""
    p, tmp = project()
    try:
        p.spec("overview")
        for status in ("planned", "building", "built", "showcased"):
            p.slice_doc("s1", status=status)
            r = p.run("check")
            expect(r.returncode == 0,
                   f"slice status {status!r} must be accepted:\n{r.stdout}")

        for status in ("draft", "active", "superseded"):
            p.slice_doc("s1", status=status)
            r = p.run("check")
            expect(r.returncode == 1,
                   f"editorial status {status!r} must be rejected on a slice")
            expect("showcased" in r.stdout,
                   f"error should name the valid slice statuses:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("check-validates-status-per-kind")
def _():
    """Status is validated against the document's kind, not merely present."""
    p, tmp = project()
    try:
        for kind, sub in (("spec", "specs"), ("exploded-spec", "exploded-specs"),
                          ("spike", "spikes")):
            for status in ("draft", "active", "superseded"):
                p.spec("d1", kind=kind, sub=sub, status=status)
                r = p.run("check")
                expect(r.returncode == 0,
                       f"{kind} status {status!r} must be accepted:\n{r.stdout}")
            for status in ("built", "showcased", "nonsense"):
                p.spec("d1", kind=kind, sub=sub, status=status)
                r = p.run("check")
                expect(r.returncode == 1,
                       f"{kind} status {status!r} must be rejected")
                expect("status" in r.stdout.lower(),
                       f"error should concern status:\n{r.stdout}")
            (p.path / sub / "d1.md").unlink()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("next-reports-position")
def _():
    """next names the loop, the reason, the blocker and the next action."""
    p, tmp = project()
    try:
        p.spec("overview")
        p.slice_doc("s1", status="building")
        p.inventory([("cap", "A capability", "planned", "specs/overview.md", "1", "-")])

        r = p.run("next")
        expect(r.returncode == 0, f"next must exit 0, got {r.returncode}\n{r.stderr}")
        for label in ("loop", "reason", "blocker", "action"):
            expect(label in r.stdout.lower(), f"human output missing {label!r}:\n{r.stdout}")

        r, data = p.next_json()
        expect(data is not None, f"--json must emit valid JSON, got:\n{r.stdout}")
        for key in ("loop", "reason", "blocker", "action", "rule"):
            expect(key in data, f"JSON missing {key!r}: {data}")
        expect(data["loop"].startswith("sprout-"),
               f"loop should name a skill, got {data['loop']!r}")
        expect(isinstance(data["rule"], int), "rule should be the precedence number")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("next-precedence-is-deterministic")
def _():
    """Published precedence resolves ambiguity, and repeats identically."""
    p, tmp = project()
    try:
        ok = p.script("ok.py", 0)

        # rule 8 - nothing at all
        _, d = p.next_json()
        expect(d["loop"] == "sprout-spec", f"empty project should route to spec, got {d}")

        # rule 7 - overview, no slice in flight
        p.spec("overview")
        _, d = p.next_json()
        expect(d["loop"] == "sprout-slice", f"no slice should route to slice, got {d}")

        # rule 6 - slice in flight with planned rows
        p.slice_doc("s1", status="planned")
        p.inventory([("cap", "A cap", "planned", "specs/overview.md", "1", f"`{ok}`")])
        _, d = p.next_json()
        expect(d["loop"] == "sprout-build", f"planned rows should route to build, got {d}")

        # rule 5 - a touched subsystem has no exploded spec; outranks 6
        p.slice_doc("s1", status="planned", subsystems=("ghost",))
        _, d = p.next_json()
        expect(d["loop"] == "sprout-slice",
               f"missing exploded spec should route to slice, got {d}")
        p.spec("ghost", kind="exploded-spec", sub="exploded-specs")
        _, d = p.next_json()
        expect(d["loop"] == "sprout-build", f"once exploded, back to build, got {d}")

        # rule 4 - slice built but not showcased
        p.slice_doc("s1", status="built", subsystems=("ghost",))
        p.inventory([("cap", "A cap", "built", "specs/overview.md", "1", f"`{ok}`")])
        _, d = p.next_json()
        expect(d["loop"] == "sprout-showcase",
               f"built-not-showcased should route to showcase, got {d}")

        # rule 3 - a building row outranks rule 4
        p.inventory([("cap", "A cap", "building", "specs/overview.md", "1", f"`{ok}`")])
        _, d = p.next_json()
        expect(d["loop"] == "sprout-build", f"building row outranks showcase, got {d}")

        # rule 2 - drift outranks rule 3
        p.spec("overview", version=2)
        _, d = p.next_json()
        expect(d["loop"] == "sprout-tidy", f"drift outranks progress, got {d}")

        # rule 1 - structural failure outranks drift
        (p.path / "INVENTORY.md").write_text("# Inventory\n\nno table here\n",
                                             encoding="utf-8")
        _, d = p.next_json()
        expect(d["rule"] == 1, f"structural failure must be rule 1, got {d}")

        # determinism
        p.spec("overview", version=1)
        p.inventory([("cap", "A cap", "planned", "specs/overview.md", "1", f"`{ok}`")])
        first = [p.next_json()[1] for _ in range(3)]
        expect(all(x == first[0] for x in first), f"next must be deterministic: {first}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("next-survives-degenerate-projects")
def _():
    """Degenerate projects yield a position or a clear refusal, never a crash."""
    p, tmp = project()
    bare_tmp = tempfile.mkdtemp(prefix="sprout-bare-")
    try:
        # An uninitialised directory must sit OUTSIDE the project tree: root
        # discovery walks up, so a subdirectory of a project is still inside it.
        bare = Path(bare_tmp)
        r = subprocess.run(
            [sys.executable, str(p.path / ".sprout" / "sprout.py"), "next"],
            cwd=bare, capture_output=True, text=True)
        expect(r.returncode == 2, f"uninitialised project should exit 2, got {r.returncode}")
        # argparse also exits 2 for an unknown subcommand, so pin the reason:
        # this must fail for want of a project, not for want of the command.
        expect("invalid choice" not in r.stderr,
               "next subcommand does not exist")
        expect(".sprout" in r.stderr,
               f"refusal should name the missing project marker:\n{r.stderr}")

        # initialised but entirely empty
        r, d = p.next_json()
        expect(r.returncode == 0, "empty project should still report a position")
        expect(d["loop"] == "sprout-spec", f"empty should route to spec, got {d}")

        # inventory missing entirely
        (p.path / "INVENTORY.md").unlink()
        r, d = p.next_json()
        expect(r.returncode == 0, f"missing inventory must not crash: {r.stderr}")
        expect(d is not None and d["rule"] == 1, f"should be rule 1, got {d}")
        expect(d["blocker"], "rule 1 must name a blocker")

        # unparseable frontmatter
        (p.path / "INVENTORY.md").write_text(INV_HEADER, encoding="utf-8")
        (p.path / "specs" / "broken.md").write_text("no frontmatter at all\n",
                                                    encoding="utf-8")
        r, d = p.next_json()
        expect(r.returncode == 0, f"unparseable spec must not crash: {r.stderr}")
        expect(d["rule"] == 1, f"should be rule 1, got {d}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(bare_tmp, ignore_errors=True)


# --------------------------------------------------------------------------

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--list":
        for name in TESTS:
            print(name)
        return 0

    names = list(TESTS) if argv[0] == "--all" else [argv[0]]
    unknown = [n for n in names if n not in TESTS]
    if unknown:
        print(f"unknown capability: {unknown[0]}", file=sys.stderr)
        print(f"known: {', '.join(TESTS)}", file=sys.stderr)
        return 2

    failures = 0
    for name in names:
        try:
            TESTS[name]()
            print(f"ok    {name}")
        except AssertionError as exc:
            print(f"FAIL  {name}\n      {exc}")
            failures += 1
        except Exception as exc:  # noqa: BLE001 - a broken test is a failure
            print(f"ERROR {name}\n      {type(exc).__name__}: {exc}")
            failures += 1

    if len(names) > 1:
        print(f"\n{len(names) - failures}/{len(names)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
