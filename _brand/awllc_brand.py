# -*- coding: utf-8 -*-
"""AWLLC brand tokens — SINGLE SOURCE OF TRUTH for Python sheet builders.

Mirrors the frozen BRAND object in awllc_reskin_all.gs (the /reskin pipeline)
and the CSS custom properties on the website. Import from here; never hardcode
a hex in a build script again. Drift between the three surfaces is exactly the
bug this file exists to prevent.

Provenance of every value below: either the .gs BRAND object or a --token in
the site's shared answer-page stylesheet. Nothing here is invented.
"""

# --- neutrals (from .gs BRAND) ---
PAPER      = "FFFFFF"   # BRAND.paper
PAPER_TINT = "FBFAF3"   # BRAND.paperTint  (site --paper)
WELL       = "F4F1E8"   # BRAND.well       (site --well)      tile / card fill
INK        = "211D14"   # BRAND.ink        (site --ink)       headers, dark bands
INK_SOFT   = "5C5645"   # BRAND.inkSoft    (site --ink-soft)  secondary text
INK_FAINT  = "6E6555"   # site --ink-faint                    footer wordmark
LINE       = "E4DFD1"   # BRAND.line       (site --line)      borders/rules
LINE_STRONG= "D8D2C2"   # site --line-strong
CHART_BAR  = "CBC5B1"   # BRAND.chartBar                      muted bar fill

# --- rainbow accent (from .gs BRAND.rainbow) ---
RAINBOW = ["E1483E", "F08A24", "EFC939", "4FAE4A", "3E7FD9", "9B4FB8"]

# --- semantic status colours ---
# GREEN is the site's --green token. AMBER/RED are deliberately NOT mapped onto
# the rainbow accents: those are bright decorative hues and fail as small status
# text on a light fill. These two stay as legible darkened signal colours and are
# the only values here without a 1:1 upstream token — documented, not accidental.
GREEN = "1E7A47"   # site --green
AMBER = "B45309"   # signal only
RED   = "B23B3B"   # signal only

# tinted status backgrounds (kept: functional, low-saturation, legible)
GREEN_BG = "E6F2EC"
AMBER_BG = "FBEFE0"
RED_BG   = "F6E7E7"

# --- typography (Sheets-safe families used by the .gs reskin) ---
FONT_SANS = "Manrope"
FONT_MONO = "Roboto Mono"

# --- aliases matching the sheet-builders' existing vocabulary (ALIASES) ---
# Kept so builders can `from awllc_brand import *` without renaming their locals.
MUTE     = INK_SOFT
CARD     = WELL
BANDBG   = LINE
WORDMARK = INK_FAINT
GREENBG  = GREEN_BG
REDBG    = RED_BG
AMBERBG  = AMBER_BG
