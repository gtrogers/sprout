#!/usr/bin/env python3
"""sprout - deterministic checks for spec-driven, slice-based delivery.

Stdlib only. Python 3.9+. Cross-platform.

Core rule: if a capability cannot be verified deterministically and
programmatically, it does not exist. This tool is what makes that rule
enforceable rather than aspirational.

    sprout check            validate specs + inventory, report drift
    sprout verify [--id X]  run verify commands for built capabilities
    sprout status           what is built, building, planned
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
STATUSES = ("planned", "building", "built")

# Documents that describe intent carry an editorial status. A slice carries
# none: its state is derived from the inventory rows that name it, because
# progress is a fact about delivered capabilities rather than a claim.
EDITORIAL_STATUSES = ("draft", "active", "superseded")
STATUSES_BY_KIND = {
    "spec": EDITORIAL_STATUSES,
    "exploded-spec": EDITORIAL_STATUSES,
    "spike": EDITORIAL_STATUSES,
}
INVENTORY_COLS = ("id", "capability", "slice", "status", "spec", "ver", "verify")
SHELL_META = set("|><;&$`\n")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = RESET = ""


# --------------------------------------------------------------------------
# project discovery
# --------------------------------------------------------------------------

def find_root(start=None):
    """Project root is the nearest ancestor containing .sprout/."""
    cur = (start or Path.cwd()).resolve()
    for cand in (cur, *cur.parents):
        if (cand / ".sprout").is_dir():
            return cand
    die("no .sprout/ directory found in this directory or any parent")


def die(msg):
    print(f"{RED}sprout: {msg}{RESET}", file=sys.stderr)
    raise SystemExit(2)


# --------------------------------------------------------------------------
# frontmatter: deliberately a flat key:value subset, so no YAML dep is needed
# --------------------------------------------------------------------------

def parse_frontmatter(path):
    """Return (dict, errors). Only flat 'key: value' pairs are supported."""
    errors = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, [f"unreadable: {exc}"]

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["missing YAML frontmatter (file must open with '---')"]

    data = {}
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
            errors.append(f"line {idx}: nested keys are not supported in sprout frontmatter")
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
# inventory: a markdown table, so it stays readable by humans
# --------------------------------------------------------------------------

def parse_inventory(root):
    """Return (rows, errors). The ledger is CSV: structured data, stored as
    such. Quoting is handled by the stdlib, so a capability description may
    contain commas, quotes or apostrophes without hand-escaping."""
    path = root / "INVENTORY.csv"
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
                return [], [
                    f"INVENTORY.csv: table is missing column(s): {', '.join(missing)}"
                ]

            for cells in reader:
                lineno = reader.line_num
                if not any(c.strip() for c in cells):
                    continue
                if len(cells) != len(header):
                    errors.append(
                        f"INVENTORY.csv line {lineno}: {len(cells)} field(s) "
                        f"but the header has {len(header)}"
                    )
                    continue
                row = {k: v.strip() for k, v in zip(header, cells)}
                row["_line"] = lineno
                row["verify"] = row["verify"].strip().strip("`").strip()
                rows.append(row)
    except (OSError, csv.Error) as exc:
        errors.append(f"INVENTORY.csv: {exc}")

    return rows, errors


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def parse_slice_subsystems(path):
    """Exploded-spec paths referenced by a slice's 'Subsystems touched' table."""
    refs, inside = [], False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return refs
    for raw in lines:
        s = raw.strip()
        if s.startswith("## "):
            inside = s.lower().startswith("## subsystems touched")
            continue
        if inside and s.startswith("|"):
            for m in re.finditer(r"(exploded-specs/[A-Za-z0-9_\-.]+\.md)", s):
                if m.group(1) not in refs:
                    refs.append(m.group(1))
    return refs


def derive_slice_states(slices, rows):
    """A slice's state is computed, never declared: 'building' if any row is
    building, 'built' once every row is built, 'planned' otherwise."""
    states = {}
    for s in slices:
        mine = [r for r in rows if r.get("slice") == s["id"]]
        if any(r["status"].lower() == "building" for r in mine):
            state = "building"
        elif mine and all(r["status"].lower() == "built" for r in mine):
            state = "built"
        else:
            state = "planned"
        states[s["id"]] = {"state": state, "rows": mine}
    return states


