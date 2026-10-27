#!/usr/bin/env python3
"""sprout - deterministic checks for spec-driven, slice-based delivery.

Stdlib only. Python 3.9+. Cross-platform.

Core rule: if a subsystem cannot be verified deterministically and
programmatically, it is not implemented. This tool is what makes that rule
enforceable rather than aspirational.

The ledger records subsystem evolution: what each spec says now, which version
the implementation satisfies, and how that is checked. The gap between the two
is work owed - the queue, not a fault.

    sprout check            validate specs and the ledger for consistency
    sprout verify [--id X]  run verify commands for implemented subsystems
    sprout status           each subsystem's spec, implementation and state
    sprout next             which loop you are in and what is blocking it
    sprout new KIND NAME    scaffold a spec / slice / exploded-spec / spike
"""

import argparse
import csv
import datetime as _dt
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

SPEC_KINDS = ("spec", "exploded-spec", "slice", "spike")
INVENTORY_COLS = ("subsystem", "spec", "implemented", "verify")

# Documents that describe intent carry an editorial status. A slice carries
# none, and names no subsystems: both are derived, because progress is a fact
# about how far the code has caught up with the specs.
EDITORIAL_STATUSES = ("draft", "active", "superseded")
STATUSES_BY_KIND = {
    "spec": EDITORIAL_STATUSES,
    "exploded-spec": EDITORIAL_STATUSES,
    "spike": EDITORIAL_STATUSES,
}

PLACEHOLDERS = ("", "-", "none", "todo", "tbd")
SHELL_META = set("|><;&$`\n")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = RESET = ""


def die(msg):
    print(f"{RED}sprout: {msg}{RESET}", file=sys.stderr)
    raise SystemExit(2)


def find_root(start=None):
    """Project root is the nearest ancestor containing .sprout/."""
    cur = (start or Path.cwd()).resolve()
    for cand in (cur, *cur.parents):
        if (cand / ".sprout").is_dir():
            return cand
    die("no .sprout/ directory found in this directory or any parent")


# --------------------------------------------------------------------------
# frontmatter: deliberately a flat key:value subset, so no YAML dep is needed
# --------------------------------------------------------------------------

