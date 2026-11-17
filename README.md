# Singing Materials site

*The sound of atomic-scale vibrations.*

A static website for hearing the phonon spectra of materials: pick a material, choose how it should
sound, press Play. Peaks are fitted with [SingingMaterials](https://github.com/lucydot/SingingMaterials),
turned into [Strudel](https://strudel.cc/) code with [MP2Strudel](https://github.com/lucydot/MP2Strudel),
from Materials Project data.

Status: page and build script working; materials list (~107) needs checking against the Materials Project.
See [`PLAN.md`](PLAN.md).

## Layout

```
PLAN.md                  architecture, decisions, materials, tasks, open questions
CLAUDE.md                context for Claude Code
materials.yml            the materials on the site, their descriptions and fit settings
docs/design.md           page design ("Clean and light")
docs/dynamic-site.md     later: what it would take to play any mp-ID
scripts/check_materials.py  check each material has phonon data; --fix swaps in good IDs
scripts/build_site_data.py  fit every material and write site/data/
site/                    the website: index.html (Listen), about.html, style.css, app.js, data/
cache/                   DOS downloads, peak files, fit plots (git-ignored)
```

## Setup

```bash
conda activate singingmaterials        # or: pip install -e "../SingingMaterials[all]" pyyaml
echo "MP_API_KEY=..." > .env
python scripts/check_materials.py --fix   # check IDs, swap in ones with phonon data
python scripts/build_site_data.py         # fit and write site/data/ (add --png for fit plots)
python -m http.server -d site 8000        # then open http://localhost:8000
```

## Licence

The site and scripts are under the [GNU Affero General Public License v3.0](LICENSE), the licence of
[Strudel](https://strudel.cc/), which the site loads and runs. Copyright © 2026 the Singing Materials authors.

- `site/title.svg` is drawn from the letter shapes of [Caveat](https://github.com/google/fonts/tree/main/ofl/caveat)
  (© The Caveat Project Authors), used under the [SIL Open Font License 1.1](https://openfontlicense.org).
- Phonon data comes from the [Materials Project](https://next-gen.materialsproject.org/), under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the fitted peaks in `site/data/` are derived from it.

## Citation

Whalley, L. et al. (2026). *Singing Materials: Initial experiments in applying sonification to phonon
spectra.* [arXiv:2603.29037](https://arxiv.org/abs/2603.29037)
