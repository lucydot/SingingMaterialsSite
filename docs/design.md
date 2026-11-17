# Page design: "Clean and light"

Chosen from five mockups on the design canvas (mockup 3):
https://claude.ai/artifact/7eraJ6ec6f8d1wGLRVeZfe

Inspired by cleanbean.co.uk and the We Sort. simple sites: plain HTML, minimal CSS, one column,
big text, no framework.

## Look

- Background `#ffffff`; text `#666666` (darker than Clean Bean's `#969696`, so it passes 4.5:1).
- One accent, `#4f58c4` (a darker lavender than Clean Bean's `#929ae8`, for contrast). Used for the
  site name, the current page in the menu, the thin rule, chosen options and the Play button.
- Font: Quicksand 400/500 (Google Fonts); code in a monospace (JetBrains Mono or `ui-monospace`).
- Type: `2rem` for almost everything on desktop (`1.5rem` on phones), `0.75em` for secondary text.
- Content `max-width: 55rem`, padding `2rem` (`1rem` on phones), blocks spaced `1rem`.
- Links: no underline, `border-bottom: 1px solid` on hover or when current.

## Page, top to bottom

1. **Header**: "Singing Materials" (accent), menu: Listen, About (`about.html`; the paper is linked
   from About and the footer). Thin 1px rule in the accent colour.
2. **Tagline**: "The sound of atomic-scale vibrations."
3. **Choose**:
   - Material: drop-down of ~100 materials grouped with `<optgroup>` (names from `index.json`), with
     the one-line description under it, ending with the mp-ID as a link to the material's Materials Project
     page. (No ID text box; removed 17 Nov 2026.)
   - Element: "all (total DOS)" first, then each element, for materials with more than one element;
     "all" plays and draws the total DOS, fitted on its own. Temperature: no temperature / 300 K / 600 K.
   - Sound: one checkbox per method in a row (a `<fieldset>`); ticked ones are in the accent colour and
     play together, as `stack(chord(C).slow(4), arp(C)).postgain(1/√n)`. One line per ticked method
     under them says what it does. Nothing ticked: Play is disabled.
   - **Play** button (accent background, white text), which becomes **Stop** while playing.
4. **Chart**: the DOS curve (dark line) with each fitted peak as a pale accent-coloured shape.
   Hover or tab to a peak: it darkens, a dashed line drops to the axis, and a small box shows
   "Peak n · frequency … THz · DOS … states/THz · width (FWHM) … THz". Axes: frequency (THz),
   DOS (states/THz). No caption (removed 17 Nov 2026).
5. **Code**: "The code producing the sound:" then the Strudel code in a pale box with an accent left
   border, and "Open this in strudel.cc ↗" (new tab) below it.
6. **Credits**: Data: Materials Project. Peaks: SingingMaterials. Sound: Strudel. Link to the paper
   (arXiv:2603.29037).

## Behaviour

- Changing material, element, temperature or method updates the chart, the code and the link
  straight away. If something is playing, it switches to the new sound.
- Play starts audio only on a click (browsers require a user gesture). First press may take a
  moment while Strudel loads its sounds.
- Works with keyboard only; real `<button>`, `<select>`, `<input>` and `<label>` elements.
- Respect `prefers-reduced-motion` (nothing animates anyway).

## Method descriptions (one line each, from `sonify.js`)

- **chord**: every peak sounds together; taller peaks louder, broader peaks wobble more.
- **arp**: the peaks one after another, low to high; sharp peaks ring longer.
- **pluck**: the chord struck once and left to ring; each peak fades at its own rate.
- **spectrum**: each peak as a band of noise, as wide as the peak.
- later: **walk** (arp moving left to right), **spread** (chord across the speakers).