def collect(root):
    """Gather every fact the Checker and Navigator need. Pure; no output.

    Structural problems and drift are kept apart because the Navigator ranks
    them differently: an unparseable project has no trustworthy position at
    all, whereas a drifted one has a position and a clear way out.
    """
    problems = []
    drift = []
    notes = []
    slices = []
    has_overview = False

    # --- specs -----------------------------------------------------------
    versions = {}
    specs_seen = 0
    for path in spec_files(root):
        rel = path.relative_to(root)
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

        if fm.get("kind") == "slice" and "status" in fm:
            problems.append(
                f"{rel}: a slice declares no status - its state is derived from "
                f"the inventory rows naming it. Remove the field."
            )

        if "kind" in fm and fm["kind"] not in SPEC_KINDS:
            problems.append(
                f"{rel}: kind '{fm['kind']}' is not one of {', '.join(SPEC_KINDS)}"
            )
        if "id" in fm:
            if not ID_RE.match(fm["id"]):
                problems.append(f"{rel}: id '{fm['id']}' must be lowercase-hyphenated")
            if fm["id"] != path.stem:
                problems.append(
                    f"{rel}: id '{fm['id']}' does not match filename stem '{path.stem}'"
                )
        if fm.get("kind") == "spec":
            has_overview = True
        if fm.get("kind") == "slice":
            slices.append({
                "id": fm.get("id", path.stem),
                "path": str(rel).replace("\\", "/"),
                "subsystems": parse_slice_subsystems(path),
            })

        if "status" in fm and fm.get("kind") in STATUSES_BY_KIND:
            valid = STATUSES_BY_KIND[fm["kind"]]
            if fm["status"] not in valid:
                problems.append(
                    f"{rel}: status '{fm['status']}' is not valid for kind "
                    f"'{fm['kind']}' (expected one of {', '.join(valid)})"
                )

        if "version" in fm:
            if not fm["version"].isdigit():
                problems.append(
                    f"{rel}: version '{fm['version']}' must be a positive integer"
                )
            else:
                versions[str(rel).replace("\\", "/")] = int(fm["version"])

    # --- inventory -------------------------------------------------------
    rows, inv_errors = parse_inventory(root)
    problems.extend(inv_errors)

    seen_ids = {}
    for row in rows:
        at = f"INVENTORY.csv:{row['_line']}"
        rid = row["id"]

        if not rid:
            problems.append(f"{at}: row has an empty ID")
        elif not ID_RE.match(rid):
            problems.append(f"{at}: ID '{rid}' must be lowercase-hyphenated")
        if rid in seen_ids:
            problems.append(f"{at}: duplicate ID '{rid}' (first seen line {seen_ids[rid]})")
        else:
            seen_ids[rid] = row["_line"]

        if not row["capability"]:
            problems.append(f"{at}: '{rid}' has no capability description")

        status = row["status"].lower()
        if status not in STATUSES:
            problems.append(
                f"{at}: '{rid}' status '{row['status']}' is not one of {', '.join(STATUSES)}"
            )

        slice_ref = row["slice"]
        if not slice_ref:
            problems.append(f"{at}: '{rid}' names no slice")
        elif not (root / "slices" / f"{slice_ref}.md").exists():
            problems.append(
                f"{at}: '{rid}' names slice '{slice_ref}', which does not exist "
                f"at slices/{slice_ref}.md"
            )

        # spec reference must resolve, and the pinned version must match
        spec_ref = row["spec"].strip().strip("`")
        spec_ref = re.sub(r"^\[.*?\]\((.*?)\)$", r"\1", spec_ref)
        if not spec_ref:
            problems.append(f"{at}: '{rid}' has no spec reference")
        elif spec_ref not in versions:
            if (root / spec_ref).exists():
                problems.append(f"{at}: '{rid}' spec '{spec_ref}' has no readable version")
            else:
                problems.append(f"{at}: '{rid}' spec '{spec_ref}' does not exist")
        elif row["ver"].isdigit():
            pinned, actual = int(row["ver"]), versions[spec_ref]
            if pinned != actual:
                drift.append(
                    f"{at}: '{rid}' DRIFT - pinned to {spec_ref} v{pinned} "
                    f"but that spec is now v{actual}; re-verify and re-pin, or revert"
                )
        else:
            problems.append(f"{at}: '{rid}' ver '{row['ver']}' must be a positive integer")

        # the central rule: built means verifiable
        verify = row["verify"]
        if status == "built":
            if not verify or verify in ("-", "none", "TODO"):
                problems.append(
                    f"{at}: '{rid}' is marked built with no verify command - "
                    f"unverifiable capabilities do not exist"
                )
            elif SHELL_META & set(verify):
                problems.append(
                    f"{at}: '{rid}' verify command contains shell metacharacters; "
                    f"wrap it in a script or make target instead"
                )
        elif verify and verify not in ("-", "none", "TODO") and SHELL_META & set(verify):
            problems.append(f"{at}: '{rid}' verify command contains shell metacharacters")

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
                    f"case-sensitive filesystems ignore other spellings"
                )
                continue
            fm, _ = parse_frontmatter(canonical)
            if "name" not in fm or "description" not in fm:
                problems.append(
                    f"{canonical.relative_to(root)}: frontmatter needs both "
                    f"'name' and 'description'"
                )
                continue
            if fm["name"] != child.name:
                problems.append(
                    f"{canonical.relative_to(root)}: name '{fm['name']}' "
                    f"must match directory '{child.name}'"
                )
            if len(fm["description"]) > 1024:
                problems.append(f"{canonical.relative_to(root)}: description exceeds 1024 chars")
            body = canonical.read_text(encoding="utf-8").splitlines()
            if len(body) > 500:
                notes.append(
                    f"{canonical.relative_to(root)}: {len(body)} lines; "
                    f"move detail into references/ (progressive disclosure)"
                )

    return {
        "slice_states": derive_slice_states(slices, rows),
        "structural": problems,
        "drift": drift,
        "notes": notes,
        "rows": rows,
        "slices": slices,
        "specs_seen": specs_seen,
        "has_overview": has_overview,
    }


