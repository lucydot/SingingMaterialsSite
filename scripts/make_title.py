"""Draw the site title, "Singing Materials", as a hand-lettered SVG: Caveat's letter shapes (as paths, so no font
is needed), each letter slightly tilted and lifted, repeated letters in Caveat's alternate forms, and the dots on
the i's replaced by small hearts.

Caveat is under the SIL Open Font License, which allows this. Get Caveat[wght].ttf from
https://github.com/google/fonts/tree/main/ofl/caveat and run from the repo root:

    python scripts/make_title.py path/to/Caveat[wght].ttf          # writes site/title.svg
    python scripts/make_title.py FONT --heart-color "#4f58c4"       # hearts in the accent colour
"""

import argparse
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

TEXT = "Singing Materials"
# glyph per letter: alternate forms so repeated letters differ, as in real handwriting
GLYPHS = ["S", "dotlessi", "n", "g", "dotlessi", "n.ss01", "g.ss02", "space",
          "M", "a", "t", "e", "r", "dotlessi", "a.ss01", "l", "s"]
# per letter: (tilt in degrees, lift in font units); fixed, so the drawing is the same every run
JITTER = [(-3, 10), (2, -8), (-1, 4), (3, -6), (-2, 12), (1, 0), (-3, -10), (0, 0),
          (2, -6), (-2, 8), (3, -4), (-1, 10), (2, -10), (-3, 4), (1, 12), (-2, -6), (3, 6)]
# hand-drawn heart, 24 units across, centred on (12, 12), point at the bottom; slightly lopsided on purpose
HEART = "M12 20.5C5 15.6 1.8 11.3 2.7 7.4 3.6 3.6 9.2 2.9 12 7.6 14.6 3.2 20.6 3.4 21.4 7.2 22.3 11.1 19.4 15.4 12 20.5Z"
HEART_TILT = [-14, 10, -6]  # one per i


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("font", type=Path, help="Caveat[wght].ttf")
    p.add_argument("--weight", type=float, default=600)
    p.add_argument("--color", default="#4f58c4", help="letters (default: the site's accent)")
    p.add_argument("--heart-color", default="#e35d86")
    p.add_argument("--out", type=Path, default=Path("site/title.svg"))
    args = p.parse_args()

    font = instantiateVariableFont(TTFont(args.font), {"wght": args.weight})
    glyphs = font.getGlyphSet()
    hmtx = font["hmtx"]
    dot = BoundsPen(glyphs)  # where the i's dot sits: the part of "i" above the dotless i
    glyphs["i"].draw(dot)
    stem = BoundsPen(glyphs)
    glyphs["dotlessi"].draw(stem)
    dot_y = (stem.bounds[3] + dot.bounds[3]) / 2 + 45  # a little higher than Caveat's dot, as hearts are bigger

    paths, hearts, x, n_heart = [], [], 0.0, 0
    xmin = ymin = float("inf")
    xmax = ymax = float("-inf")
    for name, (tilt, lift) in zip(GLYPHS, JITTER):
        width = hmtx[name][0]
        if name != "space":
            pen = SVGPathPen(glyphs)
            glyphs[name].draw(pen)
            b = BoundsPen(glyphs)
            glyphs[name].draw(b)
            cx = x + width / 2
            # font units are y-up; SVG is y-down: flip, tilt about the letter's centre, lift
            paths.append(f'<path transform="translate({cx:.0f} {-lift}) rotate({tilt}) translate({-width / 2:.0f} 0) '
                         f'scale(1 -1)" d="{pen.getCommands()}"/>')
            xmin, xmax = min(xmin, x + b.bounds[0]), max(xmax, x + b.bounds[2])
            ymin, ymax = min(ymin, -b.bounds[3] - lift), max(ymax, -b.bounds[1] - lift)
            if name == "dotlessi":
                hx = x + (stem.bounds[0] + stem.bounds[2]) / 2 + 12
                hy = -dot_y - lift
                size = 175  # font units across
                hearts.append(f'<path transform="translate({hx:.0f} {hy:.0f}) rotate({HEART_TILT[n_heart]}) '
                              f'scale({size / 24:.3f}) translate(-12 -12)" d="{HEART}"/>')
                n_heart += 1
                ymin = min(ymin, hy - size / 2)
        x += width

    # one more small heart, floating up and to the right of the last letter
    hx, hy, size = xmax + 110, ymin + 150, 130
    hearts.append(f'<path transform="translate({hx:.0f} {hy:.0f}) rotate(18) scale({size / 24:.3f}) translate(-12 -12)" d="{HEART}"/>')
    xmax = max(xmax, hx + size / 2)

    pad = 40
    vb = f"{xmin - pad:.0f} {ymin - pad:.0f} {xmax - xmin + 2 * pad:.0f} {ymax - ymin + 2 * pad:.0f}"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="{TEXT}">\n'
        f"<title>{TEXT}</title>\n"
        f'<g fill="{args.color}">\n' + "\n".join(paths) + "\n</g>\n"
        f'<g fill="{args.heart_color}">\n' + "\n".join(hearts) + "\n</g>\n</svg>\n"
    )
    args.out.write_text(svg)
    print(f"wrote {args.out} ({len(svg) // 1024} kB, viewBox {vb})")


if __name__ == "__main__":
    main()
