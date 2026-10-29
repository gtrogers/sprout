#!/usr/bin/env python3
"""Black-box verification of sprout's own subsystems.

    python3 verify/verify.py <subsystem>     run one subsystem's tests
    python3 verify/verify.py --all
    python3 verify/verify.py --list

Tests are grouped by subsystem, because that is the unit the ledger tracks:
each row's verify command asks "does this subsystem meet its spec".

Every test drives the CLI as a subprocess in a throwaway project and asserts on
exit codes and output. Nothing here imports sprout.py: these are black-box
tests of the shipped interface, which is what the method requires of everyone
else.
"""

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = OrderedDict()          # subsystem -> [(name, fn), ...]
INV_COLUMNS = ("subsystem", "spec", "implemented", "verify")
OK_CMD = "python3 verify/ok.py"


def test(subsystem, name):
    def deco(fn):
        TESTS.setdefault(subsystem, []).append((name, fn))
        return fn
    return deco


# --------------------------------------------------------------------------
# harness
# --------------------------------------------------------------------------

class Project:
    """A throwaway sprout project."""

    def __init__(self, tmp):
        self.path = Path(tmp)
        shutil.copytree(ROOT / ".sprout", self.path / ".sprout")
        for d in ("specs", "exploded-specs", "slices", "spikes", "verify"):
            (self.path / d).mkdir()
        self._rows = OrderedDict()
        self._write()
        self.script("ok.py", 0)

    # --- documents -------------------------------------------------------

    def spec(self, name, version=1, kind="spec", sub="specs", status="active"):
        p = self.path / sub / f"{name}.md"
        p.write_text(
            f"---\nid: {name}\nkind: {kind}\nversion: {version}\n"
            f"status: {status}\n---\n\n# {name}\n",
            encoding="utf-8")
        return p

    def slice_doc(self, name, status=None):
        decl = f"status: {status}\n" if status is not None else ""
        p = self.path / "slices" / f"{name}.md"
        p.write_text(
            f"---\nid: {name}\nkind: slice\nversion: 1\n{decl}---\n\n# {name}\n",
            encoding="utf-8")
        return p

    # --- the ledger ------------------------------------------------------

    def subsystem(self, name, version=1, implemented="", verify=OK_CMD):
        """An exploded spec and its ledger row, created together: the checker
        requires exactly one row per exploded spec."""
        self.spec(name, version=version, kind="exploded-spec", sub="exploded-specs")
        self._rows[name] = [name, f"exploded-specs/{name}.md",
                            str(implemented), verify]
        self._write()

    def spec_version(self, name, version):
        """Advance a subsystem's spec, leaving its implementation behind."""
        self.spec(name, version=version, kind="exploded-spec", sub="exploded-specs")

    def implemented(self, name, version):
        self._rows[name][2] = str(version)
        self._write()

    def drop_row(self, name):
        del self._rows[name]
        self._write()

    def _write(self):
        with (self.path / "INVENTORY.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(INV_COLUMNS)
            w.writerows(self._rows.values())

    def raw_inventory(self, text):
        (self.path / "INVENTORY.csv").write_text(text, encoding="utf-8")

    # --- running ---------------------------------------------------------

    def script(self, name, exit_code):
        p = self.path / "verify" / name
        p.write_text(f"import sys\nsys.exit({exit_code})\n", encoding="utf-8")
        return f"python3 verify/{name}"

    def run(self, *args):
        return subprocess.run(
            [sys.executable, str(self.path / ".sprout" / "sprout.py"), *args],
            cwd=self.path, capture_output=True, text=True)

    def next_json(self, *args):
        r = self.run("next", "--json", *args)
        try:
            return r, json.loads(r.stdout)
        except json.JSONDecodeError:
            return r, None


def project():
    tmp = tempfile.mkdtemp(prefix="sprout-verify-")
    return Project(tmp), tmp


def expect(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ==========================================================================
# document-kinds
# ==========================================================================

@test("document-kinds", "specs carry a version")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        expect(p.run("check").returncode == 0, "a versioned spec should pass")

        (p.path / "specs" / "overview.md").write_text(
            "---\nid: overview\nkind: spec\nstatus: active\n---\n\n# x\n", encoding="utf-8")
        r = p.run("check")
        expect(r.returncode == 1, "unversioned spec must fail")
        expect("version" in r.stdout, f"should name the field:\n{r.stdout}")

        (p.path / "specs" / "overview.md").write_text("# none\n", encoding="utf-8")
        expect(p.run("check").returncode == 1, "spec without frontmatter must fail")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("document-kinds", "status is validated against kind")
def _():
    p, tmp = project()
    try:
        for kind, sub in (("spec", "specs"), ("spike", "spikes")):
            for status in ("draft", "active", "superseded"):
                p.spec("d1", kind=kind, sub=sub, status=status)
                expect(p.run("check").returncode == 0,
                       f"{kind}/{status} should be accepted")
            for status in ("built", "nonsense"):
                p.spec("d1", kind=kind, sub=sub, status=status)
                r = p.run("check")
                expect(r.returncode == 1, f"{kind}/{status} must be rejected")
                expect("status" in r.stdout.lower(), f"should concern status:\n{r.stdout}")
            (p.path / sub / "d1.md").unlink()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("document-kinds", "a slice declares neither status nor subsystems")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.slice_doc("s1")
        expect(p.run("check").returncode == 0, "a bare slice document is valid")

        for declared in ("built", "showcased", "planned", "anything"):
            p.slice_doc("s1", status=declared)
            r = p.run("check")
            expect(r.returncode == 1, f"declared status {declared!r} must be rejected")
            expect("derived" in r.stdout.lower(),
                   f"should explain state is derived:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("document-kinds", "scaffolding produces checkable documents")
def _():
    p, tmp = project()
    try:
        for kind, sub in (("spec", "specs"), ("slice", "slices"),
                          ("exploded-spec", "exploded-specs"), ("spike", "spikes")):
            r = p.run("new", kind, "my-thing")
            expect(r.returncode == 0, f"new {kind} failed:\n{r.stdout}{r.stderr}")
            created = p.path / sub / "my-thing.md"
            text = created.read_text(encoding="utf-8")
            expect(f"kind: {kind}" in text, f"{kind}: wrong kind")
            expect("id: my-thing" in text, f"{kind}: id not substituted")
            expect("{{" not in text, f"{kind}: placeholder left behind")

        expect(p.run("new", "spec", "my-thing").returncode == 2,
               "new must refuse to overwrite")
        expect(p.run("new", "spec", "Bad Name").returncode == 2,
               "new must reject non-kebab names")

        # scaffolding an exploded spec must also enter it in the ledger,
        # or the project is left failing its own checks
        rows = (p.path / "INVENTORY.csv").read_text(encoding="utf-8")
        expect("my-thing" in rows,
               f"new exploded-spec should add a ledger row:\n{rows}")
        r = p.run("check")
        expect(r.returncode == 0, f"scaffolded documents must pass check:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
# inventory
# ==========================================================================

@test("inventory", "the ledger is CSV and survives punctuation")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("auth", version=1, implemented=1,
                    verify='python3 verify/ok.py')
        expect(p.run("check").returncode == 0, "a consistent ledger should pass")

        path = p.path / "INVENTORY.csv"
        with path.open(newline="", encoding="utf-8") as fh:
            parsed = list(csv.DictReader(fh))
        expect([c for c in parsed[0]] == list(INV_COLUMNS),
               f"unexpected columns: {list(parsed[0])}")
        expect(parsed[0]["subsystem"] == "auth", f"row lost data: {parsed[0]}")
        expect(not (p.path / "INVENTORY.md").exists(), "markdown ledger is gone")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("inventory", "every exploded spec has exactly one row")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("auth", version=1, implemented=1)
        expect(p.run("check").returncode == 0, "spec with a row should pass")

        p.drop_row("auth")
        r = p.run("check")
        expect(r.returncode == 1, "an exploded spec with no ledger row must fail")
        expect("auth" in r.stdout, f"should name the subsystem:\n{r.stdout}")

        p.subsystem("auth", version=1, implemented=1)
        p.raw_inventory(
            "subsystem,spec,implemented,verify\n"
            f"auth,exploded-specs/auth.md,1,{OK_CMD}\n"
            f"auth,exploded-specs/auth.md,1,{OK_CMD}\n")
        r = p.run("check")
        expect(r.returncode == 1, "duplicate rows must fail")
        expect("duplicate" in r.stdout.lower(), f"should say duplicate:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("inventory", "malformed ledgers are reported with line numbers")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.raw_inventory("subsystem,spec,implemented\n")
        r = p.run("check")
        expect(r.returncode == 1, "missing column must fail")
        expect("verify" in r.stdout, f"should name the column:\n{r.stdout}")

        p.raw_inventory("subsystem,spec,implemented,verify\ntoo,few\n")
        r = p.run("check")
        expect(r.returncode == 1, "short row must fail")
        expect("2" in r.stdout, f"should give the line number:\n{r.stdout}")

        p.raw_inventory("")
        expect(p.run("check").returncode == 1, "empty ledger must fail")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("inventory", "status reports each subsystem's spec and implemented version")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("done", version=2, implemented=2)
        p.subsystem("lagging", version=3, implemented=1)
        p.subsystem("fresh", version=1, implemented="")

        r = p.run("status")
        expect(r.returncode == 0, f"status failed:\n{r.stderr}")
        for token in ("done", "lagging", "fresh", "built", "building", "planned"):
            expect(token in r.stdout, f"status missing {token!r}:\n{r.stdout}")
        line = next(l for l in r.stdout.splitlines() if "lagging" in l)
        expect("1" in line and "3" in line,
               f"lagging row should show both versions: {line!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
# checker
# ==========================================================================

@test("checker", "a spec ahead of its implementation is not a failure")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("auth", version=1, implemented=1)
        expect(p.run("check").returncode == 0, "caught-up subsystem passes")

        p.spec_version("auth", 2)
        r = p.run("check")
        expect(r.returncode == 0,
               f"a spec ahead of its code is work owed, not a failure:\n{r.stdout}")
        expect("DRIFT" not in r.stdout, f"should not report drift:\n{r.stdout}")

        p.implemented("auth", 2)
        expect(p.run("check").returncode == 0, "catching up stays clean")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("checker", "an implementation may not claim a version its spec lacks")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("auth", version=2, implemented=3)
        r = p.run("check")
        expect(r.returncode == 1, "implemented above spec version must fail")
        expect("2" in r.stdout and "3" in r.stdout,
               f"should name both versions:\n{r.stdout}")

        p.implemented("auth", 2)
        expect(p.run("check").returncode == 0, "equal versions are fine")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("checker", "an unverifiable subsystem cannot be implemented")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        for placeholder in ("", "-", "none", "TODO"):
            p.subsystem("auth", version=1, implemented=1, verify=placeholder)
            r = p.run("check")
            expect(r.returncode == 1, f"implemented with verify={placeholder!r} must fail")
            expect("unverifiable" in r.stdout or "no verify" in r.stdout,
                   f"should explain the rule:\n{r.stdout}")

        p.subsystem("auth", version=1, implemented="", verify="-")
        expect(p.run("check").returncode == 0,
               "an unimplemented subsystem may lack a command")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("checker", "verify commands must be single invocations")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        for bad in ("make test > out.txt", "a && b", "x ; y"):
            p.subsystem("auth", version=1, implemented=1, verify=bad)
            r = p.run("check")
            expect(r.returncode == 1, f"verify {bad!r} must be rejected")
            expect("metacharacter" in r.stdout, f"should name the reason:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("checker", "dangling and mismatched spec references are caught")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.raw_inventory("subsystem,spec,implemented,verify\n"
                        f"ghost,exploded-specs/ghost.md,1,{OK_CMD}\n")
        r = p.run("check")
        expect(r.returncode == 1, "dangling spec reference must fail")
        expect("does not exist" in r.stdout, f"should say missing:\n{r.stdout}")

        p.spec("auth", kind="exploded-spec", sub="exploded-specs")
        p.raw_inventory("subsystem,spec,implemented,verify\n"
                        f"other,exploded-specs/auth.md,1,{OK_CMD}\n")
        r = p.run("check")
        expect(r.returncode == 1, "row id must match the spec's id")
        expect("other" in r.stdout, f"should name the mismatch:\n{r.stdout}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
# verifier
# ==========================================================================

@test("verifier", "verify runs each implemented subsystem's command")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        bad = p.script("bad.py", 3)

        p.subsystem("good", version=1, implemented=1)
        r = p.run("verify")
        expect(r.returncode == 0, f"passing command should exit 0:\n{r.stdout}")
        expect("PASS" in r.stdout, f"should report PASS:\n{r.stdout}")

        p.subsystem("broken", version=1, implemented=1, verify=bad)
        r = p.run("verify")
        expect(r.returncode == 1, f"failing command must exit 1, got {r.returncode}")
        expect("FAIL" in r.stdout, f"should report FAIL:\n{r.stdout}")
        expect("broken" in r.stdout, "failure should be attributed")

        r = p.run("verify", "--id", "good")
        expect(r.returncode == 0 and "good" in r.stdout, "--id should target one row")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("verifier", "unimplemented subsystems are never executed")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("later", version=1, implemented="", verify=p.script("bad.py", 3))
        r = p.run("verify")
        expect(r.returncode == 0, f"planned rows must not run:\n{r.stdout}")
        expect("later" not in r.stdout, "planned rows should be skipped silently")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ==========================================================================
# navigator
# ==========================================================================

@test("navigator", "next reports loop, reason, blocker and action")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("auth", version=2, implemented=1)

        r = p.run("next")
        expect(r.returncode == 0, f"next must exit 0:\n{r.stderr}")
        for label in ("loop", "reason", "blocker", "action"):
            expect(label in r.stdout.lower(), f"missing {label!r}:\n{r.stdout}")

        r, d = p.next_json()
        expect(d is not None, f"--json must emit JSON:\n{r.stdout}")
        for key in ("loop", "reason", "blocker", "action", "rule"):
            expect(key in d, f"JSON missing {key!r}: {d}")
        expect(d["loop"].startswith("sprout-"), f"loop should name a skill: {d}")
        expect(isinstance(d["rule"], int), "rule should be the precedence number")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("navigator", "precedence is published and deterministic")
def _():
    p, tmp = project()
    try:
        # rule 4 - nothing at all
        _, d = p.next_json()
        expect(d["loop"] == "sprout-spec", f"empty project -> spec, got {d}")

        # rule 3 - an overview and no gaps
        p.spec("overview")
        p.subsystem("auth", version=1, implemented=1)
        _, d = p.next_json()
        expect(d["loop"] == "sprout-slice", f"no gaps -> slice, got {d}")

        # rule 2 - a gap is work owed
        p.spec_version("auth", 2)
        _, d = p.next_json()
        expect(d["loop"] == "sprout-build" and d["rule"] == 2,
               f"a gap -> build, got {d}")
        expect("auth" in d["blocker"], f"should name the subsystem: {d}")

        # rule 1 - structural failure outranks the queue
        p.raw_inventory("broken\n")
        _, d = p.next_json()
        expect(d["rule"] == 1, f"structural failure must be rule 1, got {d}")

        # determinism
        p.subsystem("auth", version=2, implemented=1)
        first = [p.next_json()[1] for _ in range(3)]
        expect(all(x == first[0] for x in first), f"must be deterministic: {first}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("navigator", "routing follows the version gaps")
def _():
    p, tmp = project()
    try:
        p.spec("overview")
        p.subsystem("auth", version=1, implemented=1)
        _, d = p.next_json()
        expect(d["loop"] == "sprout-slice", f"caught up -> slice, got {d}")

        p.spec_version("auth", 3)
        _, d = p.next_json()
        expect(d["loop"] == "sprout-build", f"spec ahead -> build, got {d}")

        p.implemented("auth", 3)
        _, d = p.next_json()
        expect(d["loop"] == "sprout-slice", f"caught up again -> slice, got {d}")
        expect("showcase" in d["action"].lower(),
               f"should still prompt for showcase: {d['action']!r}")

        # the gap was the only thing that changed: no document was touched
        p.slice_doc("s1")
        p.spec_version("auth", 4)
        _, d = p.next_json()
        expect(d["loop"] == "sprout-build",
               f"a bare slice document must not affect routing, got {d}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("navigator", "showcase is prompted only when something was delivered")
def _():
    p, tmp = project()
    try:
        # a brand new project has delivered nothing; prompting to showcase it
        # is nonsense and the first thing a new user would see
        p.spec("overview")
        _, d = p.next_json()
        expect(d["rule"] == 3, f"overview and no subsystems -> rule 3, got {d}")
        expect("showcase" not in d["action"].lower(),
               f"nothing is built, so showcase must not be prompted: {d['action']!r}")

        # once something is implemented, prompting for it is right
        p.subsystem("auth", version=1, implemented=1)
        _, d = p.next_json()
        expect(d["rule"] == 3, f"caught up -> rule 3, got {d}")
        expect("showcase" in d["action"].lower(),
               f"delivered work should prompt a showcase: {d['action']!r}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("navigator", "degenerate projects yield a position or a clear refusal")
def _():
    p, tmp = project()
    bare_tmp = tempfile.mkdtemp(prefix="sprout-bare-")
    try:
        r = subprocess.run(
            [sys.executable, str(p.path / ".sprout" / "sprout.py"), "next"],
            cwd=bare_tmp, capture_output=True, text=True)
        expect(r.returncode == 2, f"uninitialised project -> exit 2, got {r.returncode}")
        expect("invalid choice" not in r.stderr, "next subcommand must exist")
        expect(".sprout" in r.stderr, f"should name the marker:\n{r.stderr}")

        r, d = p.next_json()
        expect(r.returncode == 0, "empty project still has a position")
        expect(d["loop"] == "sprout-spec", f"empty -> spec, got {d}")

        (p.path / "INVENTORY.csv").unlink()
        r, d = p.next_json()
        expect(r.returncode == 0, f"missing ledger must not crash:\n{r.stderr}")
        expect(d is not None and d["rule"] == 1, f"should be rule 1, got {d}")
        expect(d["blocker"], "rule 1 must name a blocker")

        p._write()
        (p.path / "specs" / "broken.md").write_text("no frontmatter\n", encoding="utf-8")
        r, d = p.next_json()
        expect(r.returncode == 0, f"unparseable spec must not crash:\n{r.stderr}")
        expect(d["rule"] == 1, f"should be rule 1, got {d}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(bare_tmp, ignore_errors=True)


# ==========================================================================
# skills
# ==========================================================================

@test("skills", "every skill stays within the portable subset")
def _():
    skills_dir = ROOT / ".agents" / "skills"
    dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    expect(len(dirs) >= 6, f"expected at least 6 skills, found {len(dirs)}")

    for d in dirs:
        names = [q.name for q in d.iterdir() if q.name.lower() == "skill.md"]
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
               f"{d.name}: portable skills use only name and description, got {sorted(fm)}")
        expect(fm["name"] == d.name, f"{d.name}: name must match directory")
        expect(40 <= len(fm["description"]) <= 1024,
               f"{d.name}: description length {len(fm['description'])} out of range")
        expect(any(t in fm["description"] for t in ("Use when", "Use after", "Use whenever")),
               f"{d.name}: description must state a trigger condition")
        expect(len(lines) <= 500, f"{d.name}: {len(lines)} lines, over guidance")


# ==========================================================================
# distribution
# ==========================================================================

@test("distribution", "global install links skills so git pull is the update")
def _():
    home = Path(tempfile.mkdtemp(prefix="sprout-home-"))
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "install.py"), "--global", "--home", str(home)],
            capture_output=True, text=True)
        expect(r.returncode == 0, f"global install failed:\n{r.stdout}{r.stderr}")

        for agent_dir in (".claude/skills", ".agents/skills"):
            base = home / agent_dir
            expect(base.is_dir(), f"{agent_dir} was not created")
            for skill in ("sprout-spec", "sprout-slice", "sprout-build",
                          "sprout-tidy", "sprout-showcase", "sprout-spike"):
                link = base / skill
                expect(link.is_symlink(),
                       f"{agent_dir}/{skill} must be a symlink, so git pull updates it")
                expect(link.resolve() == (ROOT / ".agents" / "skills" / skill).resolve(),
                       f"{agent_dir}/{skill} points at {link.resolve()}, not the repo")
                expect((link / "SKILL.md").exists(),
                       f"{agent_dir}/{skill} does not resolve to a skill")

        # idempotent: a second run changes nothing and still succeeds
        r2 = subprocess.run(
            [sys.executable, str(ROOT / "install.py"), "--global", "--home", str(home)],
            capture_output=True, text=True)
        expect(r2.returncode == 0, f"re-run failed:\n{r2.stdout}{r2.stderr}")
        expect("current" in r2.stdout.lower() or "skip" in r2.stdout.lower(),
               f"re-run should report links as already current:\n{r2.stdout}")

        # never clobber something a user put there
        foreign = home / ".claude" / "skills" / "sprout-spec"
        foreign.unlink()
        foreign.mkdir()
        (foreign / "SKILL.md").write_text("mine\n", encoding="utf-8")
        r3 = subprocess.run(
            [sys.executable, str(ROOT / "install.py"), "--global", "--home", str(home)],
            capture_output=True, text=True)
        expect((foreign / "SKILL.md").read_text(encoding="utf-8") == "mine\n",
               "an existing directory must never be clobbered")
        expect("sprout-spec" in r3.stdout, f"should report the conflict:\n{r3.stdout}")

        # global mode must not touch the project-install paths
        expect(not (home / "INVENTORY.csv").exists(),
               "--global must not create project state")
        expect(not (home / ".sprout").exists(),
               "--global must not vendor the tool; that is per project")
    finally:
        shutil.rmtree(home, ignore_errors=True)


@test("distribution", "install bootstraps a working project")
def _():
    tmp = tempfile.mkdtemp(prefix="sprout-install-")
    try:
        target = Path(tmp) / "newproj"
        r = subprocess.run([sys.executable, str(ROOT / "install.py"), str(target)],
                           capture_output=True, text=True)
        expect(r.returncode == 0, f"install failed:\n{r.stdout}{r.stderr}")

        for rel in (".sprout/sprout.py", ".agents/skills/sprout-build/SKILL.md",
                    "INVENTORY.csv", "AGENTS.md", "specs", "verify"):
            expect((target / rel).exists(), f"install did not create {rel}")

        header = (target / "INVENTORY.csv").read_text(encoding="utf-8").strip()
        expect(header == ",".join(INV_COLUMNS),
               f"ledger header should be the subsystem schema, got {header!r}")

        claude = target / ".claude" / "skills"
        expect((claude / "sprout-build" / "SKILL.md").exists(),
               ".claude/skills does not resolve to the skills")

        agents = (target / "AGENTS.md").read_text(encoding="utf-8")
        expect("<!--" not in agents and "-->" not in agents,
               f"AGENTS.md still contains comment markup:\n{agents[:300]}")
        expect("sprout.py next" in agents,
               "AGENTS.md should tell a resuming agent to ask where it is")

        def sp(*a):
            return subprocess.run(
                [sys.executable, str(target / ".sprout" / "sprout.py"), *a],
                cwd=target, capture_output=True, text=True)
        expect(sp("check").returncode == 0, f"fresh install should pass check:\n{sp('check').stdout}")
        expect(sp("status").returncode == 0, "fresh install should report status")
        expect(sp("next").returncode == 0, "fresh install should report a position")

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


# --------------------------------------------------------------------------

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--list":
        for sub, tests in TESTS.items():
            print(f"{sub}  ({len(tests)})")
            for name, _ in tests:
                print(f"    {name}")
        return 0

    if argv[0] == "--all":
        groups = list(TESTS.items())
    elif argv[0] in TESTS:
        groups = [(argv[0], TESTS[argv[0]])]
    else:
        print(f"unknown subsystem: {argv[0]}", file=sys.stderr)
        print(f"known: {', '.join(TESTS)}", file=sys.stderr)
        return 2

    failures = total = 0
    for sub, tests in groups:
        for name, fn in tests:
            total += 1
            label = f"{sub}: {name}"
            try:
                fn()
                print(f"ok    {label}")
            except AssertionError as exc:
                print(f"FAIL  {label}\n      {exc}")
                failures += 1
            except Exception as exc:  # noqa: BLE001 - a broken test is a failure
                print(f"ERROR {label}\n      {type(exc).__name__}: {exc}")
                failures += 1

    if total > 1:
        print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
