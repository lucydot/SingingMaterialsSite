"""Build the site's data from materials.yml.

For each material: fetch the phonon DOS (cached in cache/), fit peaks with SingingMaterials at each
temperature, and write site/data/materials/<mp_id>.json holding, per temperature, the Strudel code
(MP2Strudel's block, data embedded), the peaks and the chart data. Also writes site/data/index.json
(the material list) and site/data/methods.json (the sonification methods, taken from MP2Strudel's sonify.js).

Run from the repo root, with MP_API_KEY in a .env file (here or in a parent folder):

    python scripts/build_site_data.py                 # every material
    python scripts/build_site_data.py mp-66 mp-149    # only these (index.json still lists all built so far)
    python scripts/build_site_data.py --png           # also save fit plots to cache/plots/

A material that fails (e.g. no phonon data) is reported and skipped; the rest are still built.
"""

import argparse
import contextlib
import json
import re
import sys
import traceback
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"  # <mp_id>_dos.json from SingingMaterials, peaks JSON, plots; git-ignored
OUT = ROOT / "site" / "data"
CHART_POINTS = 400  # DOS curve points per label

# sonification methods on the page: what the code ends with, and one line on what you hear
METHODS = {
    "chord": ("chord({x}).slow(2)", "Every peak sounds together; taller peaks louder, broader peaks wobble more."),
    "arp": ("arp({x})", "The peaks one after another, low to high; sharp peaks ring longer."),
    "pluck": ("pluck({x})", "The chord struck once and left to ring; each peak fades at its own rate."),
    "spectrum": ("spectrum({x}).slow(2)", "Each peak as a band of noise, as wide as the peak."),
}


def r(values, n):
    return [float(round(float(v), n)) for v in values]


def sig(values, n=4):
    """round to n significant figures (DOS values span many orders of magnitude at low temperature)."""
    return [float(f"{float(v):.{n}g}") for v in values]


def method_snippets(sonify_path):
    """{method: code} from sonify.js: each method's definition plus the helpers it uses, in file order.
    sonify.js is split into blocks at blank lines; blocks that are only comments (examples) are skipped."""
    blocks = [b.strip("\n") for b in re.split(r"\n\s*\n", sonify_path.read_text())]
    defined = {}  # name -> block index
    for i, b in enumerate(blocks):
        for name in re.findall(r"^const (\w+)\s*=", b, flags=re.MULTILINE):
            defined[name] = i

    def needs(name, seen):
        i = defined[name]
        if i in seen:
            return
        seen.add(i)
        body = re.sub(r"//.*", "", blocks[i])  # names mentioned in comments are not dependencies
        for other, j in defined.items():
            if j != i and re.search(rf"\b{other}\b", body):
                needs(other, seen)

    out = {}
    for method in METHODS:
        seen = set()
        needs(method, seen)
        out[method] = "\n\n".join(blocks[i] for i in sorted(seen))
    return out


def chart_data(fits):
    """DOS curve (downsampled) and fitted peaks for each label, in physical units."""
    f_max = max(float(f["frequencies"][-1]) for f in fits.values()) / 1e12
    # end the x axis where every label's DOS has died away, not at the end of MP's grid
    last = 0.0
    for f in fits.values():
        d = np.asarray(f["densities"])
        if d.max() > 0:
            last = max(last, float(f["frequencies"][np.nonzero(d > 1e-3 * d.max())[0][-1]]) / 1e12)
    x_max = min(f_max, last * 1.04 + 0.2)
    edges = np.linspace(0.0, x_max, CHART_POINTS + 1)
    x = (edges[:-1] + edges[1:]) / 2

    labels = {}
    for label, f in fits.items():
        f_thz = np.asarray(f["frequencies"]) / 1e12
        d = np.asarray(f["densities"])
        # max in each bin, so the curve's peaks stay as tall as the fitted peaks drawn over it
        idx = np.clip(np.searchsorted(edges, f_thz) - 1, 0, CHART_POINTS - 1)
        d = np.clip(d, 0, None)
        y = np.interp(x, f_thz, d, left=0.0, right=0.0)  # for bins narrower than MP's grid, which hold no point
        inside = f_thz <= x_max
        np.maximum.at(y, idx[inside], d[inside])
        labels[label] = {
            "dos": sig(y),
            "peaks": [
                {"freq_THz": c, "dos": h, "fwhm_THz": w, "modes": m}
                for c, h, w, m in zip(
                    r(np.asarray(f["centres"]) / 1e12, 3),
                    sig(f["dos"]),
                    r(np.asarray(f["fwhms"]) / 1e12, 3),
                    sig(f["modes"], 3),
                )
            ],
        }
    return {"x_THz": r(x, 3), "labels": labels}


