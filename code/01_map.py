"""The map image: town symbols, my readings of the labels, the climate lines, and the web images.

  * Miller drew every town as a small brown disc with spokes. I find them automatically (a colour mask, a morphological
    opening and a test for round blobs of the right size) and snap each of my by-eye positions in
    data/map_positions.csv to the nearest disc within 20 pixels. Positions with no disc that close keep my reading.
  * The seven climates are horizontal bands bounded by red lines; the ten sections are vertical. I find the red lines
    in each section (a long horizontal opening of a red mask) and record, for every section, the row of the equator
    line and of each boundary between climates (data/climate_lines.json). Where a line is not found in a section, the
    median over the other sections is used.
  * Outputs: data/map_points.csv (each reading with its snapped pixel on the image as drawn, on the image turned north
    up, its climate and section), data/climate_lines.json, the web tile pyramid img/tiles/{z}/{x}/{y}.webp (WebP, to keep the repository small) (the image as
    drawn, at full resolution at zoom 7), img/idrisi_2000.jpg and img/idrisi_4000.jpg (whole map, for the fallback view
    and the figures)."""
import shutil
import numpy as np, pandas as pd
from PIL import Image
from scipy import ndimage as nd
from common import *

Image.MAX_IMAGE_PIXELS = None
SRC = f"{RAW}/tabula_rogeriana_miller1928.jpg"
im = Image.open(SRC).convert("RGB")
assert im.size == (IMG_W, IMG_H), im.size

# ---------- town symbols ----------
discs = []
STEP, PAD = 1300, 40
for x0 in range(0, IMG_W, STEP):
    for y0 in range(0, IMG_H, STEP):
        bx0, by0 = max(0, x0 - PAD), max(0, y0 - PAD)
        a = np.asarray(im.crop((bx0, by0, min(IMG_W, x0 + STEP + PAD), min(IMG_H, y0 + STEP + PAD)))).astype(np.int16)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        m = (R + G + B < 330) & (B < R)                                     # dark brown ink and fill
        m = nd.binary_closing(m, iterations=2)
        op = nd.binary_opening(m, structure=np.ones((9, 9)))
        lab, n = nd.label(op)
        for i, s in enumerate(nd.find_objects(lab), 1):
            h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
            if not (13 <= h <= 34 and 13 <= w <= 34 and abs(h - w) <= 7):
                continue
            fill = (lab[s] == i).mean()
            if not .55 <= fill <= .95:
                continue
            cy, cx = nd.center_of_mass(lab[s] == i)
            X, Y = bx0 + s[1].start + cx, by0 + s[0].start + cy
            if x0 <= X < x0 + STEP and y0 <= Y < y0 + STEP:
                discs.append((X, Y))
D = np.array(discs)
print("town discs found by shape", len(D))
# second detector: discs touching rivers or labels are missed above, so match a template made from the clean discs
import cv2
gray = np.asarray(im.convert("L")).astype(np.float32)
pat = [gray[int(round(y)) - 15:int(round(y)) + 16, int(round(x)) - 15:int(round(x)) + 16] for x, y in D
       if 15 <= x < IMG_W - 16 and 15 <= y < IMG_H - 16]
T = np.mean(pat, 0); T = (T + np.rot90(T) + np.rot90(T, 2) + np.rot90(T, 3)) / 4
score = cv2.matchTemplate(gray, T.astype(np.float32), cv2.TM_CCOEFF_NORMED)
pk = np.argwhere((score == cv2.dilate(score, np.ones((15, 15), np.uint8))) & (score > .55))
D2 = pk[:, ::-1].astype(float) + 15
far = np.array([np.hypot(D[:, 0] - x, D[:, 1] - y).min() > 8 for x, y in D2])
D = np.vstack([D, D2[far]])
print("plus template matches", int(far.sum()), "; all", len(D))
del gray, score

pos = pd.read_csv(f"{DATA}/map_positions.csv")
sx, sy, sd = [], [], []
for r in pos.itertuples():
    d = np.hypot(D[:, 0] - r.x, D[:, 1] - r.y)
    j = int(d.argmin())
    if d[j] <= 20:
        sx.append(round(float(D[j, 0]), 1)); sy.append(round(float(D[j, 1]), 1)); sd.append(round(float(d[j]), 1))
    else:
        sx.append(float(r.x)); sy.append(float(r.y)); sd.append(None)
pos["x_snap"], pos["y_snap"], pos["snap_px"] = sx, sy, sd
print("snapped", pos.snap_px.notna().sum(), "of", len(pos), "; median shift", pos.snap_px.median())
dup = pos[pos.duplicated(["x_snap", "y_snap"], keep=False)]
assert dup.empty, dup[["label", "identification", "x", "y"]].values.tolist()   # two readings on one disc: a misreading

