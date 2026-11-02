"""Geography: outlines for the page and the figures (Natural Earth 1:50m), a modern position for every place I read on
the map, checked against three gazetteers, al-Idrisi's own route distances, and the Hereford numbers for comparison.

  * Modern positions are mine (code/coords_hand.py). Each is checked against al-Thurayya (by the map's transliteration
    and by my identification), Pleiades (attested and romanised names) and Natural Earth towns (modern names). A match
    is a gazetteer point of the same name within 150 km; the distance from my point to the nearest match is recorded.
    Any match more than 30 km away is printed for review (I checked each one; none needed a change, see the printout).
  * Route distances: code/reading.py lists each distance, the OCR line it comes from and the words on that line; this
    step checks that the words really are on that line of the scan's text before using them.
  * Outputs: data/world.json, data/places.json (every located place with position on the map, modern position,
    region and gazetteer checks), data/routes.csv, data/hereford.json, data/sources.json."""
import difflib
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping
from common import *
import coords_hand, reading

iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats = []
for f in W50["features"]:
    gs = shape(f["geometry"]).simplify(0.04, preserve_topology=True)
    if gs.is_empty: continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso_of(f["properties"]), "name": f["properties"].get("NAME_EN") or f["properties"]["NAME"]},
                  "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")

# ---------- gazetteers ----------
TH = jload(f"{RAW}/thurayya/master/places.geojson")["features"]
THI = {}
for f in TH:
    c = f["properties"]["cornuData"]
    if c["top_type_hom"] in ("regions",) or c["toponym_search"].startswith("RoutPoint"):
        continue
    la, lo = float(c["coord_lat"]), float(c["coord_lon"])
    for v in re.split(r"[,/]", c["toponym_search"]) + [c["toponym_translit"]]:
        k = norm(v).replace("al ", "").replace(" ", "")
        if len(k) >= 3:
            THI.setdefault(k, []).append((c["toponym_search"], la, lo, c["cornu_URI"]))
THKEYS = sorted(THI)
NE = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
NEI = {}
for f in NE:
    p = f["properties"]
    for v in {norm(p["name"]), norm(p.get("nameascii") or ""), norm(p.get("namealt") or "")}:
        if v: NEI.setdefault(v, []).append((p["name"], p["latitude"], p["longitude"]))
pl = pd.read_csv(f"{PLEIADES}/places.csv", dtype=str, keep_default_na=False)
nm = pd.read_csv(f"{PLEIADES}/names.csv", dtype=str, keep_default_na=False)
pl = pl[(pl.representative_latitude != "") & (pl.representative_longitude != "")]
PL = {r.id: (r.title, float(r.representative_latitude), float(r.representative_longitude)) for r in pl.itertuples()}
PLI = {}
for r in nm.itertuples():
    for fm in (r.attested_form, r.romanized_form_1, r.romanized_form_2, r.romanized_form_3):
        for v in re.split(r"[,/;]", fm):
            if norm(v) and r.place_id in PL: PLI.setdefault(norm(v), set()).add(r.place_id)
for pid, (t, *_) in PL.items():
    for v in re.split(r"[,/;]", re.sub(r"\([^)]*\)", "", t)):
        if norm(v): PLI.setdefault(norm(v), set()).add(pid)


def names_of(ident):
    parts = [ident.split(" (")[0]] + re.findall(r"\(([^)]*)\)", ident) + reading.GAZ_ALIASES.get(ident, [])
    out = set()
    for p in parts:
        for q in re.split(r",| on the | of ", p):
            q = re.sub(r"^(Old|capital|the) ", "", q.strip())
            if len(norm(q)) >= 3: out.add(norm(q))
    return out


def nearest(cands, la, lo, maxkm=150):
    best = None
    for name, a, b, *rest in cands:
        d = float(gc_km(la, lo, a, b))
        if d <= maxkm and (best is None or d < best[1]):
            best = (name, round(d, 1))
    return best


def check(ident, label, la, lo):
    keys = names_of(ident)
    ne = nearest([x for k in keys for x in NEI.get(k, [])], la, lo)
    plc = nearest([(PL[i][0], PL[i][1], PL[i][2]) for k in keys for i in PLI.get(k, ())], la, lo)
    tk = {norm(k).replace(" ", "") for k in keys} | {norm(label).replace("al ", "").replace(" ", "")}
    thc = [x for k in tk for x in THI.get(k, [])]
    for k in tk:                                           # close spellings of the map's own transliteration
        if len(k) >= 4:
            for m in difflib.get_close_matches(k, [x for x in THKEYS if x[:1] == k[:1]], n=4, cutoff=.8):
                thc += THI[m]
    th = nearest(thc, la, lo)
    return ne, plc, th