def parse_frontmatter(path):
    """Return (dict, errors). Only flat 'key: value' pairs are supported."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, [f"unreadable: {exc}"]

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["missing YAML frontmatter (file must open with '---')"]

    data, errors = {}, []
    for idx, raw in enumerate(lines[1:], start=2):
        if raw.strip() == "---":
            return data, errors
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            errors.append(f"line {idx}: not a 'key: value' pair")
            continue
        key, _, val = raw.partition(":")
        if key != key.strip():
            errors.append(f"line {idx}: nested keys are not supported")
            continue
        data[key.strip()] = val.strip().strip('"').strip("'")
    errors.append("frontmatter is not terminated by '---'")
    return data, errors


def spec_files(root):
    for sub in ("specs", "exploded-specs", "slices", "spikes"):
        d = root / sub
        if d.is_dir():
            for p in sorted(d.rglob("*.md")):
                yield p


# --------------------------------------------------------------------------
# the ledger
# --------------------------------------------------------------------------

def inventory_path(root):
    return root / "INVENTORY.csv"


def parse_inventory(root):
    """Return (rows, errors). One row per subsystem, stored as CSV: the ledger
    is structured data, and stdlib quoting keeps hand-editing safe."""
    path = inventory_path(root)
    if not path.exists():
        return [], ["INVENTORY.csv not found at project root"]

    rows, errors = [], []
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            try:
                header = [c.strip().lower() for c in next(reader)]
            except StopIteration:
                return [], ["INVENTORY.csv is empty; expected a header row"]

            missing = [c for c in INVENTORY_COLS if c not in header]
            if missing:
                return [], [f"INVENTORY.csv: missing column(s): {', '.join(missing)}"]

            for cells in reader:
                lineno = reader.line_num
                if not any(c.strip() for c in cells):
                    continue
                if len(cells) != len(header):
                    errors.append(
                        f"INVENTORY.csv line {lineno}: {len(cells)} field(s) "
                        f"but the header has {len(header)}")
                    continue
                row = {k: v.strip() for k, v in zip(header, cells)}
                row["_line"] = lineno
                row["verify"] = row["verify"].strip().strip("`").strip()
                rows.append(row)
    except (OSError, csv.Error) as exc:
        errors.append(f"INVENTORY.csv: {exc}")

    return rows, errors


def write_inventory(root, rows):
    with inventory_path(root).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(INVENTORY_COLS)
        for r in rows:
            w.writerow([r[c] for c in INVENTORY_COLS])


def is_placeholder(cmd):
    return cmd.strip().lower() in PLACEHOLDERS


# --------------------------------------------------------------------------
# collect: every fact the checker, navigator and reporters need
# --------------------------------------------------------------------------

def collect(root):
    """Pure. Gathers facts and consistency problems; never reports a gap
    between spec and implementation as a problem, because that is the queue."""
    problems, notes = [], []
    versions, spec_ids = {}, {}
    specs_seen = 0
    has_overview = False

    for path in spec_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        fm, fm_errors = parse_frontmatter(path)
        for err in fm_errors:
            problems.append(f"{rel}: {err}")
        if not fm:
            continue
        specs_seen += 1

        required = ("id", "kind", "version")
        if fm.get("kind") != "slice":
            required += ("status",)
        for field in required:
            if field not in fm:
                problems.append(f"{rel}: frontmatter missing required field '{field}'")

        kind = fm.get("kind")
        if kind and kind not in SPEC_KINDS:
            problems.append(f"{rel}: kind '{kind}' is not one of {', '.join(SPEC_KINDS)}")
        if kind == "spec":
            has_overview = True
        if kind == "slice" and "status" in fm:
            problems.append(
                f"{rel}: a slice declares no status - its state is derived from "
                f"how far the subsystems have caught up with their specs. "
                f"Remove the field.")
        if "status" in fm and kind in STATUSES_BY_KIND:
            valid = STATUSES_BY_KIND[kind]
            if fm["status"] not in valid:
                problems.append(
                    f"{rel}: status '{fm['status']}' is not valid for kind "
                    f"'{kind}' (expected one of {', '.join(valid)})")
        if "id" in fm:
            if not ID_RE.match(fm["id"]):
                problems.append(f"{rel}: id '{fm['id']}' must be lowercase-hyphenated")
            if fm["id"] != path.stem:
                problems.append(
                    f"{rel}: id '{fm['id']}' does not match filename stem '{path.stem}'")
            spec_ids[rel] = fm["id"]
        if "version" in fm:
            if not fm["version"].isdigit() or int(fm["version"]) < 1:
                problems.append(
                    f"{rel}: version '{fm['version']}' must be a positive integer")
            else:
                versions[rel] = int(fm["version"])

    # --- the ledger ------------------------------------------------------
    rows, inv_errors = parse_inventory(root)
    problems.extend(inv_errors)

    subsystems, seen = {}, {}
    for row in rows:
        at = f"INVENTORY.csv:{row['_line']}"
        name = row["subsystem"]

        if not name:
            problems.append(f"{at}: row has no subsystem name")
            continue
        if not ID_RE.match(name):
            problems.append(f"{at}: subsystem '{name}' must be lowercase-hyphenated")
        if name in seen:
            problems.append(
                f"{at}: duplicate subsystem '{name}' (first seen line {seen[name]})")
            continue
        seen[name] = row["_line"]

        spec_ref = row["spec"]
        spec_version = None
        if not spec_ref:
            problems.append(f"{at}: '{name}' has no spec reference")
        elif spec_ref not in versions:
            if (root / spec_ref).exists():
                problems.append(f"{at}: '{name}' spec '{spec_ref}' has no readable version")
            else:
                problems.append(f"{at}: '{name}' spec '{spec_ref}' does not exist")
        else:
            spec_version = versions[spec_ref]
            if spec_ids.get(spec_ref) != name:
                problems.append(
                    f"{at}: '{name}' does not match the id '{spec_ids.get(spec_ref)}' "
                    f"of the spec it names")

        impl_raw = row["implemented"].strip()
        impl = None
        if impl_raw:
            if not impl_raw.isdigit() or int(impl_raw) < 1:
                problems.append(
                    f"{at}: '{name}' implemented '{impl_raw}' must be blank or a "
                    f"positive integer")
            else:
                impl = int(impl_raw)
                if spec_version is not None and impl > spec_version:
                    problems.append(
                        f"{at}: '{name}' claims to implement v{impl} but its spec is "
                        f"only at v{spec_version}; an implementation cannot satisfy a "
                        f"version its spec does not have")

        verify = row["verify"]
        if impl is not None and is_placeholder(verify):
            problems.append(
                f"{at}: '{name}' is implemented with no verify command - "
                f"unverifiable means not implemented")
        elif not is_placeholder(verify) and SHELL_META & set(verify):
            problems.append(
                f"{at}: '{name}' verify command contains shell metacharacters; "
                f"wrap it in a script or make target instead")

        if spec_version is None:
            state = "planned"
        elif impl is None:
            state = "planned"
        elif impl < spec_version:
            state = "building"
        else:
            state = "built"

        subsystems[name] = {
            "spec": spec_ref,
            "spec_version": spec_version,
            "implemented": impl,
            "verify": verify,
            "state": state,
            "line": row["_line"],
        }

    # every exploded spec must appear exactly once, or work could be owed
    # that nothing reports
    for rel, sid in sorted(spec_ids.items()):
        if rel.startswith("exploded-specs/") and sid not in subsystems:
            problems.append(
                f"{rel}: subsystem '{sid}' has no row in INVENTORY.csv, so any "
                f"work it owes would go unreported")

    # --- skills ----------------------------------------------------------
    for skills_dir in (root / ".agents" / "skills", root / ".claude" / "skills"):
        if not skills_dir.is_dir() or skills_dir.is_symlink():
            continue
        for child in sorted(skills_dir.iterdir()):
            if not child.is_dir():
                continue
            canonical = child / "SKILL.md"
            actual = [p for p in child.iterdir() if p.name.lower() == "skill.md"]
            if not actual:
                problems.append(f"{child.relative_to(root)}: no SKILL.md")
                continue
            if not canonical.exists():
                problems.append(
                    f"{actual[0].relative_to(root)}: must be named exactly 'SKILL.md' - "
                    f"case-sensitive filesystems ignore other spellings")
                continue
            fm, _ = parse_frontmatter(canonical)
            if "name" not in fm or "description" not in fm:
                problems.append(
                    f"{canonical.relative_to(root)}: frontmatter needs both "
                    f"'name' and 'description'")
                continue
            if fm["name"] != child.name:
                problems.append(
                    f"{canonical.relative_to(root)}: name '{fm['name']}' must match "
                    f"directory '{child.name}'")
            if len(fm["description"]) > 1024:
                problems.append(f"{canonical.relative_to(root)}: description over 1024 chars")
            if len(canonical.read_text(encoding="utf-8").splitlines()) > 500:
                notes.append(
                    f"{canonical.relative_to(root)}: over 500 lines; move detail "
                    f"into references/ (progressive disclosure)")

    return {
        "structural": problems,
        "notes": notes,
        "rows": rows,
        "subsystems": subsystems,
        "specs_seen": specs_seen,
        "has_overview": has_overview,
    }


def gaps(facts):
    """Subsystems whose implementation lags their spec. This is the queue."""
    return {n: s for n, s in facts["subsystems"].items()
            if s["state"] in ("planned", "building")}


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def cmd_check(root, args):
    facts = collect(root)
    for note in facts["notes"]:
        print(f"{YELLOW}warn{RESET}  {note}")

    if facts["structural"]:
        for problem in facts["structural"]:
            print(f"{RED}FAIL{RESET}  {problem}")
        print(f"\n{RED}check failed{RESET}: {len(facts['structural'])} problem(s) "
              f"across {facts['specs_seen']} spec(s) and "
              f"{len(facts['rows'])} subsystem(s)")
        return 1

    owed = gaps(facts)
    summary = (f"{GREEN}OK{RESET}    {facts['specs_seen']} spec(s) versioned, "
               f"{len(facts['subsystems'])} subsystem(s) consistent")
    if owed:
        summary += f", {len(owed)} with work owed"
    print(summary)
    return 0


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------

def cmd_verify(root, args):
    facts = collect(root)
    if facts["structural"] and not facts["subsystems"]:
        for err in facts["structural"]:
            print(f"{RED}FAIL{RESET}  {err}")
        return 2

    targets = {n: s for n, s in facts["subsystems"].items()
               if s["implemented"] is not None}
    if args.id:
        if args.id not in targets:
            die(f"no implemented subsystem named '{args.id}'")
        targets = {args.id: targets[args.id]}

    if not targets:
        print(f"{YELLOW}nothing to verify{RESET}: no subsystem is implemented yet")
        return 0

    failed = []
    for name in sorted(targets):
        info = targets[name]
        cmd = info["verify"]
        if is_placeholder(cmd):
            print(f"{RED}FAIL{RESET}  {name}: implemented with no verify command")
            failed.append(name)
            continue
        try:
            argv = shlex.split(cmd, posix=(sys.platform != "win32"))
        except ValueError as exc:
            print(f"{RED}FAIL{RESET}  {name}: unparseable verify command ({exc})")
            failed.append(name)
            continue

        proc = subprocess.run(argv, cwd=root, capture_output=True, text=True, shell=False)
        at = f"v{info['implemented']}"
        if proc.returncode == 0:
            print(f"{GREEN}PASS{RESET}  {name} {DIM}{at}  {cmd}{RESET}")
        else:
            print(f"{RED}FAIL{RESET}  {name} {DIM}{at}  {cmd}{RESET} "
                  f"(exit {proc.returncode})")
            for line in (proc.stdout + proc.stderr).strip().splitlines()[-15:]:
                print(f"        {line}")
            failed.append(name)

    print()
    if failed:
        print(f"{RED}{len(failed)} of {len(targets)} failed{RESET}: {', '.join(failed)}")
        return 1
    print(f"{GREEN}all {len(targets)} verified{RESET}")
    return 0


# --------------------------------------------------------------------------
# status
# --------------------------------------------------------------------------

def cmd_status(root, args):
    facts = collect(root)
    subs = facts["subsystems"]
    if not subs:
        if facts["structural"]:
            for err in facts["structural"]:
                print(f"{RED}FAIL{RESET}  {err}")
            return 2
        print(f"{YELLOW}no subsystems in the ledger yet{RESET}")
        return 0

    width = max(len(n) for n in subs) + 2
    print("SUBSYSTEMS")
    for name in sorted(subs):
        s = subs[name]
        spec_v = "?" if s["spec_version"] is None else f"v{s['spec_version']}"
        impl_v = "-" if s["implemented"] is None else f"v{s['implemented']}"
        colour = {"built": GREEN, "building": YELLOW, "planned": DIM}[s["state"]]
        print(f"  {name:<{width}} spec {spec_v:<5} impl {impl_v:<5} "
              f"{colour}{s['state']}{RESET}")

    owed = gaps(facts)
    done = len(subs) - len(owed)
    print(f"\n{done}/{len(subs)} subsystems caught up with their specs")
    if owed:
        print(f"{YELLOW}work owed{RESET}: {', '.join(sorted(owed))}")
    return 0


# --------------------------------------------------------------------------
# next
# --------------------------------------------------------------------------

def resolve_position(root, facts):
    """Resolve the current loop by fixed precedence; first match wins.

    Four rules, because the flow is one-way. A slice does not declare which
    subsystems it touches: updating an exploded spec is that declaration, and
    the resulting gap is what gets read here.
    """
    def at(rule, loop, reason, blocker, action):
        return {"rule": rule, "loop": loop, "reason": reason,
                "blocker": blocker, "action": action}

    if facts["structural"]:
        n = len(facts["structural"])
        return at(1, "repair",
                  f"{n} structural problem(s) in the specs or ledger",
                  facts["structural"][0],
                  "Run 'sprout check' and fix what it reports. No loop can "
                  "proceed on a project that cannot be parsed.")

    owed = gaps(facts)
    if owed:
        names = sorted(owed)
        detail = ", ".join(
            f"{n} (spec v{owed[n]['spec_version']}, "
            f"implemented {'none' if owed[n]['implemented'] is None else 'v' + str(owed[n]['implemented'])})"
            for n in names[:3])
        return at(2, "sprout-build",
                  f"{len(owed)} subsystem(s) behind their specs",
                  detail,
                  "Write the black-box tests for the specced behaviour, confirm "
                  "each fails in the code under test, then implement. Raise "
                  "'implemented' only after re-verifying.")

    if facts["has_overview"]:
        return at(3, "sprout-slice",
                  "an overview spec exists and every subsystem is caught up",
                  "no subsystem is behind its spec",
                  "Showcase the delivered work if you have not already, then "
                  "define the next slice and update the specs it requires.")

    return at(4, "sprout-spec",
              "no overview spec exists yet",
              "specs/ contains no document of kind 'spec'",
              "Write the overview spec: goals, non-goals, subsystems, "
              "constraints and invariants.")


def cmd_next(root, args):
    facts = collect(root)
    pos = resolve_position(root, facts)

    if args.json:
        print(json.dumps(pos, indent=2))
        return 0

    colour = RED if pos["rule"] == 1 else GREEN
    print(f"{DIM}rule{RESET}     {pos['rule']}")
    print(f"{DIM}loop{RESET}     {colour}{pos['loop']}{RESET}")
    print(f"{DIM}reason{RESET}   {pos['reason']}")
    print(f"{DIM}blocker{RESET}  {pos['blocker']}")
    print(f"{DIM}action{RESET}   {pos['action']}")
    if pos["loop"] == "sprout-build":
        print(f"\n{DIM}note     position within the build loop (tests vs "
              f"implementation) is not derivable from artifacts{RESET}")
    return 0


# --------------------------------------------------------------------------
# new
# --------------------------------------------------------------------------

DEST = {
    "spec": "specs",
    "exploded-spec": "exploded-specs",
    "slice": "slices",
    "spike": "spikes",
}


def cmd_new(root, args):
    kind, name = args.kind, args.name
    if not ID_RE.match(name):
        die(f"name '{name}' must be lowercase-hyphenated (a-z, 0-9, -)")

    template = root / ".sprout" / "templates" / f"{kind}.md"
    if not template.exists():
        die(f"no template at {template.relative_to(root)}")

    out_dir = root / DEST[kind]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.md"
    if out.exists():
        die(f"{out.relative_to(root)} already exists")

    body = template.read_text(encoding="utf-8")
    body = body.replace("{{id}}", name)
    body = body.replace("{{title}}", name.replace("-", " ").title())
    body = body.replace("{{date}}", _dt.date.today().isoformat())
    out.write_text(body, encoding="utf-8")
    print(f"{GREEN}created{RESET} {out.relative_to(root)}")

    # An exploded spec must appear in the ledger, or the project is left
    # failing its own checks the moment it is scaffolded.
    if kind == "exploded-spec":
        rows, errors = parse_inventory(root)
        if errors:
            print(f"{YELLOW}warn{RESET}    could not add a ledger row: {errors[0]}")
            return 0
        if any(r["subsystem"] == name for r in rows):
            return 0
        rows.append({"subsystem": name, "spec": f"exploded-specs/{name}.md",
                     "implemented": "", "verify": "-"})
        write_inventory(root, rows)
        print(f"{GREEN}added{RESET}   INVENTORY.csv row for '{name}' "
              f"{DIM}(set its verify command before implementing){RESET}")
    return 0


# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(prog="sprout", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="validate specs and the ledger for consistency")

    p_verify = sub.add_parser("verify", help="run verify commands for implemented subsystems")
    p_verify.add_argument("--id", help="verify a single subsystem")

    sub.add_parser("status", help="each subsystem's spec, implementation and state")

    p_next = sub.add_parser("next", help="which loop you are in and what blocks it")
    p_next.add_argument("--json", action="store_true", help="emit the position as JSON")

    p_new = sub.add_parser("new", help="scaffold a document from a template")
    p_new.add_argument("kind", choices=sorted(DEST))
    p_new.add_argument("name")

    args = parser.parse_args(argv)
    root = find_root()
    return {
        "check": cmd_check,
        "verify": cmd_verify,
        "status": cmd_status,
        "next": cmd_next,
        "new": cmd_new,
    }[args.cmd](root, args)


if __name__ == "__main__":
    raise SystemExit(main())
