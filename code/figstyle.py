"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines, and the map image turned north up."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from PIL import Image
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#67615A", "axes.labelcolor": "#1F1D1A",
                     "xtick.color": "#67615A", "ytick.color": "#67615A"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F1E6", "#1F1D1A", "#67615A", "#E6DDC8", "#DED3BC", "#E7EDEF"
LAPIS, SAFF, RED, GREEN = "#23468C", "#C98A12", "#B4372A", "#2E7D5B"
W = jload(f"{DATA}/world.json")
SCALE = 4000 / IMG_W


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


def world(ax, ext, land=LAND, ec="#FFFFFF", lw=.4, sea=SEA, aspect_lat=None):
    """Plate carree map with the cosine of the mid latitude as aspect, so shapes are not squashed."""
    ax.set_facecolor(sea)
    for f in W["features"]:
        for r in rings(f["geometry"]):
            ax.add_patch(MPoly(r, closed=True, fc=land, ec=ec, lw=lw, zorder=1))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect(1 / np.cos(np.radians(aspect_lat if aspect_lat is not None else (ext[2] + ext[3]) / 2)))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def oldmap(north=True):
    """The 4,000 px web image of the map; turned north up by default. Pixel (x, y) as drawn maps to
    ((IMG_W - x) * SCALE, (IMG_H - y) * SCALE) on the turned image."""
    im = Image.open(f"{IMG}/idrisi_4000.jpg")
    return im.rotate(180) if north else im


def nu(x, y):
    return (IMG_W - np.asarray(x)) * SCALE, (IMG_H - np.asarray(y)) * SCALE


def crop_full(x0, y0, x1, y1, north=True):
    """Full-resolution crop of the map (pixels as drawn), pieced together from the full-resolution web tiles in img/tiles."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    out = Image.new("RGB", (x1 - x0, y1 - y0), (232, 220, 190))
    for tx in range((TX0 + x0) // 256, (TX0 + x1 - 1) // 256 + 1):
        for ty in range((TY0 + y0) // 256, (TY0 + y1 - 1) // 256 + 1):
            fn = f"{IMG}/tiles/{TZ}/{tx}/{ty}.webp"
            if os.path.exists(fn):
                out.paste(Image.open(fn), (tx * 256 - TX0 - x0, ty * 256 - TY0 - y0))
    return out.rotate(180) if north else out