pos = pd.read_csv(f"{DATA}/map_points.csv")
rows, review = [], []
for r in pos.itertuples():
    la, lo, reg = coords_hand.C[r.identification]
    ne, plc, th = check(r.identification, r.label, la, lo)
    ds = [g[1] for g in (ne, plc, th) if g]
    if ds and min(ds) > 30:
        review.append(f"{r.identification}: nearest gazetteer match {min(ds)} km (NE {ne}, Pleiades {plc}, al-Thurayya {th})")
    rows.append({"label": r.label, "identification": r.identification, "conf": r.conf, "region": reg, "lat": la, "lon": lo,
                 "x": r.x_snap, "y": r.y_snap, "x_north": r.x_north, "y_north": r.y_north, "snap_px": None if pd.isna(r.snap_px) else r.snap_px,
                 "climate": int(r.climate), "section": int(r.section),
                 "thurayya": th[0] if th else "", "thurayya_km": th[1] if th else None, "pleiades": plc[0] if plc else "",
                 "pleiades_km": plc[1] if plc else None, "naturalearth": ne[0] if ne else "", "naturalearth_km": ne[1] if ne else None})
P = pd.DataFrame(rows)
P["checked"] = P[["thurayya_km", "pleiades_km", "naturalearth_km"]].notna().any(axis=1)
P["check_km"] = P[["thurayya_km", "pleiades_km", "naturalearth_km"]].min(axis=1)
jsave(P.to_dict("records"), f"{DATA}/places.json", indent=0)
print("places", len(P), "checked in a gazetteer", int(P.checked.sum()), "; by gazetteer:",
      {g: int(P[g + "_km"].notna().sum()) for g in ("thurayya", "pleiades", "naturalearth")}, "; median distance", P.check_km.median())
print("\n".join(review) or "no gazetteer disagreements over 30 km")
print("not found in any gazetteer:", P[~P.checked].identification.tolist())

# ---------- route distances ----------
OCR = open(f"{RAW}/dozy_degoeje_1866_afrique_espagne_ocr.txt", encoding="utf-8").read().split("\n")
ws = lambda s: re.sub(r"\s+", " ", s).strip()
rr = []
for a, b, mi, dy, ln, quote in reading.ROUTES:
    assert ws(quote) in ws(OCR[ln - 1]), (ln, quote, OCR[ln - 1])
    ca = reading.EXTRA.get(a) or coords_hand.C[a][:2]; cb = reading.EXTRA.get(b) or coords_hand.C[b][:2]
    km = float(gc_km(ca[0], ca[1], cb[0], cb[1]))
    rr.append({"from": a, "to": b, "miles": mi, "days": dy, "ocr_line": ln, "ocr_text": ws(OCR[ln - 1]), "from_lat": ca[0], "from_lon": ca[1],
               "to_lat": cb[0], "to_lon": cb[1], "km": round(km, 1), "km_per_mile": round(km / mi, 3) if mi else None,
               "km_per_day": round(km / dy, 1) if dy else None})
RT = pd.DataFrame(rr)
RT.to_csv(f"{DATA}/routes.csv", index=False)
print("routes", len(RT), "with miles", RT.miles.notna().sum(), "with days", RT.days.notna().sum(),
      "; median km per mile", RT.km_per_mile.median(), "; median km per day", RT.km_per_day.median())

# ---------- Hereford numbers (my mappa-mundi study) for the comparison ----------
H = jload(HEREFORD)
jsave({"source": "Hotham (2026), The world according to the Hereford Mappa Mundi, data/results.json", "page": HEREFORD_PAGE,
       "located_real": H["located"]["unique_real"], "fit_r2": H["fit"]["r2"], "median_disp_km": H["fit"]["median_disp_km"],
       "bearing_median_err": H["bearing"]["median_abs_err"], "bearing_within45_pct": H["bearing"]["within45_pct"],
       "dist_spearman": H["dist"]["spearman"], "britain_names_pct": H["britain"]["names_pct"], "britain_stretch": H["britain"]["stretch"],
       "holyland_stretch": H["regions"]["Holy Land"]["stretch"], "britain_brg_err": H["regions"]["British Isles"]["median_abs_brg_err"],
       "north_africa_brg_err": H["regions"]["North Africa"]["median_abs_brg_err"], "india_stretch": H["regions"]["India and Central Asia"]["stretch"],
       "year": 1300}, f"{DATA}/hereford.json", indent=1)

meta = jload(f"{RAW}/dozy_degoeje_1866_meta.json")
lic = open(f"{RAW}/thurayya/DATA-LICENSE.md", encoding="utf-8").read()
assert "CC BY 4.0" in lic
jsave({"dozy": {"title": meta["title"], "date": meta["date"], "licence": meta["lic"], "ia": DOZY_IA, "ocr_lines": len(OCR)},
       "miller": {"url": MILLER_URL, "licence": "Public domain", "size": [IMG_W, IMG_H]},
       "thurayya": {"url": THURAYYA_URL, "licence": "CC BY 4.0", "places": len(TH)},
       "pleiades": {"version": PLEIADES_VER, "licence": "CC BY 3.0"}}, f"{DATA}/sources.json", indent=1)
