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


# --- sample-data safety -----------------------------------------------------
# Two demo workbooks were seeded in July from the real Gainesville outreach
# tracker, and one of them stated that two named real companies lost money on a
# job -- against invented figures. Harmless in a private sales file, and not
# publishable the moment the same file is served on a public URL. Found on
# 2026-08-08, one step before publishing.
#
# The trap is that nothing about those files was wrong; they were correct for
# the job they were built for. Only their destination changed, and nobody
# re-reads a finished artifact when the only change is where it lives. So the
# check cannot live in anyone's memory -- it runs at build time, every time.
REAL_CONTACTS = (
    'Wilson Exterior', 'Premier Lawn Care', 'Tindale Pest', 'Getter Done Fence',
    'Kind Touch Cleaning', 'Loblolly Landscaping', 'Paynes Prairie Landscaping',
    'Gainesville Lawnscaping', 'Buckman Hardware', 'Rocky Point Storage',
    'Hawthorne Trail Cycles', 'Osprey Point Cafe', 'Crossroads Realty',
    'Invictus Property', 'Haile Village Realty', 'Millhopper Vet Supply',
    'Santa Fe Print Shop', 'Scharnagl', 'Ocala Central Vet', 'Cross Keys',
    'Pattison', 'ABC Waste', 'Riley Welding', 'CC Restoration',
    'Georgia Janitorial',
)


def assert_no_real_contacts(rows, where: str) -> None:
    """Refuse to build a public sample containing a real business name.

    `rows` is any nested structure of sample data; it is stringified whole, so
    a name buried in a note or an address column is still caught.
    """
    blob = str(rows)
    hits = sorted({n for n in REAL_CONTACTS if n.lower() in blob.lower()})
    if hits:
        raise SystemExit(
            f'REFUSING TO BUILD {where}: sample data contains real business '
            f'name(s) from the outreach tracker: {", ".join(hits)}. '
            'Replace with fictional names before publishing.')
