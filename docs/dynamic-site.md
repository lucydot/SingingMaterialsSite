# Later: playing any Materials Project ID

Today the site is static: every sound is fitted on your machine and committed as a JSON file.
To let a visitor type *any* mp-ID and hear it, something has to fetch that material's phonon DOS
from the Materials Project and fit it. That has to happen off the visitor's browser, for two reasons:

1. **The API key.** The Materials Project needs a key, and anything sent to the browser is public.
2. **The fitting is Python** (SingingMaterials + scipy). It could run in the browser with Pyodide, but
   it would still need the key to get the data, so that doesn't remove the need for a server.

So yes, on-demand fitting means a back end. But "any mp-ID" is a smaller set than it sounds: only
materials with phonon calculations can sing. `scripts/check_materials.py` prints how many there are
(the Petretto et al. 2018 set alone is ~1,500). That gives three options:

## A. Precompute every material with phonon data (no back end)

Run `build_site_data.py` over the full list of phonon IDs once (a few hours, mostly downloading), and
publish all of it statically. At ~30 kB per material, 1,500–5,000 materials is 50–150 MB: fine for
GitHub Pages (1 GB limit), Cloudflare Pages or Netlify. The ID box then finds anything that can be
heard, instantly, with no server, no secrets and no running costs. Re-run when the Materials Project
adds data.

What's needed: a list of every phonon ID (one `mpr.materials.phonon.search` call), a material
**search** in place of the drop-down (type a name, formula or ID; names come from MP's summary data),
and automatic fits. The hand-tuned `n_peaks`/`smoothing` in `materials.yml` would stay for the featured
materials; the rest use defaults, and the page should say "automatic fit".

**This is the recommended next step.** It gives the "type any mp-ID" experience with the static
architecture unchanged.

## B. A small API service (a real back end)

Needed only if fitting must be live, e.g. visitors change `n_peaks`, smoothing, temperature or pitch
mapping themselves, or if you want new MP data to appear without a rebuild.

- **Service:** a small Python web app (FastAPI or Flask) with one endpoint,
  `GET /api/material/mp-149?temp=300` → the same JSON as `site/data/materials/<id>.json`. It imports
  SingingMaterials and MP2Strudel exactly as the build script does.
- **Hosting:** anywhere that runs a Python container, e.g. Google Cloud Run, Fly.io, Render, Railway, or
  a university VM. The MP key is an environment secret there. Expect cold starts of a few seconds
  on free tiers, and a fit takes ~1–5 s.
- **Cache:** store each result (disk, S3/R2 or a database) so each material is fetched and fitted once.
- **Protection:** rate-limit per visitor, accept only `mp-\d+`, and cap concurrent fits, so nobody
  can use up your MP quota or your server.
- **Front end:** unchanged except that `app.js` fetches from the API when a material isn't in the static
  files, and shows "fitting…" while it waits.
- **Ongoing:** a server to keep patched and paid for, logs, uptime. That is the real cost of B.

## C. Requests via GitHub (phase 2 in PLAN.md)

"Not on the site yet: request it" opens a GitHub issue; an Action with the MP key builds that material
and redeploys. No server, but minutes rather than seconds, and only for people with GitHub accounts.
A stepping stone, and largely made unnecessary by A.
