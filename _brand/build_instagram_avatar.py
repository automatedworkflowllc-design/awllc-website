# Build the Instagram profile picture from the LIVE app icon's {a_w} glyph.
#
# WHY NOT JUST UPLOAD icon-512.png. Instagram renders a profile picture as a CIRCLE, and the
# app icon is a rounded square: a parchment card holding a monitor with a bezel and a stand.
# Inscribed in a circle the bezel corners clip, and at the size this is actually seen -- ~110px
# on a profile, 32px beside a comment -- the monitor chrome turns to mud. The brand notes are
# explicit that the retro computer is an ACCENT, not the trust mark. The trust mark is {a_w}.
#
# So this takes the real glyph out of the shipped icon rather than redrawing it -- same pixels,
# same identity -- and rebuilds it full-bleed on the screen colour, sized to sit well inside the
# circular crop.
#
# The glyph is extracted as a MASK rather than cropped as a rectangle. Cropping would carry the
# source's own glow gradient with it and leave a visible seam against a new background.
import os
import pathlib as _pl
from PIL import Image, ImageDraw, ImageFilter

ROOT = _pl.Path(__file__).resolve().parents[1]
SRC = ROOT / 'icon-512.png'
OUT = ROOT / '_brand' / 'instagram-avatar.png'

SIZE = 1080                      # Instagram stores up to 320 but accepts and downsamples large
SCALE = 3                        # integer, so pixel-art edges stay crisp under NEAREST

# Measured off icon-512.png rather than guessed: the bright-cyan strokes of {a_w}.
GLYPH_BOX = (123, 220, 393, 323)   # x0, y0, x1, y1  (270 x 103)

BG = (18, 22, 40)                # screen navy, a touch deeper than the icon's so the glow reads
CYAN = (120, 226, 240)           # the phosphor
GLOW = (70, 190, 214)

src = Image.open(SRC).convert('RGBA')
sp = src.load()

# ---- glyph -> 1-bit mask -------------------------------------------------
gx0, gy0, gx1, gy1 = GLYPH_BOX
gw, gh = gx1 - gx0, gy1 - gy0
mask = Image.new('L', (gw, gh), 0)
mp = mask.load()
on = 0
for y in range(gh):
    for x in range(gw):
        r, g, b, a = sp[gx0 + x, gy0 + y]
        if g > 200 and b > 200 and r < 160:
            mp[x, y] = 255
            on += 1
if on < 500:
    raise SystemExit('REFUSING: only %d glyph pixels found - the source icon or the '
                     'measured box changed, and a near-empty mask would ship a blank avatar' % on)

big = mask.resize((gw * SCALE, gh * SCALE), Image.NEAREST)

# ---- canvas --------------------------------------------------------------
img = Image.new('RGBA', (SIZE, SIZE), BG + (255,))

# Phosphor bloom behind the text, so it reads as a lit screen rather than flat type.
glow_layer = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow_layer)
gd.ellipse([SIZE * 0.10, SIZE * 0.20, SIZE * 0.90, SIZE * 0.80], fill=GLOW + (70,))
glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(SIZE * 0.11))
img = Image.alpha_composite(img, glow_layer)

# Soft halo traced from the glyph itself.
halo = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
hx = (SIZE - big.width) // 2
hy = (SIZE - big.height) // 2
halo.paste(GLOW + (150,), (hx, hy), big)
halo = halo.filter(ImageFilter.GaussianBlur(14))
img = Image.alpha_composite(img, halo)

# The glyph itself, crisp.
text_layer = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
text_layer.paste(CYAN + (255,), (hx, hy), big)
img = Image.alpha_composite(img, text_layer)

# Vignette: keeps the CRT feel without scanlines, which alias badly at 32px.
vig = Image.new('L', (SIZE, SIZE), 0)
ImageDraw.Draw(vig).ellipse([-SIZE * 0.18, -SIZE * 0.18, SIZE * 1.18, SIZE * 1.18], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(SIZE * 0.09))
dark = Image.new('RGBA', (SIZE, SIZE), (6, 8, 16, 255))
img = Image.composite(img, dark, vig)

img.convert('RGB').save(OUT, 'PNG', optimize=True)

# ---- checks --------------------------------------------------------------
w_frac = big.width / SIZE
print('glyph mask pixels: %d' % on)
print('glyph rendered:    %dx%d  (%.0f%% of canvas width)' % (big.width, big.height, w_frac * 100))
print('circle-safe:       %s' % ('yes - centred vertically, so the crop is widest exactly where '
                                 'the glyph sits' if w_frac < 0.80 else 'NO - too wide'))
print('saved:', OUT, '%.1f KB' % (OUT.stat().st_size / 1024))
