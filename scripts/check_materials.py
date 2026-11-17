"""Check that every material in materials.yml has phonon data on the Materials Project, with the
formula and space group given there; suggest a replacement ID where not.

Run from the repo root, with MP_API_KEY in a .env file (here or in a parent folder):

    python scripts/check_materials.py          # report
    python scripts/check_materials.py --fix    # also write the suggested IDs into materials.yml

A suggestion is a Materials Project entry with the same formula that has phonon data: the one with the
expected space group if there is one, otherwise the most stable. Check the --fix changes before committing.
Entries with no phonon data for their formula at all are reported; remove or replace them by hand.
"""

import argparse
import os
import re
import sys
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv
from mp_api.client import MPRester

MATERIALS = Path("materials.yml")


def get(doc, name):
    """field from an mp_api document, whether it came back as an object or a dict."""
    return doc.get(name) if isinstance(doc, dict) else getattr(doc, name, None)


def symbol(doc):
    sym = get(doc, "symmetry")
    return get(sym, "symbol") if sym is not None else None


def as_list(sg):
    return [] if sg is None else [sg] if isinstance(sg, str) else list(sg)


def suggest(candidates, expected_sg):
    """best candidate: expected space group first, then lowest energy above hull."""
    def key(doc):
        return (symbol(doc) not in expected_sg, get(doc, "energy_above_hull") or 0.0)
    return min(candidates, key=key) if candidates else None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fix", action="store_true", help="write suggested IDs into materials.yml")
    args = p.parse_args()

    text = MATERIALS.read_text()
    materials = yaml.safe_load(text)["materials"]
    load_dotenv(find_dotenv(usecwd=True))

    with MPRester(os.getenv("MP_API_KEY")) as mpr:
        print("listing every material with phonon data...")
        phonon_ids = {str(get(d, "material_id")) for d in mpr.materials.phonon.search(fields=["material_id"])}
        print(f"{len(phonon_ids)} materials have phonon data\n")

        by_formula = {}
        for f in sorted({m["formula"] for m in materials}):
            by_formula[f] = mpr.materials.summary.search(
                formula=f, fields=["material_id", "formula_pretty", "symmetry", "energy_above_hull"]
            )

    ok, fixed, missing = 0, [], []
    for m in materials:
        mp_id, name, formula, expected_sg = m["id"], m["name"], m["formula"], as_list(m.get("sg"))
        docs = {str(get(d, "material_id")): d for d in by_formula[m["formula"]]}
        doc = docs.get(mp_id)
        problems = []
        if doc is None:
            problems.append(f"not a {formula} entry")
        else:
            if expected_sg and symbol(doc) not in expected_sg:
                problems.append(f"space group {symbol(doc)}, expected {'/'.join(expected_sg)}")
        if mp_id not in phonon_ids:
            problems.append("no phonon data")

        if not problems:
            ok += 1
            continue
        candidates = [d for i, d in docs.items() if i in phonon_ids]
        best = suggest(candidates, expected_sg)
        if best is None:
            print(f"  NO    {mp_id:11} {name:24} {'; '.join(problems)}; no {formula} entry has phonon data")
            missing.append(m)
            continue
        new_id = str(get(best, "material_id"))
        note = "" if not expected_sg or symbol(best) in expected_sg else f" (space group {symbol(best)}: check)"
        print(f"  SWAP  {mp_id:11} {name:24} {'; '.join(problems)} -> {new_id}{note}")
        fixed.append((mp_id, new_id))

    print(f"\n{ok} OK, {len(fixed)} to swap, {len(missing)} with no phonon data for their formula")
    if missing:
        print("No phonon data (remove or replace by hand): " + ", ".join(f"{m['name']} ({m['formula']})" for m in missing))

    if fixed and args.fix:
        for old, new in fixed:
            text, n = re.subn(rf"^(\s*- id: ){re.escape(old)}\s*$", rf"\g<1>{new}  # was {old}", text, flags=re.MULTILINE)
            if n != 1:
                print(f"could not find '- id: {old}' once in {MATERIALS}; change it by hand")
        MATERIALS.write_text(text)
        print(f"wrote {len(fixed)} new IDs to {MATERIALS}; check them before committing")
    elif fixed:
        print("Run with --fix to write the suggested IDs into materials.yml.")

    sys.exit(1 if missing or (fixed and not args.fix) else 0)


if __name__ == "__main__":
    main()