# ---------- climate and section lines ----------
NOM = [530, 1300, 2050, 2800, 3535, 4300, 5050]       # rough rows of the equator and the six boundaries between climates
lines = []
for k, x0 in enumerate(range(0, IMG_W, STEP)):
    a = np.asarray(im.crop((x0, 0, min(IMG_W, x0 + STEP), IMG_H))).astype(np.int16)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    o = nd.binary_opening((R > 140) & (R - G > 70) & (R - B > 70), structure=np.ones((1, 201)))
    prof = o.sum(1)
    rows = np.where(prof > 300)[0]
    grp = []
    for r_ in rows:
        if grp and r_ - grp[-1][-1] <= 6: grp[-1].append(r_)
        else: grp.append([r_])
    found = [float(np.mean(g)) for g in grp]
    row = []
    for nmn in NOM:
        c = [f for f in found if abs(f - nmn) < 130]
        row.append(round(min(c, key=lambda f: abs(f - nmn)), 1) if c else None)
    lines.append({"x0": x0, "x1": min(IMG_W, x0 + STEP), "rows": row})
for i in range(len(NOM)):
    med = float(np.median([l["rows"][i] for l in lines if l["rows"][i] is not None]))
    for l in lines:
        if l["rows"][i] is None:
            l["rows"][i] = round(med, 1); l.setdefault("filled", []).append(i)
BOTTOM = 5800                                            # the map's lower frame (north edge of climate VII)
TOP = 175                                                # the upper frame, beyond the equator
CL = {"sections": lines, "bottom": BOTTOM, "top": TOP, "nominal": NOM,
      "note": "rows on the image as drawn (south up): rows[0] is the equator line, rows[k] the boundary between climate k and k+1"}
jsave(CL, f"{DATA}/climate_lines.json", indent=1)
for l in lines:
    print(l["x0"], l["rows"], l.get("filled", ""))


def climate(x, y):
    l = lines[min(len(lines) - 1, int(x // STEP))]["rows"]
    if y < l[0]: return 0                               # south of the equator
    for k in range(1, 7):
        if y < l[k]: return k
    return 7


pos["climate"] = [climate(x, y) for x, y in zip(pos.x_snap, pos.y_snap)]
pos["section"] = [10 - min(9, int(x // STEP)) for x in pos.x_snap]     # sections numbered from the west (right of the image as drawn)
pos["x_north"], pos["y_north"] = north_up(pos.x_snap, pos.y_snap)
pos.round(1).to_csv(f"{DATA}/map_points.csv", index=False)
print(pos.climate.value_counts().sort_index().to_dict())

# ---------- web images ----------
for w in (2000, 4000):
    im.resize((w, round(IMG_H * w / IMG_W)), Image.LANCZOS).save(f"{IMG}/idrisi_{w}.jpg", quality=78 if w == 2000 else 72, optimize=True, progressive=True)
T = f"{IMG}/tiles"
if os.path.exists(T):
    shutil.rmtree(T)
canvas = im
for z in range(TZ, 0, -1):
    sc = 2 ** (TZ - z)
    W_, H_ = (IMG_W + sc - 1) // sc, (IMG_H + sc - 1) // sc
    lvl = canvas if sc == 1 else im.resize((W_, H_), Image.LANCZOS)
    ox, oy = TX0 / sc, TY0 / sc
    tx0, ty0 = int(ox // 256), int(oy // 256)
    tx1, ty1 = int((ox + W_ - 1) // 256), int((oy + H_ - 1) // 256)
    n = 0
    for tx in range(tx0, tx1 + 1):
        os.makedirs(f"{T}/{z}/{tx}", exist_ok=True)
        for ty in range(ty0, ty1 + 1):
            tile = Image.new("RGB", (256, 256), (232, 220, 190))
            px, py = int(round(tx * 256 - ox)), int(round(ty * 256 - oy))
            cx0, cy0, cx1, cy1 = max(0, px), max(0, py), min(W_, px + 256), min(H_, py + 256)
            tile.paste(lvl.crop((cx0, cy0, cx1, cy1)), (cx0 - px, cy0 - py))
            tile.save(f"{T}/{z}/{tx}/{ty}.webp", "WEBP", quality=60 if z == TZ else 68, method=6)
            n += 1
    print("zoom", z, "tiles", n)
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(T) for f in fs)
print("tiles MB", round(tot / 1e6, 1))
jsave({"tz": TZ, "tworld": TWORLD, "tx0": TX0, "ty0": TY0, "img_w": IMG_W, "img_h": IMG_H, "minzoom": 1, "maxzoom": TZ,
       "n_discs": len(D), "snapped": int(pos.snap_px.notna().sum()), "snap_median_px": float(pos.snap_px.median()),
       "web": {"small": "img/idrisi_2000.jpg", "large": "img/idrisi_4000.jpg"}}, f"{DATA}/fit.json", indent=1)
