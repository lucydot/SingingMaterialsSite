# A search bar for finding materials

Goal: a visitor types "calcium carbonate", "CaCO3" or "mp-3953" into a search bar,
sees matching materials, and plays one.

Only materials with phonon data on the Materials Project can be played, so the searchable set is
fixed and fairly small. 

1. **Build step (needs MP_API_KEY, run locally or in an Action):** query the Materials Project for
   every material with phonon data, keeping only light fields: mp-ID, formula (plain and pretty),
   elements, crystal system / space group, energy above hull (to rank the stable form first),
   number of sites. Save as `site/data/search-index.json`.
2. **Names:** the Materials Project indexes by formula and elements, not common names. Add a small
   curated `names.yml` for the well-known ones (calcite / aragonite → CaCO₃ by space group, rock salt →
   NaCl, quartz → SiO₂, …), plus simple chemical-name parsing ("calcium carbonate" → Ca + CO₃,
   "magnesium oxide" → MgO) for the rest.
3. **On the page:** load the index once and search it in the browser (formula, elements, names,
   mp-ID), ranked with the most stable form first.






