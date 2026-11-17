# Singing Materials site: plan

The thinking so far, gathered from the planning chat (13–17 Nov 2026). Decisions are marked
**Decided**; things still to settle are under *Open questions* at the end.

## Goal

A small public website where anyone can pick a material, choose how it should sound, press
**Play**, and hear its atomic-scale vibrations. It should:

- show the fitted phonon DOS peaks, with frequency, DOS and width on hover;
- show the Strudel code behind the sound, with a link that opens it in strudel.cc;
- be plain HTML and minimal CSS, in the "Clean and light" style (see `docs/design.md`).

## How it fits with the existing projects

| Project | Role |
|---|---|
| `../SingingMaterials` | Fetches phonon DOS from the Materials Project, fits Gaussian peaks (`peak_fitting`), maps phonon frequencies to audible ones (`frequency_mapping`). **Use the latest local version.** |
| `../MP2Strudel` | `mp2strudel.py` turns peak fits into JSON and into Strudel code with the data embedded, plus a `strudel.cc/#<base64>` link that opens it. `sonify.js` holds the sonification methods (arp, chord, spectrum, pluck, walk, spread). |
| this repo | `materials.yml` → build script → static site in `site/`, deployed to GitHub Pages. |

`../AtomicStrudel` (the earlier Flask app) is **not** used.

## Architecture (phase 1: static, data saved in the repo)

```
materials.yml ──► scripts/build_site_data.py ──► site/data/…  ──► GitHub Pages
                  (run locally, uses MP_API_KEY;       (committed)      (Action only deploys;
                   imports SingingMaterials +                            no API key in Actions)
                   MP2Strudel)
```

**Decided:**

- **Static site, data built locally and committed.** Run the build on your machine with your
  Materials Project key, commit `site/data/`, push. The GitHub Action only deploys `site/` to Pages, so
  there is no API key in GitHub and no secrets on the page.
- **One source for the sound.** For each material and temperature, the build writes the same Strudel
  code MP2Strudel makes (data embedded, so it needs no fetch). The page:
  - plays that code with `@strudel/web` (pinned version) when Play is pressed;
  - shows it in the "code behind the sound" box;
  - links to `https://strudel.cc/#<base64 of the code>` (MP2Strudel's `strudel_url`, already working).
  
  What you hear on the site, what you read and what opens in strudel.cc are then identical.
- **Sonification methods come from `sonify.js`.** The method picker sets which function the code ends
  with (`chord(C)`, `arp(C)`, …). Start with 4 on the page (chord, arp, pluck, spectrum); walk and
  spread need headphones and can come later.
- **Pitch mapping is SingingMaterials' `frequency_mapping`**, as MP2Strudel uses it (default:
  35 octaves down, 1 THz ≈ 29 Hz). Keep one mapping for every material, so materials can be compared
  by ear.
- **Hover chart is a hand-drawn SVG**, not Plotly/Bokeh/mpld3: the build writes a downsampled DOS curve
  and the peak shapes, and about 50 lines of JS draw them and show a tooltip (frequency in THz,
  DOS in states/THz, FWHM in THz). This keeps the page light and in style; Plotly is the fallback if
  zoom/pan becomes important.
- **Material picker:** a drop-down of the materials on the site (the Materials Project ID box was
  removed, 17 Nov 2026). The description ends with the mp-ID, linking to the Materials Project page.
- **Element picker:** "all (total DOS)" plus each element (open question 4 settled this way). The build
  fits the total DOS as its own projection (`by_temp[t].total`); its fit settings come from a `total`
  key in a per-element `n_peaks` / `smoothing` dict, else the defaults.

### Data the page needs (built by `scripts/build_site_data.py`)

With ~100 materials, there is **one file per material** (all temperatures together) rather than three
files per material × temperature, so the page makes one request per material:

```
site/data/index.json                 # the drop-down: mp_id, name, formula, group, description, labels, temps
site/data/methods.json               # per method: the code from sonify.js (method + the helpers it uses),
                                     # the line that plays it (e.g. "chord({x}).slow(4)"), one-line description
site/data/materials/<mp_id>.json     # per material: settings, labels, pitch warnings, and per temperature
  by_temp: { "athermal" | "300K" | "600K": {
    name,      # MP2Strudel's export_name, e.g. C_mp66_element_athermal
    strudel,   # MP2Strudel's strudel_block: the data block with the peaks embedded
    peaks,     # MP2Strudel's peaks JSON, {label: {freq, width, D}}
    chart: { x_THz: [400 points], labels: { C: { dos: [400 points],
             peaks: [{freq_THz, dos, fwhm_THz, modes, audible_Hz}, …] } } } } }
```

The page's code = `strudel` + the method's code from `methods.json` + the play line for the chosen
element. That exact text is played, shown, and base64-encoded into the strudel.cc link.
The DOS caches and intermediate peak files go in `cache/` (git-ignored).

## Materials

**Now ~107 materials** in `materials.yml` (17 Nov 2026), in groups shown as `<optgroup>`s in the
drop-down: Elements, Semiconductors, Salts, Oxides, Minerals, Perovskites and ferroelectrics,
Thermoelectrics, Layered materials, Hard and light materials. Each has a one-line `description` shown
under the drop-down, and an expected space group `sg` so `check_materials.py --fix` can pick the
right polymorph. Many IDs were written from memory and **must be checked** (task 1). Some (metals,
magnetic or f-electron materials such as Cu, Au, FeS₂, CeO₂, WC) may have no phonon data; drop those.

