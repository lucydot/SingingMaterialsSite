# Later: a search bar for site visitors

Not for now. Goal: a visitor types "calcium carbonate", "CaCO3" or "mp-3953" into a search bar,
sees matching materials, and plays one.

## Recommended: a static search index, built ahead of time

Only materials with phonon data on the Materials Project can be played, so the searchable set is
fixed and fairly small. That means the search doesn't need a live API at all:

1. **Build step (needs MP_API_KEY, run locally or in an Action):** query the Materials Project for
   every material with phonon data, keeping only light fields: mp-ID, formula (plain and pretty),
   elements, crystal system / space group, energy above hull (to rank the stable form first),
   number of sites. Save as `site/data/search-index.json`.
2. **Names:** the Materials Project indexes by formula and elements, not common names. Add a small
   curated `names.yml` for the well-known ones (calcite / aragonite → CaCO₃ by space group, rock salt →
   NaCl, quartz → SiO₂, …), plus simple chemical-name parsing ("calcium carbonate" → Ca + CO₃,
   "magnesium oxide" → MgO) for the rest.
3. **On the page:** load the index once and search it in the browser (formula, elements, names,
   mp-ID), ranked with the most stable form first. No API key, no server, works on GitHub Pages.
4. **Playing a result:**
   - if the material's peaks are already built → play it straight away;
   - if not → "Request this material", which starts the GitHub-issue workflow (phase 2 in `PLAN.md`)
     to fetch, fit and add it, so any searchable material can become playable.

Check the index size once built; if it's large, split it by first element or load it only when the
search bar is used.

## Alternatives considered

- **Live search through a small relay** (e.g. a Cloudflare Worker holding the API key and calling the
  Materials Project summary search). Always up to date, but adds a server to run and protect from
  misuse. Worth it only if the static index gets too big or stale.
- **A Materials Project MCP server** (e.g. `mcp-materials-project` on PyPI). Useful for the owner
  while developing (ask Claude to find IDs), but MCP is a tool interface for AI assistants, so visitors
  can't use it from the page. Natural-language search for visitors would need an LLM behind a server:
  more cost and moving parts than this needs.

## Licensing (checked 17 Nov 2026; not legal advice)

- Materials Project core data is CC BY 4.0: copying, redistributing and adapting are allowed with
  attribution. Publishing processed results (peak fits, downsampled DOS, a search index) fits this.
- Not every MP data product has the same terms (e.g. GNoME data is non-commercial only). Check the
  phonon dataset's own entry on https://next-gen.materialsproject.org/about/terms before building
  the full index.
- Older MP terms ask you to email the MP team before downloading large fractions of the database,
  and an old forum answer framed bulk collection as "for analysis, not redistribution". Email them
  about publishing a ~30k-entry index; they're generally supportive and it removes any doubt.
- Attribution on the site: cite the Materials Project (Jain et al., APL Mater. 2013) and the phonon
  dataset papers (Petretto et al., Sci. Data 2018, and the newer atomate2 phonon database), link each
  material to its MP page, give the data snapshot date, and say the data was processed (CC BY asks
  you to indicate changes).

## Open questions

- Does `mp_api` let the build filter directly for "has phonon data"? (Believed so via the summary
  search's available-properties filter; check the docs.)
- How many materials have phonon data now, and how big is the index? Published figures (Nov 2026):
  the original DFPT phonon set on the Materials Project was ~1,500 materials (Petretto et al. 2018);
  a newer atomate2 phonon database of 27,000+ crystals has since been integrated into the Materials
  Project (APS March Meeting 2026). Get the exact current count from the API, and check which of the
  two sets SingingMaterials' `get_phonon_dos_by_material_id` returns. At ~27,000 entries the index is
  likely a few MB uncompressed, so splitting it or loading it only on first search may be worth it.
  phonondb (Togo, ~10,000 materials, already readable by SingingMaterials) is another possible source.
- Should every search result be playable on request, or only a curated subset?