def build_material(m, defaults, mp2strudel, png):
    """fit one material at each temperature; return its index entry."""
    from singingmaterials import frequency_mapping, mp_interface, peak_fitting

    s = {**defaults, **{k: v for k, v in m.items() if k in ("temps", "projection", "n_peaks", "smoothing", "min_frequency")}}
    temps = [None if t == "athermal" else t for t in s["temps"]]
    pitch_map = (1.0, frequency_mapping.phonon_to_audible_octaves(1e12, s["octaves_down"]))

    with contextlib.chdir(CACHE):  # SingingMaterials caches <mp_id>_dos.json in the working directory
        dos_dict = mp_interface.get_dos_raw_mp(m["id"])
    formula = dos_dict["metadata"].get("formula") or m["formula"]
    if formula != m["formula"]:
        print(f"  warning: {m['id']} is {formula} on the Materials Project, not {m['formula']}")
    labels = list(peak_fitting._projections(dos_dict, s["projection"]))

    def settings_for(projection, labels):
        """fit settings for one projection. The total DOS ("all" on the page) uses a `total` key in a
        per-element n_peaks / smoothing dict if there is one, otherwise the default."""
        def pick(key):
            v = s[key]
            if projection == "total" and isinstance(v, dict):
                return v.get("total", defaults[key])
            return mp2strudel.settings_for_material(v, labels)
        return {
            "n_peaks": pick("n_peaks"),
            "smoothing_THz": pick("smoothing"),
            "min_frequency_THz": s["min_frequency"],
            "pitch_map": {"THz": pitch_map[0], "Hz": pitch_map[1]},
            "octaves_down": s["octaves_down"],
        }

    def fit(projection, labels, settings, temp, warnings):
        """fit one projection at one temperature: MP2Strudel's peaks and Strudel block, plus the chart data."""
        fits = peak_fitting.fit_dos_peaks(
            dos_dict=dos_dict,
            projection=projection,
            temperature=temp,
            n_peaks=settings["n_peaks"],
            smoothing=settings["smoothing_THz"],
            min_frequency=settings["min_frequency_THz"],
        )
        peaks = mp2strudel.peaks_to_json(fits, pitch_map)
        name = mp2strudel.export_name(m["id"], formula, projection, temp)
        peaks_path = CACHE / "peaks" / f"{name}.json"  # strudel_block reads the peaks from this file
        peaks_path.write_text(json.dumps(peaks, indent=1, ensure_ascii=False))
        desc = {
            "mp_id": m["id"], "formula": formula, "labels": labels, "projection": projection,
            "settings": settings, "files": {temp: peaks_path},
        }
        tag = mp2strudel.temp_tag(temp)
        block = mp2strudel.strudel_block([desc], f"{m['name']}, {formula} {m['id']} ({tag})")
        chart = chart_data(fits)
        for label, p in peaks.items():  # audible pitch of each peak, for the chart tooltip
            for peak, hz in zip(chart["labels"][label]["peaks"], p["freq"]):
                peak["audible_Hz"] = hz
        warnings.extend(mp2strudel.pitch_warnings(fits, peaks))
        if png:
            mp2strudel.save_plot(fits, formula, CACHE / "plots" / f"{name}.png")
        return {"name": name, "strudel": block, "peaks": peaks, "chart": chart}

    settings = settings_for(s["projection"], labels)
    total_settings = settings_for("total", ["total"])
    by_temp, warnings = {}, {}
    for temp in temps:
        tag, w = mp2strudel.temp_tag(temp), []
        by_temp[tag] = fit(s["projection"], labels, settings, temp, w)
        by_temp[tag]["total"] = fit("total", ["total"], total_settings, temp, w)  # "all" on the page
        if w:
            warnings[tag] = w

    data = {
        "mp_id": m["id"],
        "name": m["name"],
        "formula": formula,
        "projection": s["projection"],
        "labels": labels,
        "settings": settings,
        "total_settings": total_settings,
        "temps": list(by_temp),
        "pitch_warnings": warnings,
        "by_temp": by_temp,
    }
    path = OUT / "materials" / f"{m['id']}.json"
    path.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    n_warn = sum(len(v) for v in warnings.values())
    print(f"  wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} kB, labels {', '.join(labels)}"
          + (f", {n_warn} pitch warnings" if n_warn else "") + ")")
    return {"labels": labels, "temps": list(by_temp), "formula": formula}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mp_ids", nargs="*", help="only build these (default: all in materials.yml)")
    p.add_argument("--materials", type=Path, default=ROOT / "materials.yml")
    p.add_argument("--mp2strudel", type=Path, default=ROOT.parent / "MP2Strudel", help="MP2Strudel folder")
    p.add_argument("--png", action="store_true", help="also save fit plots to cache/plots/")
    args = p.parse_args()

    sys.path.insert(0, str(args.mp2strudel.resolve()))
    import mp2strudel

    config = yaml.safe_load(args.materials.read_text())
    defaults, materials = config["defaults"], config["materials"]
    unknown = set(args.mp_ids) - {m["id"] for m in materials}
    if unknown:
        p.error(f"not in {args.materials.name}: {', '.join(sorted(unknown))}")

    for d in (CACHE / "peaks", CACHE / "plots", OUT / "materials"):
        d.mkdir(parents=True, exist_ok=True)

    failed = []
    for m in materials:
        if args.mp_ids and m["id"] not in args.mp_ids:
            continue
        print(f"{m['id']} {m['name']}")
        try:
            build_material(m, defaults, mp2strudel, args.png)
        except Exception as e:
            print(f"  FAILED: {e}")
            if not isinstance(e, ValueError):
                traceback.print_exc()
            failed.append(m)

    # the index lists every material in materials.yml that has a built data file, in materials.yml order
    index = []
    for m in materials:
        path = OUT / "materials" / f"{m['id']}.json"
        if not path.is_file():
            continue
        d = json.loads(path.read_text())
        index.append({
            "mp_id": m["id"],
            "name": m["name"],
            "formula": d["formula"],
            "group": m["group"],
            "description": m["description"],
            "labels": d["labels"],
            "temps": d["temps"],
        })
    (OUT / "index.json").write_text(json.dumps(index, indent=1, ensure_ascii=False))

    snippets = method_snippets(args.mp2strudel / "sonify.js")
    methods = [{"name": k, "play": play, "describe": describe, "code": snippets[k]} for k, (play, describe) in METHODS.items()]
    (OUT / "methods.json").write_text(json.dumps(methods, indent=1, ensure_ascii=False))

    print(f"\n{len(index)} of {len(materials)} materials on the site (site/data/index.json)")
    if failed:
        print(f"{len(failed)} failed this run: " + ", ".join(f"{m['id']} {m['name']}" for m in failed))
        print("If they have no phonon data, run scripts/check_materials.py --fix.")


if __name__ == "__main__":
    main()