The original 8, chosen so pairs tell a story, are all still in the list:

| # | Material | Formula | MP ID | Why it's interesting to hear |
|---|---|---|---|---|
| 1 | Diamond | C | mp-66 | Light, stiff atoms: the highest frequencies of the set. Already working. |
| 2 | Silicon | Si | mp-149 | Same structure as diamond, heavier atom: hear the whole spectrum drop. |
| 3 | Gallium arsenide | GaAs | mp-2534 | Same structure again, two similar-mass atoms; a classic semiconductor. |
| 4 | Boron arsenide | BAs | mp-10044 | Very different masses, so a big gap between low and high peaks. Famous for its very high thermal conductivity. |
| 5 | Rock salt | NaCl | mp-22862 | Familiar, simple, soft. |
| 6 | Magnesium oxide | MgO | mp-1265 | Same structure as NaCl but stiffer bonds: pairs with rock salt. |
| 7 | Lead telluride | PbTe | mp-19717 | Heavy and soft: the lowest frequencies, a thermoelectric. The opposite of diamond. |
| 8 | Calcite | CaCO₃ | mp-3953 | Many atoms and three elements, rich spectrum. Already working. |

Alternates if any of these has no phonon data: α-quartz SiO₂ (mp-7000), cubic boron nitride BN
(mp-1639), zinc oxide ZnO (mp-2133), potassium chloride KCl (mp-23193).

Temperatures: athermal, 300 K, 600 K for all.

## Phase 2: request a new material (later)

A "request it" link opens a GitHub issue form; an Action labelled `material-request` checks the ID,
runs the build with the `MP_API_KEY` secret, commits the data, redeploys, and replies on the issue.
Details and a workflow sketch: `docs/phase2-requests.md`. Phase 2 is when the API key moves into
GitHub secrets.

## Phase 3: a search bar for visitors (later)

Visitors type a name, formula or mp-ID ("calcium carbonate", "CaCO3", "mp-3953") and get matching
materials. Plan: a static search index of every Materials Project material with phonon data, built
ahead of time and searched in the browser (no API key or server), plus a small list of common names.
Results not yet built go through the phase 2 request. Details: `docs/future-search.md`.

## Tasks, in order

1. **Check the IDs have phonon data.** `python scripts/check_materials.py` (one call lists every MP
   material with phonon data, then checks formula and space group); `--fix` writes suggested IDs into
   `materials.yml`. *Script written; needs running with the MP key.*
2. **Build script** `scripts/build_site_data.py`: *done.* Reuses MP2Strudel's `peaks_to_json`,
   `strudel_block`, `export_name`, `pitch_warnings` (imported from `../MP2Strudel`, or `--mp2strudel PATH`,
   which works with any answer to open question 1), and fits with SingingMaterials directly so the chart
   gets physical values without fitting twice. Failed materials are skipped and listed.
   *Tested on diamond, calcite and rock salt from cached DOS files.*
3. **Listen and tune.** Check each material's fit plot (`--png`, to `cache/plots/`) and how it sounds;
   adjust `n_peaks` / `smoothing` / `min_frequency` per material in `materials.yml`. Watch the pitch
   warnings: at 300 K and 600 K the occupation weighting can put a peak near 0 THz (diamond gets one at
   0.08 THz → 2 Hz), which `min_frequency` fixes.
4. **Build the page** in `site/`: *done* (`index.html`, `about.html`, `style.css`, `app.js`). Menu is
   **Listen** and **About** only. State is kept in the URL (`?m=mp-66&e=C&t=300K&s=chord`), so any
   sound can be linked to. All four methods evaluated without errors in Strudel 1.3.0 (headless Chrome).
5. **GitHub Action** `.github/workflows/pages.yml`: on push to `main`, deploy `site/` to Pages
   (`actions/upload-pages-artifact` + `actions/deploy-pages`). Turn on Pages → "GitHub Actions".
6. **Check**: every material and method plays; the strudel.cc links open with the right code; the chart
   tooltip values match the fit CSVs; works on a phone; keyboard-only works.
7. Phase 2 when ready.

## Open questions

1. **Repo layout.** Options:
   - (a) This repo, with `MP2Strudel` added as a git submodule (or checked out in the Action) and
     imported. Keeps MP2Strudel as its own tool.
   - (b) Move the site into the MP2Strudel repo as `site/`. One repo, simplest imports.
   - (c) Make MP2Strudel pip-installable and depend on it.
   
   Phase 1 builds data locally, so any of these works today; it matters for phase 2, when the Action
   needs both SingingMaterials and MP2Strudel.
2. **SingingMaterials version.** The build uses the local, latest version. For phase 2 the Action will
   install it from GitHub, so push the current local changes and pin a commit
   (`pip install git+https://github.com/lucydot/SingingMaterials@<commit>`).
3. **Site name and address** (e.g. `lucydot.github.io/singing-materials`). Strudel code no longer needs
   it (data is embedded), but the page and the phase 2 issue links do.
4. **Element choice for multi-element materials:** play one element at a time (current mockup), all
   elements together (e.g. `stack(pluck(Ca).pan(0.15), pluck(C).pan(0.5), pluck(O).pan(0.85))`), or
   offer "all" as an option?
5. **Licence:** *settled 17 Nov 2026*: the repo is AGPL-3.0 (`LICENSE`), matching Strudel; the footer links
   to the source. Title lettering is from Caveat (OFL 1.1); Materials Project data is CC BY 4.0 (README).
