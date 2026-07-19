# -*- coding: utf-8 -*-
"""Export the pipeline-architecture diagram to PNG for off-site surfaces (LinkedIn).

SINGLE SOURCE OF TRUTH: the SVG lives in build-log/index.html and is read from
there. Nothing about the diagram is redefined in this file — a theme map only
substitutes colour tokens, so the light (site) and dark (LinkedIn) renders can
never drift apart in content. Editing the page updates both exports.

Usage:  python _brand/export_architecture.py
Out:    _scratch/architecture-light.png, _scratch/architecture-dark.png (1200x630)
"""
import io, os, re, subprocess, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'build-log', 'index.html')
OUT = os.path.join(ROOT, '_scratch')
W, H, SCALE = 1200, 630, 2

def find_chrome():
    for p in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
              os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe')]:
        if os.path.exists(p):
            return p
    return None

# Dark theme, ROLE-AWARE.
#
# A flat hex->hex map is wrong here and the first render proved it: #211D14 is
# both the ink colour AND the darkest surface. Substituting it globally turned
# every body label near-black on a near-black card - "Status = Active" and the
# trust rule were effectively invisible. Same failure shape as the "$0 lost"
# dashboard: one token silently serving two roles.
#
# So substitution happens per element, and what a colour becomes depends on
# whether it is painting TEXT or a SURFACE.
TEXT_DARK = {
    '#211D14': '#F2F0E9',   # primary ink -> light ink
    '#FBFAF3': '#F2F0E9',   # already-light ink stays light
    '#6E6555': '#95907F',   # faint label, lifted for dark contrast
    '#CBC5B1': '#A8A292',
    '#1E7A47': '#57C98A',   # green status, lifted
    '#B45309': '#E5A952',   # amber status, lifted
}
SURFACE_DARK = {
    '#FFFFFF': '#16181D',   # card
    '#F4F1E8': '#1F232A',   # well
    '#D8D2C2': '#343A44',   # border
    '#211D14': '#0E1014',   # header bar / deepest surface
    '#E6F2EC': '#123322',   # green pill
    '#FBEFE0': '#3A2A12',   # amber pill
    '#1E7A47': '#57C98A',   # the trust-rule accent bar
}
STROKE_DARK = {'#211D14': '#C9C4B6', '#D8D2C2': '#4A505B'}

def extract_svg():
    s = io.open(PAGE, encoding='utf-8').read()
    m = re.search(r'(<svg viewBox="0 0 860 452".*?</svg>)', s, re.S)
    if not m:
        sys.exit('architecture SVG not found in %s' % PAGE)
    return m.group(1)

def themed(svg, dark):
    """Recolour per element, choosing the map by the role the colour plays."""
    if not dark:
        return svg

    def sub_attr(tag, attr, table):
        def r(m):
            return '%s="%s"' % (attr, table.get(m.group(1).upper(), m.group(1)))
        return re.sub(r'%s="(#[0-9A-Fa-f]{6})"' % attr, r, tag)

    def recolour(m):
        tag = m.group(0)
        name = m.group(1).lower()
        if name == 'text' or name == 'tspan':
            return sub_attr(tag, 'fill', TEXT_DARK)
        # arrowheads live inside <marker> and read as strokes, not surfaces
        tag = sub_attr(tag, 'stroke', STROKE_DARK)
        return sub_attr(tag, 'fill', SURFACE_DARK)

    out = re.sub(r'<(\w+)[^>]*>', recolour, svg)
    # the marker arrowhead is a <path fill=...> but paints a stroke colour
    out = re.sub(r'(<marker[^>]*>\s*<path[^>]*fill=")#[0-9A-Fa-f]{6}',
                 r'\g<1>#C9C4B6', out)
    return out

def render(svg, path, dark):
    chrome = find_chrome()
    if not chrome:
        sys.exit('Chrome not found - cannot rasterise')
    bg = '#0E1014' if dark else '#FFFFFF'
    html = ('<html><body style="margin:0;width:%dpx;height:%dpx;background:%s;'
            'display:flex;align-items:center;justify-content:center">'
            '<div style="width:%dpx">%s</div></body></html>'
            % (W, H, bg, int(W * 0.94), themed(svg, dark)))
    tmp = os.path.join(OUT, '_render.html')
    io.open(tmp, 'w', encoding='utf-8').write(html)
    subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--hide-scrollbars', '--force-device-scale-factor=%d' % SCALE,
                    '--window-size=%d,%d' % (W, H), '--virtual-time-budget=6000',
                    '--screenshot=' + path, 'file:///' + tmp.replace('\\', '/')],
                   capture_output=True, timeout=120)
    os.remove(tmp)
    if not os.path.exists(path):
        sys.exit('render failed: %s' % path)
    try:
        from PIL import Image
        im = Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS)
        im.save(path, optimize=True)
    except ImportError:
        pass
    print('  %-34s %6.1f KB' % (os.path.basename(path), os.path.getsize(path) / 1024.0))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    svg = extract_svg()
    print('architecture SVG read from build-log/index.html (%d chars)' % len(svg))
    render(svg, os.path.join(OUT, 'architecture-light.png'), False)
    render(svg, os.path.join(OUT, 'architecture-dark.png'), True)
