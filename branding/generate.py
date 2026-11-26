"""Generate darkm.dev logo SVGs (mark, wordmark light/dark, favicon) with text converted to paths."""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
WEIGHT = int(sys.argv[3]) if len(sys.argv) > 3 else 700
OUT.mkdir(parents=True, exist_ok=True)

INK = "#0B0B12"      # near-black (text on light bg, tile)
PAPER = "#F4F4F8"    # near-white (moon, text on dark bg)
ACCENT = "#8B7CFF"   # soft violet (cursor, ".dev")

font = instantiateVariableFont(TTFont(FONT), {"wght": WEIGHT})
cmap, gs = font.getBestCmap(), font.getGlyphSet()
UPM = font["head"].unitsPerEm
ASC = font["hhea"].ascent


def text_path(text, size, x0, baseline, tracking=0.0):
    """Return (svg path d, advance width) for text at font size, baseline y."""
    s = size / UPM
    pen = SVGPathPen(gs)
    x = 0.0
    for ch in text:
        g = cmap[ord(ch)]
        tp = TransformPen(pen, (s, 0, 0, -s, x0 + x, baseline))
        gs[g].draw(tp)
        x += gs[g].width * s + tracking * size
    return pen.getCommands(), x - tracking * size


def mark(x, y, size, tile=True):
    """Moon + cursor mark in a size x size box at (x, y)."""
    k = size / 64
    parts = []
    if tile:
        parts.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{15*k:.2f}" fill="{INK}"/>')
    # crescent = big circle minus offset circle (via mask with unique id)
    mid = f"m{int(x)}{int(y)}{int(size)}"
    parts.append(
        f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{size}" height="{size}">'
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#fff"/>'
        f'<circle cx="{x+38*k:.2f}" cy="{y+24*k:.2f}" r="{14*k:.2f}" fill="#000"/></mask>'
        f'<circle cx="{x+28*k:.2f}" cy="{y+33*k:.2f}" r="{18*k:.2f}" fill="{PAPER}" mask="url(#{mid})"/>'
    )
    # terminal cursor block sitting in the crescent's hollow
    parts.append(f'<rect x="{x+46*k:.2f}" y="{y+19.5*k:.2f}" width="{8*k:.2f}" height="{14*k:.2f}" rx="{1.5*k:.2f}" fill="{ACCENT}"/>')
    return "".join(parts)


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


# --- mark / favicon -------------------------------------------------------------
(OUT / "darkmdev-mark.svg").write_text(svg(64, 64, mark(0, 0, 64), "darkm.dev"))

# --- horizontal wordmark ----------------------------------------------------------
H, M = 64, 64           # height, mark size
FS = 34                 # font size
GAP = 16
base = H / 2 + FS * 0.36  # optical vertical centring of lowercase
d1, w1 = text_path("darkm", FS, M + GAP, base, tracking=-0.02)
d2, w2 = text_path(".dev", FS, M + GAP + w1, base, tracking=-0.02)
W = M + GAP + w1 + w2 + 2
for variant, fg in (("light", INK), ("dark", PAPER)):
    # light = for light backgrounds (ink text); dark = for dark backgrounds (paper text)
    tile = mark(0, 0, M)
    if variant == "dark":
        # on dark bg the ink tile disappears; outline it subtly
        tile = tile.replace(f'fill="{INK}"/>', f'fill="{INK}" stroke="#2A2A38" stroke-width="1.5"/>', 1)
    body = tile + f'<path d="{d1}" fill="{fg}"/><path d="{d2}" fill="{ACCENT}"/>'
    (OUT / f"darkmdev-logo-{variant}.svg").write_text(svg(W, H, body, "darkm.dev"))

print("wrote", sorted(p.name for p in OUT.glob("*.svg")), f"wordmark {W:.0f}x{H}")
