"""Shared paths, groupings and helpers for the idrisi project.

Raw inputs (raw/, read in place, never modified; steps 03 onward and the release run without raw/):
  raw/tabula_rogeriana_miller1928.jpg
      Konrad Miller's 1928 reconstruction of al-Idrisi's world map of 1154 (the Tabula Rogeriana), 12,999 x 5,958 px,
      south at the top. Wikimedia Commons "Tabula Rogeriana 1929 copy by Konrad Miller.jpg". Public domain.
  raw/dozy_degoeje_1866_afrique_espagne_ocr.txt, raw/dozy_degoeje_1866_meta.json
      Dozy, R. and de Goeje, M. J. (1866) Description de l'Afrique et de l'Espagne par Edrisi. Leiden: Brill.
      Internet Archive OCR text (bub_gb_6EMNNqPF2zAC), public domain mark. Al-Idrisi's route distances, in French.
  raw/thurayya/master/places.geojson, routes.json
      al-Thurayya Gazetteer (M. Seydi and M. Romanov), places and routes of the early Islamic world from G. Cornu's
      Atlas du monde arabo-islamique (1983), with modern coordinates. CC BY 4.0 (raw/thurayya/DATA-LICENSE.md).
  /home/claude/rawstore/mappa-mundi/pleiades/places.csv, names.csv
      Pleiades gazetteer of ancient places, version 4.1. CC BY 3.0.
  /home/claude/newdata/raw/geo/ne_*.geojson
      Natural Earth countries, land and populated places. Public domain.
  /home/claude/studies/mappa-mundi/data/results.json
      My own Hereford Mappa Mundi study (same method), for the comparison; the numbers used are copied into
      data/hereford.json by 02_geo.py.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("ID_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("ID_GEO", "/home/claude/newdata/raw/geo")
PLEIADES = os.environ.get("ID_PLEIADES", "/home/claude/rawstore/mappa-mundi/pleiades")
HEREFORD = os.environ.get("ID_HEREFORD", "/home/claude/studies/mappa-mundi/data/results.json")
FONTS = os.environ.get("ID_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
WORK = os.path.join(os.environ.get("IDTMP", "/dev/shm/idrisi"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK, IMG):
    os.makedirs(d, exist_ok=True)

SLUG = "idrisi"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23882607"                     # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/idrisi/"               # filled in by the publisher
HEREFORD_PAGE = "https://maps.tristanhotham.com/mappa-mundi/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
PLEIADES_VER = "4.1"
MILLER_URL = "https://commons.wikimedia.org/wiki/File:Tabula_Rogeriana_1929_copy_by_Konrad_Miller.jpg"
DOZY_IA = "https://archive.org/details/bub_gb_6EMNNqPF2zAC"
THURAYYA_URL = "https://github.com/althurayya/althurayya.github.io"

# The image as drawn: south at the top. Size of Miller's sheet as scanned.
IMG_W, IMG_H = 12999, 5958

# Regions used in the analysis, in display order, with colours (west to east, then north to south)
REGIONS = [("England", "#2E8A6E"), ("France and the Low Countries", "#5D8F9E"), ("Iberia", "#B07A12"),
           ("Central and Eastern Europe", "#6E4C9A"), ("Italy and Corsica", "#2F5FA7"), ("Sicily and Malta", "#C2412D"),
           ("Greece and the Balkans", "#3B7DD8"), ("Morocco and Algeria", "#9C6B3A"), ("Tunisia and Libya", "#D46A8C"),
           ("Egypt and Nubia", "#E0A11B"), ("Syria and Palestine", "#8E3B2E"), ("Anatolia", "#7A9A3A"),
           ("Iraq and the Jazira", "#3B3B3B"), ("Arabia", "#C9852B"), ("Iran and the Caucasus", "#1F7A8C"),
           ("Central Asia and Afghanistan", "#7E5A9B"), ("Sind and India", "#A23B72"), ("West Africa", "#8C8478")]
RCOL = dict(REGIONS)
RNAMES = [r for r, _ in REGIONS]
# Groups for the headline comparison: the Mediterranean world Roger's court knew well, against the far north and east
GROUPS = {"Mediterranean": ["Sicily and Malta", "Italy and Corsica", "Iberia", "Morocco and Algeria", "Tunisia and Libya",
                            "Greece and the Balkans", "Syria and Palestine", "Egypt and Nubia", "Anatolia"],
          "Northern Europe": ["England", "France and the Low Countries", "Central and Eastern Europe"],
          "Asia beyond the Euphrates": ["Iraq and the Jazira", "Iran and the Caucasus", "Central Asia and Afghanistan", "Sind and India", "Arabia"]}

JER = (31.7767, 35.2345)
PALERMO = (38.116, 13.361)
ARAB_MILE_KM = (1.92, 2.0)          # range for the Arab mile used in the text (4,000 cubits); see paper


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "abs": return f"{abs(round(float(v))):,}"
    raise ValueError(f)


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


def bearing(lat1, lon1, lat2, lon2):
    """Initial great-circle bearing from point 1 to point 2, degrees clockwise from north."""
    import numpy as np
    p1, p2, dl = np.radians(lat1), np.radians(lat2), np.radians(lon2 - lon1)
    x = np.sin(dl) * np.cos(p2); y = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return (np.degrees(np.arctan2(x, y)) + 360) % 360


def north_up(x, y):
    """Pixel on the map as drawn (south up) to the map turned through 180 degrees (north up, east right)."""
    return IMG_W - x, IMG_H - y


# Web tiles: the image as drawn is laid on Web Mercator pixel space at zoom TZ, at full resolution, centred.
# TZ = 7 leaves room around the image, so the whole sheet fits a phone screen at zoom 0.
TZ = 7
TWORLD = 256 * 2 ** TZ
TX0, TY0 = (TWORLD - IMG_W) // 2, (TWORLD - IMG_H) // 2


def px2ll(x, y):
    """Pixel on the image as drawn to the pseudo longitude and latitude used to show the image in MapLibre."""
    import math
    X, Y = TX0 + x, TY0 + y
    lon = X / TWORLD * 360 - 180
    n = math.pi - 2 * math.pi * Y / TWORLD
    return lon, math.degrees(math.atan(math.sinh(n)))