def cmd_check(root, args):
    facts = collect(root)
    for note in facts["notes"]:
        print(f"{YELLOW}warn{RESET}  {note}")

    failures = facts["structural"] + facts["drift"]
    if failures:
        for problem in failures:
            print(f"{RED}FAIL{RESET}  {problem}")
        print(
            f"\n{RED}check failed{RESET}: {len(failures)} problem(s) "
            f"across {facts['specs_seen']} spec(s) and "
            f"{len(facts['rows'])} inventory row(s)"
        )
        return 1
    print(
        f"{GREEN}OK{RESET}    {facts['specs_seen']} spec(s) versioned, "
        f"{len(facts['rows'])} inventory row(s) consistent, no drift"
    )
    return 0


# --------------------------------------------------------------------------
# next: where am I, and what is blocking the transition out of here
# --------------------------------------------------------------------------

def resolve_position(root, facts):
    """Resolve the current loop by fixed precedence; first match wins.

    The ordering carries the design. Rule 1 outranks everything because a
    project that cannot be parsed has no trustworthy position. Rule 2 outranks
    progress because building on a drifted spec is how specs become fiction.
    """
    rows = facts["rows"]
    slices = facts["slices"]

    def at(rule, loop, reason, blocker, action):
        return {"rule": rule, "loop": loop, "reason": reason,
                "blocker": blocker, "action": action}

    if facts["structural"]:
        n = len(facts["structural"])
        return at(1, "repair",
                  f"{n} structural problem(s) in the specs or inventory",
                  facts["structural"][0],
                  "Run 'sprout check' and fix what it reports. No loop can "
                  "proceed on a project that cannot be parsed.")

    if facts["drift"]:
        n = len(facts["drift"])
        return at(2, "sprout-tidy",
                  f"{n} inventory row(s) pinned to a stale spec version",
                  facts["drift"][0],
                  "Re-verify each drifted capability and re-pin it, or revert "
                  "the spec change. Never re-pin a row you have not re-verified.")

    building = [r for r in rows if r["status"].lower() == "building"]
    if building:
        ids = ", ".join(r["id"] for r in building[:3])
        return at(3, "sprout-build",
                  f"{len(building)} capability(ies) in progress",
                  f"not yet built: {ids}",
                  "Continue the build loop. If tests are not written yet, "
                  "write them and confirm they fail in the code under test.")

    states = facts["slice_states"]
    in_flight = [s for s in slices
                 if states.get(s["id"], {}).get("state") in ("planned", "building")]

    for s in in_flight:
        missing = [ref for ref in s["subsystems"] if not (root / ref).exists()]
        if missing:
            return at(4, "sprout-slice",
                      f"slice '{s['id']}' references a subsystem with no exploded spec",
                      f"missing: {', '.join(missing)}",
                      "Explode the remaining subsystems before implementing. "
                      "A slice you cannot explode is not yet understood.")

    planned = [r for r in rows if r["status"].lower() == "planned"]
    if in_flight and planned:
        s = in_flight[0]
        return at(5, "sprout-build",
                  f"slice '{s['id']}' is specced with {len(planned)} capability(ies) planned",
                  f"{len(planned)} capability(ies) still planned",
                  "Write the black-box tests for the slice walkthrough, then "
                  "confirm each fails in the code under test before implementing.")

    if facts["has_overview"]:
        built = [sid for sid, v in states.items() if v["state"] == "built"]
        recent = f" Showcase {built[-1]!r} if you have not already;" if built else ""
        return at(6, "sprout-slice",
                  "an overview spec exists and no slice is in flight",
                  "no slice is planned or building",
                  f"{recent} then define the next slice and explode the "
                  f"subsystems it touches.".strip().capitalize()
                  if recent else
                  "Showcase the most recently built slice if you have not "
                  "already, then define the next slice and explode the "
                  "subsystems it touches.")

    return at(7, "sprout-spec",
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

    colour = RED if pos["rule"] <= 2 else GREEN
    print(f"{DIM}rule{RESET}     {pos['rule']}")
    print(f"{DIM}loop{RESET}     {colour}{pos['loop']}{RESET}")
    print(f"{DIM}reason{RESET}   {pos['reason']}")
    print(f"{DIM}blocker{RESET}  {pos['blocker']}")
    print(f"{DIM}action{RESET}   {pos['action']}")

    # Sub-loop position inside build is not derivable from artifacts, so say so
    # rather than implying more precision than exists.
    if pos["loop"] == "sprout-build":
        print(f"\n{DIM}note     position within the build loop (tests vs "
              f"implementation) is not derivable from artifacts{RESET}")
    return 0


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------

def cmd_verify(root, args):
    rows, errors = parse_inventory(root)
    if errors:
        for err in errors:
            print(f"{RED}FAIL{RESET}  {err}")
        return 2

    targets = [r for r in rows if r["status"].lower() == "built"]
    if args.id:
        targets = [r for r in targets if r["id"] == args.id]
        if not targets:
            die(f"no built inventory row with id '{args.id}'")

    if not targets:
        print(f"{YELLOW}nothing to verify{RESET}: no capabilities marked built")
        return 0

    failed = []
    for row in targets:
        cmd = row["verify"]
        if not cmd or cmd in ("-", "none", "TODO"):
            print(f"{RED}FAIL{RESET}  {row['id']}: marked built with no verify command")
            failed.append(row["id"])
            continue
        try:
            argv = shlex.split(cmd, posix=(sys.platform != "win32"))
        except ValueError as exc:
            print(f"{RED}FAIL{RESET}  {row['id']}: unparseable verify command ({exc})")
            failed.append(row["id"])
            continue

        proc = subprocess.run(
            argv, cwd=root, capture_output=True, text=True, shell=False
        )
        if proc.returncode == 0:
            print(f"{GREEN}PASS{RESET}  {row['id']}  {DIM}{cmd}{RESET}")
        else:
            print(f"{RED}FAIL{RESET}  {row['id']}  {DIM}{cmd}{RESET} (exit {proc.returncode})")
            tail = (proc.stdout + proc.stderr).strip().splitlines()
            for line in tail[-15:]:
                print(f"        {line}")
            failed.append(row["id"])

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
    rows, errors = parse_inventory(root)
    if errors:
        for err in errors:
            print(f"{RED}FAIL{RESET}  {err}")
        return 2

    buckets = {s: [r for r in rows if r["status"].lower() == s] for s in STATUSES}
    unknown = [r for r in rows if r["status"].lower() not in STATUSES]

    width = max((len(r["id"]) for r in rows), default=0) + 2
    for status in STATUSES:
        group = buckets[status]
        if not group:
            continue
        print(f"\n{status.upper()} ({len(group)})")
        for row in group:
            print(f"  {row['id']:<{width}} {DIM}{row['capability']}{RESET}")
    if unknown:
        print(f"\n{YELLOW}UNKNOWN STATUS ({len(unknown)}){RESET}")
        for row in unknown:
            print(f"  {row['id']:<28} status={row['status']!r}")

    states = collect(root)["slice_states"]
    if states:
        print("\nSLICES")
        sw = max(len(k) for k in states) + 2
        for sid in sorted(states):
            info = states[sid]
            done = sum(1 for r in info["rows"] if r["status"].lower() == "built")
            print(f"  {sid:<{sw}} {info['state']:<9} "
                  f"{DIM}{done}/{len(info['rows'])} built{RESET}")

    total = len(rows)
    built = len(buckets["built"])
    print(
        f"\n{built}/{total} built"
        + (f", {len(buckets['building'])} in progress" if buckets["building"] else "")
        + (f", {len(buckets['planned'])} planned" if buckets["planned"] else "")
    )
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
    return 0


# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(prog="sprout", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="validate specs and inventory, report version drift")

    p_verify = sub.add_parser("verify", help="run verify commands for built capabilities")
    p_verify.add_argument("--id", help="verify a single inventory ID")

    sub.add_parser("status", help="show what is built, building, planned")

    p_next = sub.add_parser(
        "next", help="report the current loop, what is blocking it, and what to do")
    p_next.add_argument("--json", action="store_true",
                        help="emit the position as a JSON object")

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
