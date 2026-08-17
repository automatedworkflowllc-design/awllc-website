# -*- coding: utf-8 -*-
"""1080x1080 social cards, generated from the SHARED brand tokens.

WHY A GENERATOR: the same defect that gave the site three different colour schemes would
give every hand-made social post a different look. Palette is imported from tokens.py, so a
card cannot drift off-brand.

DESIGN NOTES (rewritten 2026-08-16 after the first pass was, correctly, called unpolished):

  The first version centred every single element - headline, sub, cells, captions, footer.
  Centre-everything is the most reliable tell of a machine-made layout: it has no grid, no
  asymmetry, and no hierarchy beyond font size. This version is built on a left margin with
  a single measured column, and only the kicker rule is allowed to break it.

  The spreadsheet card also drew two rounded rectangles and then EXPLAINED in a caption that
  they were cells. If the whole idea rests on something reading as a spreadsheet, it has to
  actually look like one - so this version draws real chrome: column letters, row numbers,
  gridlines, a selection outline, and above all a formula bar. The formula bar is the point.
  It is literally where the truth about a cell lives, and where the two differ. Show it and
  no caption is needed.

  TYPE: one serif display face (Cambria) for the headline only, one sans (Calibri) for
  everything structural, one mono (Consolas) for anything that is data. Three roles, no
  overlap. Uppercase micro-labels carry letter-spacing, drawn by hand since PIL has none.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tokens import LIGHT
except Exception:
    LIGHT = {}

BG     = LIGHT.get('bg',      '#F5F3ED')
PANEL  = LIGHT.get('panel',   '#FFFDF8')
WELL   = LIGHT.get('well',    '#EAE6DA')
SUNK   = LIGHT.get('sunk',    '#E2DDCE')
INK    = LIGHT.get('ink',     '#191713')
INK2   = LIGHT.get('ink-2',   '#3D3934')
MUT    = LIGHT.get('mut',     '#6B6459')
FAINT  = LIGHT.get('faint',   '#938A7B')
LINE   = LIGHT.get('line',    '#DDD8CA')
RULE   = LIGHT.get('rule',    '#C2BAA7')
ACCENT = LIGHT.get('accent',  '#8A6413')
OK     = LIGHT.get('ok',      '#2A6A4F')
BAD    = LIGHT.get('bad',     '#98283C')

F = "C:/Windows/Fonts/"
def font(n, s): return ImageFont.truetype(F + n, s)

DISPLAY, DISPLAY_R = "cambriab.ttf", "cambria.ttc"
MONO, MONO_B       = "consola.ttf", "consolab.ttf"
SANS, SANS_B       = "calibri.ttf", "calibrib.ttf"

W = H = 1080
M = 96                      # left margin - the whole layout hangs off this

LOGO_DARK, LOGO_B1, LOGO_B2 = '#16181d', '#6FA8FF', '#BC8BFF'
RAINBOW = ['#fb6f6a', '#ffab3f', '#ffd93d', '#54cf8e', '#3aa5ff', '#8f7cf6']


def _lerp(c1, c2, t):
    a = tuple(int(c1[i:i+2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i:i+2], 16) for i in (1, 3, 5))
    return tuple(int(a[i] + (b[i]-a[i]) * t) for i in range(3))


def tracked(d, xy, s, f, fill, sp=2.6, anchor_left=True):
    """Letter-spaced text. PIL has no tracking, and uppercase micro-labels look cramped
    without it, so it is drawn glyph by glyph."""
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + sp
    return x


def wrap(d, s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def draw_logo(d, x, top, target_w=250, align_left=True):
    """The real lockup, rebuilt from the inline SVG the live site serves. Consolas is in that
    SVG's own declared font stack, so this is the site's fallback, not my substitution."""
    s = target_w / 315.6
    hb, hbar, r = 43*s, 4*s, 11*s
    x0 = x if align_left else x - target_w/2
    d.rounded_rectangle([x0, top, x0+target_w, top+hb], r, fill='#FFFFFF')
    dw = 83*s
    d.rounded_rectangle([x0, top, x0+dw+r, top+hb], r, fill=LOGO_DARK)
    d.rectangle([x0+dw, top, x0+dw+r, top+hb], fill='#FFFFFF')
    d.rounded_rectangle([x0, top, x0+target_w, top+hb], r, outline=RULE, width=1)
    by = top + hb
    for px in range(int(target_w)):
        t = px/max(1, target_w-1); seg = t*(len(RAINBOW)-1)
        i = min(int(seg), len(RAINBOW)-2)
        d.line([(x0+px, by), (x0+px, by+hbar)], fill=_lerp(RAINBOW[i], RAINBOW[i+1], seg-i))
    fs = max(9, int(17*s))
    fl, fw = font(MONO_B, fs), font(MONO, fs)
    ty = top + hb/2
    bx = x0 + 19*s
    for txt, col in (("{", LOGO_B1), ("a_w", '#FFFFFF'), ("}", LOGO_B2)):
        d.text((bx, ty), txt, font=fl, fill=col, anchor="lm")
        bx += d.textlength(txt, font=fl)
    d.text((x0 + 101*s, ty), "automated_workflow", font=fw, fill=LOGO_DARK, anchor="lm")


def kicker(d, y, text, col=ACCENT):
    """Small brass rule + letter-spaced label. The one element allowed to sit above the grid."""
    d.line([(M, y), (M + 46, y)], fill=col, width=3)
    tracked(d, (M + 60, y - 9), text, font(SANS_B, 21), col, sp=3.0)


def footer(d, left_text):
    d.line([(M, H - 150), (W - M, H - 150)], fill=LINE, width=2)
    draw_logo(d, M, H - 128, target_w=232)
    f = font(SANS, 23)
    for i, ln in enumerate(left_text):
        d.text((W - M, H - 124 + i*30), ln, font=f, fill=FAINT, anchor="ra")


# =====================================================================================
# CARD 1 - the typed-over total, told through the formula bar
# =====================================================================================
def fx_row(d, x, y, w, cell_ref, formula, value, tag, tag_col, live):
    """One spreadsheet row: a real formula bar, then the cell as the grid renders it."""
    lbl = font(SANS_B, 20)
    tracked(d, (x, y), cell_ref, lbl, FAINT, sp=2.4)

    # --- formula bar: fx gutter + the actual contents of the cell ---
    by = y + 34
    bh = 68
    d.rounded_rectangle([x, by, x + w, by + bh], 8, fill=PANEL, outline=RULE, width=2)
    d.rectangle([x + 2, by + 2, x + 74, by + bh - 2], fill=WELL)
    d.line([(x + 74, by + 2), (x + 74, by + bh - 2)], fill=RULE, width=2)
    d.text((x + 38, by + bh/2), "fx", font=font(DISPLAY_R, 30), fill=MUT, anchor="mm")
    d.text((x + 98, by + bh/2), formula, font=font(MONO_B, 31),
           fill=(INK if live else BAD), anchor="lm")

    # --- how the grid renders it: column letter, row number, the selected cell ---
    gy = by + bh + 22
    gh = 76
    colw = 300
    d.rectangle([x, gy, x + 62, gy + 30], fill=SUNK)
    d.rectangle([x + 62, gy, x + 62 + colw, gy + 30], fill=SUNK)
    d.text((x + 31, gy + 15), "", font=font(SANS, 18), fill=MUT, anchor="mm")
    d.text((x + 62 + colw/2, gy + 15), "D", font=font(SANS_B, 19), fill=MUT, anchor="mm")
    d.rectangle([x, gy + 30, x + 62, gy + 30 + gh], fill=SUNK)
    d.text((x + 31, gy + 30 + gh/2), "20", font=font(SANS, 20), fill=MUT, anchor="mm")
    d.rectangle([x + 62, gy + 30, x + 62 + colw, gy + 30 + gh], fill=PANEL)
    d.rectangle([x + 62, gy + 30, x + 62 + colw, gy + 30 + gh],
                outline=(ACCENT if not live else RULE), width=(3 if not live else 2))
    d.text((x + 62 + colw - 22, gy + 30 + gh/2), value, font=font(MONO_B, 42),
           fill=INK, anchor="rm")

    # verdict, set against the cell rather than under it
    tx = x + 62 + colw + 44
    tracked(d, (tx, gy + 42), tag, font(SANS_B, 22), tag_col, sp=2.2)
    sub = "recalculates when the data changes" if live else "frozen the moment it was typed"
    d.text((tx, gy + 74), sub, font=font(SANS, 23), fill=MUT)
    return gy + 30 + gh


def build_typed(out_path):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    kicker(d, 104, "WHAT THE CELL ACTUALLY CONTAINS")

    d.text((M, 140), "Both of these", font=font(DISPLAY, 76), fill=INK)
    d.text((M, 218), "say $48,200.", font=font(DISPLAY, 76), fill=INK)
    d.text((M, 316), "The grid shows you the value. It never shows you",
           font=font(DISPLAY_R, 32), fill=MUT)
    d.text((M, 356), "how the value got there.", font=font(DISPLAY_R, 32), fill=MUT)

    fx_row(d, M, 436, 760, "SHEET  ·  CELL D20", "=SUM(D2:D19)", "$48,200",
           "LIVE", OK, live=True)
    fx_row(d, M, 686, 760, "SHEET  ·  CELL D20", "48200", "$48,200",
           "TYPED", BAD, live=False)

    footer(d, ["Free tool. Shows which totals are typed.",
               "automatedworkflowllc.com/skeleton"])
    img.save(out_path, "PNG", optimize=True)
    return out_path


# =====================================================================================
# CARD 2 - cardinality
# =====================================================================================
def build_cardinality(out_path):
    """Claims traced to the 'A Predictable Bill' summary. NB: the source states 10x the
    SERIES, and says a volume-based bill charges the two the SAME - it states no price
    ratio, so the card must not imply one."""
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    kicker(d, 104, "WHY THE BILL SURPRISES YOU")

    d.text((M, 140), "Same 30 readings.", font=font(DISPLAY, 74), fill=INK)
    d.text((M, 218), "One is quietly expensive.", font=font(DISPLAY, 74), fill=INK)
    d.text((M, 320), "Identical data. One label different.",
           font=font(DISPLAY_R, 32), fill=MUT)

    x, y, w = M, 400, W - M*2
    rows = [("request latency", "order_id", "30", "EXPENSIVE", BAD),
            ("orders latency",  "region",   "3",  "HEALTHY",   OK)]
    hy = y
    d.line([(x, hy), (x + w, hy)], fill=RULE, width=2)
    for lab, cx in (("MEASUREMENT", x), ("LABEL USED", x + 340),
                    ("SERIES CREATED", x + 590)):
        tracked(d, (cx, hy + 18), lab, font(SANS_B, 19), FAINT, sp=2.4)
    d.line([(x, hy + 52), (x + w, hy + 52)], fill=LINE, width=2)

    ry = hy + 52
    for name, lab, series, verdict, col in rows:
        rh = 112
        d.text((x, ry + rh/2 - 4), name, font=font(SANS, 32), fill=INK2, anchor="lm")
        d.text((x + 340, ry + rh/2 - 4), lab, font=font(MONO_B, 30), fill=col, anchor="lm")
        d.text((x + 590, ry + rh/2 - 4), series, font=font(MONO_B, 46), fill=col, anchor="lm")
        tracked(d, (x + 700, ry + rh/2 - 15), verdict, font(SANS_B, 22), col, sp=2.2)
        ry += rh
        d.line([(x, ry), (x + w, ry)], fill=LINE, width=2)

    fp = font(SANS, 31)
    yy = ry + 46
    for ln in wrap(d, "Label a measurement with something unique to every event and you create "
                      "a new series to store and search, forever, for every event.", fp, w):
        d.text((M, yy), ln, font=fp, fill=INK2); yy += 42

    d.rectangle([M, yy + 26, M + 5, yy + 96], fill=ACCENT)
    d.text((M + 26, yy + 28), "A bill based on volume charges these two the same",
           font=font(SANS_B, 30), fill=INK)
    d.text((M + 26, yy + 66), "and cannot tell you which one is ruining you.",
           font=font(SANS_B, 30), fill=INK)

    footer(d, ["Built and running as a pilot.",
               "OpenTelemetry · Go · ClickHouse"])
    img.save(out_path, "PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "typed"
    out = sys.argv[2] if len(sys.argv) > 2 else "social-card.png"
    print(build_cardinality(out) if which == "cardinality" else build_typed(out))
