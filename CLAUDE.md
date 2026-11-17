# Singing Materials site

A static website where people pick a material, choose a sonification method, press Play and hear
its phonon spectrum, with a hover chart of the fitted peaks and the Strudel code behind the sound.

**Read `PLAN.md` first**: it has the architecture, the decisions already made, the material list,
the task order and the open questions. `docs/design.md` is the page spec; `docs/phase2-requests.md`
is for later.

## Related code (sibling folders in ~/Code)

- `../SingingMaterials`: Python package, the owner's. Peak fitting (`peak_fitting.fit_dos_peaks`),
  frequency mapping (`frequency_mapping`), Materials Project access (`mp_interface`). Use the latest
  local version (installed editable: `pip install -e "../SingingMaterials[all]"`). Don't edit it from
  here without asking.
- `../MP2Strudel`: `mp2strudel.py` (peaks → JSON + Strudel code with embedded data + strudel.cc link)
  and `sonify.js` (the sonification methods). Reuse rather than reimplement. Don't edit it from here
  without asking.
- `../AtomicStrudel`: old Flask app. Not used.

## Conventions

- Site: plain HTML, minimal CSS, small vanilla JS. No framework, no bundler, no build step for the page.
- Pin CDN versions (e.g. `@strudel/web@x.y.z`), never `@latest`.
- Accessible by default: real form controls with labels, keyboard works, text contrast ≥ 4.5:1.
- The Materials Project API key lives only in `.env` (git-ignored). Never put it in the site or in
  committed files.
- Python: match the style of SingingMaterials/MP2Strudel (short docstrings, numpy, argparse).
- `*_dos.json` caches are git-ignored; built site data in `site/data/` is committed (phase 1).

## Start here

Task 1 in `PLAN.md`: run `python scripts/check_materials.py` and fix up `materials.yml`.
Then settle open question 1 (repo layout) with the owner before writing the build script.
