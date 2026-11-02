"""Every number used anywhere (data/results.json), the reusable tables (data/located.csv, data/regions.csv,
data/climates.csv) and the page data (data/site.json). Reads only data/ (raw/ is not needed from here on).

Definitions
  * map frame: pixels on Miller's 1928 reconstruction. The map is drawn with south at the top; every measurement is made
    after turning it through 180 degrees (north up, east right). Map y is measured upwards in that frame.
  * global fit: the affine map (six numbers, least squares) from map position to longitude and latitude. Al-Idrisi's map
    is built on a grid of climates (latitude bands) and sections, so this is its natural comparison; the fitted
    position of a place is where the map puts it on the globe, and the residual (km) is how far that is from the place.
  * local error: for each place, an affine map fitted to its eight nearest neighbours (by true distance, the place itself
    left out) predicts where the place should be; the local error is the distance from there to the real place. It
    measures how well the map keeps the shape of each neighbourhood, whatever happens at the scale of the whole map.
  * bearing error (by region): for every pair of places in a region at least 100 km apart, the difference between the
    compass bearing on the map (north up) and the true initial bearing; the median of the absolute differences.
  * stretch: as in the Hereford study, the median of map distance over true distance for pairs at least 100 km apart in
    a region, relative to the same median over all pairs on the map (1 = the map's average scale). Because the map is
    a rectangular grid, east to west distances in the north are drawn too long by the grid alone; 'grid stretch' is
    the same figure computed for a perfect rectangular (plate carree) map, for comparison.
  * Hereford comparison: the similarity fit (rotation, uniform scale, shift) onto an azimuthal equidistant projection
    centred on Jerusalem, bearings and distances from Jerusalem, computed exactly as in the Hereford study.
  * warped grid: a smoothed thin plate spline from longitude and latitude to map position (and back), used only to draw
    the modern graticule on the old map and the old climate lines on the modern map."""
import itertools
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.stats import spearmanr
from scipy.interpolate import RBFInterpolator
from common import *
import warnings
warnings.filterwarnings("ignore")

P = pd.DataFrame(jload(f"{DATA}/places.json"))
CL = jload(f"{DATA}/climate_lines.json")
RT = pd.read_csv(f"{DATA}/routes.csv")
HF = jload(f"{DATA}/hereford.json")
FIT = jload(f"{DATA}/fit.json")
R = {}
pc = lambda a, b: round(100 * a / b, 1) if b else None
P["X"], P["Y"] = P.x_north.astype(float), -P.y_north.astype(float)          # north up, y up
n = len(P)
R["source"] = {"pleiades_version": PLEIADES_VER, "n": n, "high": int((P.conf == "high").sum()), "medium": int((P.conf == "medium").sum()), "regions": int(P.region.nunique()),
               "snapped": FIT["snapped"], "snapped_pct": pc(FIT["snapped"], n), "snap_median_px": FIT["snap_median_px"], "discs": FIT["n_discs"],
               "checked": int(P.checked.sum()), "checked_pct": pc(P.checked.sum(), n), "check_median_km": round(float(P.check_km.median()), 1),
               "thurayya": int(P.thurayya_km.notna().sum()), "pleiades": int(P.pleiades_km.notna().sum()), "naturalearth": int(P.naturalearth_km.notna().sum()),
               "img_w": IMG_W, "img_h": IMG_H, "year": 1154, "miller_year": 1928, "years_apart": 1300 - 1154}


# ---------- global affine fit: map -> longitude, latitude ----------
def affine(X, Y, U, V, w=None):
    A = np.c_[X, Y, np.ones(len(X))]
    cu, *_ = np.linalg.lstsq(A, U, rcond=None); cv, *_ = np.linalg.lstsq(A, V, rcond=None)
    return cu, cv


cu, cv = affine(P.X, P.Y, P.lon, P.lat)
A = np.c_[P.X, P.Y, np.ones(n)]
P["fit_lon"], P["fit_lat"] = A @ cu, A @ cv
P["resid_km"] = gc_km(P.lat, P.lon, P.fit_lat, P.fit_lon)
r2 = lambda y, yh: float(1 - np.sum((y - yh) ** 2) / np.sum((y - np.mean(y)) ** 2))
R["affine"] = {"lon_per_px": round(float(cu[0]), 5), "lat_per_px": round(float(cv[1]), 5), "lon_from_y": round(float(cu[1]), 5), "lat_from_x": round(float(cv[0]), 5),
               "r2_lon": round(r2(P.lon, P.fit_lon), 3), "r2_lat": round(r2(P.lat, P.fit_lat), 3),
               "median_resid_km": round(float(P.resid_km.median())), "mean_resid_km": round(float(P.resid_km.mean())),
               "p90_resid_km": round(float(P.resid_km.quantile(.9))), "within250_pct": pc((P.resid_km <= 250).sum(), n),
               "within500_pct": pc((P.resid_km <= 500).sum(), n),
               "px_per_lon_deg": round(1 / float(cu[0]), 1), "px_per_lat_deg": round(1 / float(cv[1]), 1)}
R["affine"]["lon_lat_ratio"] = round(1 / (R["affine"]["px_per_lat_deg"] / R["affine"]["px_per_lon_deg"]), 2)
R["affine"]["aspect"] = round(R["affine"]["px_per_lat_deg"] / R["affine"]["px_per_lon_deg"], 2)   # a degree of latitude against a degree of longitude
# the latitude at which a plate carree with this aspect would be true to scale
R["affine"]["true_scale_lat"] = round(float(np.degrees(np.arccos(min(1, 1 / R["affine"]["aspect"])))), 1)
# inverse: longitude, latitude -> map
M = np.array([[cu[0], cu[1]], [cv[0], cv[1]]]); b = np.array([cu[2], cv[2]]); Mi = np.linalg.inv(M)


def ll2map(lon, lat):
    v = Mi @ (np.array([lon, lat]) - b)
    return v[0], -v[1]                                        # north-up pixel (y down)


# ---------- local error: leave-one-out affine from the eight nearest neighbours ----------
LAT, LON = P.lat.values, P.lon.values
DK = gc_km(LAT[:, None], LON[:, None], LAT[None, :], LON[None, :])
loc, lsc, lrot = [], [], []
AEQ = {}
for i in range(n):
    order = np.argsort(DK[i]); nb = [j for j in order if j != i][:8]
    lat0, lon0 = LAT[i], LON[i]
    T = Transformer.from_crs(4326, f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +units=km", always_xy=True)
    ex, ny = T.transform(LON[nb], LAT[nb])
    Xn, Yn = P.X.values[nb], P.Y.values[nb]
    au, av = affine(Xn, Yn, ex, ny)
    pe, pn = au @ [P.X[i], P.Y[i], 1], av @ [P.X[i], P.Y[i], 1]
    loc.append(float(np.hypot(pe, pn)))                       # the place itself is at (0, 0)
    J = np.array([[au[0], au[1]], [av[0], av[1]]])
    lsc.append(float(np.sqrt(abs(np.linalg.det(J)))))         # km per map pixel, locally
    lrot.append(float(np.degrees(np.arctan2(J[1, 0] - J[0, 1], J[0, 0] + J[1, 1]))))   # rotation of the local map against north
P["local_km"], P["local_km_per_px"], P["local_rot"] = loc, lsc, lrot
R["local"] = {"median_km": round(float(P.local_km.median())), "within100_pct": pc((P.local_km <= 100).sum(), n),
              "within200_pct": pc((P.local_km <= 200).sum(), n), "p90_km": round(float(P.local_km.quantile(.9)))}


# ---------- pairwise bearings and stretch by region ----------
def mbrg(dx, dy):                                              # map bearing, north up, y up
    return (np.degrees(np.arctan2(dx, dy)) + 360) % 360


def pairs(d, minkm=100):
    out = []
    for i, j in itertools.combinations(d.index, 2):
        t = DK[i, j]
        if t < minkm: continue
        tb = float(bearing(LAT[i], LON[i], LAT[j], LON[j]))
        mb = float(mbrg(P.X[j] - P.X[i], P.Y[j] - P.Y[i]))
        md = float(np.hypot(P.X[j] - P.X[i], P.Y[j] - P.Y[i]))
        # the same pair on a perfect rectangular grid with the fitted aspect (degrees scaled as on the map)
        gd = float(np.hypot((LON[j] - LON[i]) * R["affine"]["px_per_lon_deg"], (LAT[j] - LAT[i]) * R["affine"]["px_per_lat_deg"]))
        out.append((t, abs(((mb - tb + 180) % 360) - 180), md / t, gd / t))
    return np.array(out) if out else np.zeros((0, 4))


ALL = pairs(P)
MED_S, MED_G = float(np.median(ALL[:, 2])), float(np.median(ALL[:, 3]))
R["pairs"] = {"n": len(ALL), "median_brg_err": round(float(np.median(ALL[:, 1]))), "within45_pct": pc((ALL[:, 1] <= 45).sum(), len(ALL)),
              "spearman_dist": round(float(spearmanr(ALL[:, 0], ALL[:, 2] * ALL[:, 0]).correlation), 3)}
regs = []
for reg in RNAMES:
    d = P[P.region == reg]
    if d.empty: continue
    pr = pairs(d)
    ok = len(d) >= 5 and len(pr) >= 5
    regs.append({"region": reg, "n": len(d), "pairs": len(pr), "scored": ok,
                 "median_resid_km": round(float(d.resid_km.median())), "median_local_km": round(float(d.local_km.median())),
                 "median_brg_err": round(float(np.median(pr[:, 1]))) if ok else None,
                 "stretch": round(float(np.median(pr[:, 2])) / MED_S, 2) if ok else None,
                 "grid_stretch": round(float(np.median(pr[:, 3])) / MED_G, 2) if ok else None,
                 "median_lat": round(float(d.lat.median()), 1), "median_lon": round(float(d.lon.median()), 1),
                 "rotation": round(float(np.median(d.local_rot))) if ok else None})
RG = pd.DataFrame(regs)
RG["excess_stretch"] = (RG.stretch / RG.grid_stretch).round(2)
RG.to_csv(f"{DATA}/regions.csv", index=False)
R["regions"] = {r["region"]: {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in r.items()} for r in RG.to_dict("records")}
G = R["regions"]
sc = RG[RG.scored].copy()
R["rank_local"] = sc.sort_values("median_local_km").region.tolist()
R["rank_brg"] = sc.sort_values("median_brg_err").region.tolist()
R["rank_stretch"] = sc.sort_values("stretch", ascending=False).region.tolist()
R["best_local"] = {"region": R["rank_local"][0], "km": G[R["rank_local"][0]]["median_local_km"]}
R["worst_local"] = {"region": R["rank_local"][-1], "km": G[R["rank_local"][-1]]["median_local_km"]}
R["best_brg"] = {"region": R["rank_brg"][0], "deg": G[R["rank_brg"][0]]["median_brg_err"]}
R["worst_brg"] = {"region": R["rank_brg"][-1], "deg": G[R["rank_brg"][-1]]["median_brg_err"]}

# groups: the Mediterranean against northern Europe and Asia
grp = {}
for g, members in GROUPS.items():
    d = P[P.region.isin(members)]
    pr = np.vstack([pairs(P[P.region == m]) for m in members if (P.region == m).sum() >= 2])
    grp[g] = {"n": len(d), "median_local_km": round(float(d.local_km.median())), "median_resid_km": round(float(d.resid_km.median())),
              "median_brg_err": round(float(np.median(pr[:, 1]))), "pairs": len(pr)}
R["groups"] = grp
gm, gn, ga = grp["Mediterranean"], grp["Northern Europe"], grp["Asia beyond the Euphrates"]
R["groups"]["ratio_local_north"] = round(gn["median_local_km"] / gm["median_local_km"], 1)
R["groups"]["ratio_local_asia"] = round(ga["median_local_km"] / gm["median_local_km"], 1)

# ---------- the Hereford comparison: similarity fit about Jerusalem, bearings and distances from Jerusalem ----------
AEQD = Transformer.from_crs(4326, f"+proj=aeqd +lat_0={JER[0]} +lon_0={JER[1]} +units=km", always_xy=True)
jx, jy = P.loc[P.identification == "Jerusalem", ["X", "Y"]].values[0]
H_ = P[P.identification != "Jerusalem"].copy()
ex, ny = AEQD.transform(H_.lon.values, H_.lat.values)
Z = (H_.X.values - jx) + 1j * (H_.Y.values - jy); Wc = ex + 1j * ny
a = (np.conj(Z - Z.mean()) @ (Wc - Wc.mean())) / (np.conj(Z - Z.mean()) @ (Z - Z.mean())); bb = Wc.mean() - a * Z.mean()
Wh = a * Z + bb
sim_r2 = float(1 - np.sum(np.abs(Wh - Wc) ** 2) / np.sum(np.abs(Wc - Wc.mean()) ** 2))
H_["true_brg"] = bearing(JER[0], JER[1], H_.lat.values, H_.lon.values)
H_["map_brg"] = mbrg(H_.X - jx, H_.Y - jy)
H_["brg_err"] = ((H_.map_brg - H_.true_brg + 180) % 360) - 180
H_["true_km"] = gc_km(JER[0], JER[1], H_.lat.values, H_.lon.values)
ae = H_.brg_err.abs()
rot = float(np.degrees(np.angle(a)))
R["jerusalem"] = {"n": len(H_), "sim_r2": round(sim_r2, 3), "sim_median_disp_km": round(float(np.median(np.abs(Wh - Wc)))),
                  "rotation_deg": round(rot, 1), "median_brg_err": round(float(ae.median())), "within45_pct": pc((ae <= 45).sum(), len(H_)),
                  "within90_pct": pc((ae <= 90).sum(), len(H_)),
                  "spearman": round(float(spearmanr(H_.true_km, np.hypot(H_.X - jx, H_.Y - jy)).correlation), 3)}
R["hereford"] = HF
R["compare"] = {"r2_gain": round(R["jerusalem"]["sim_r2"] - HF["fit_r2"], 3), "disp_ratio": round(HF["median_disp_km"] / R["jerusalem"]["sim_median_disp_km"], 1),
                "n_ratio": round(n / HF["located_real"], 1)}
# England from Jerusalem, as in the Hereford study
eng = H_[H_.region == "England"]
R["jerusalem"]["england_brg_err"] = round(float(eng.brg_err.abs().median()))

# ---------- climates ----------
lines = CL["sections"]
STEP = lines[0]["x1"] - lines[0]["x0"]
B = np.array([l["rows"] for l in lines])                       # rows on the image as drawn, per section
med_rows = np.median(B, axis=0).tolist() + [CL["bottom"]]
# latitude as a function of map row (as drawn), from the global fit: row -> north-up y -> latitude at the map's median x
xm = float(P.X.median())


def lat_at_row(row, x_north=xm):
    return float(cv[0] * x_north + cv[1] * (-(IMG_H - row)) + cv[2])


# implied boundaries: the latitude that best separates the places of each pair of neighbouring climates
bounds = []
for k in range(1, 7):
    a_, b_ = np.sort(P[P.climate == k].lat.values), np.sort(P[P.climate == k + 1].lat.values)
    cand = np.unique(np.r_[a_, b_])
    score = [((a_ < t).sum() + (b_ >= t).sum(), -abs(t - (np.median(a_) + np.median(b_)) / 2), t) for t in cand]
    best = max(score)
    ties = [s_[2] for s_ in score if s_[0] == best[0]]
    t = float(np.mean([ties[0], ties[-1]])) if len(ties) > 1 else best[2]
    bounds.append(round(t, 1))
cl = []
for k in range(1, 8):
    d = P[P.climate == k]
    cl.append({"climate": k, "n": len(d), "lat_min": round(float(d.lat.min()), 1), "lat_max": round(float(d.lat.max()), 1),
               "lat_p10": round(float(d.lat.quantile(.1)), 1), "lat_p90": round(float(d.lat.quantile(.9)), 1), "lat_median": round(float(d.lat.median()), 1),
               "implied_south": bounds[k - 2] if k > 1 else None, "implied_north": bounds[k - 1] if k < 7 else None,
               "row_south": round(med_rows[k - 1]), "row_north": round(med_rows[k]), "height_px": round(med_rows[k] - med_rows[k - 1])})
CLT = pd.DataFrame(cl)
CLT.to_csv(f"{DATA}/climates.csv", index=False)
R["climates"] = {str(c["climate"]): c for c in cl}
meds = [c["lat_median"] for c in cl]
P["climate_by_lat"] = [int(np.searchsorted(bounds, la, side="right")) + 1 for la in P.lat]
R["climate_summary"] = {"monotonic": all(a < b for a, b in zip(meds, meds[1:])), "bounds": bounds,
                        "widths": [round(b2 - b1, 1) for b1, b2 in zip(bounds, bounds[1:])],
                        "height_px": round(float(np.mean(np.diff(med_rows)))), "right_climate_pct": pc((P.climate_by_lat == P.climate).sum(), n),
                        "within_one_pct": pc(((P.climate_by_lat - P.climate).abs() <= 1).sum(), n), "lat_r2": R["affine"]["r2_lat"]}
cs_ = R["climate_summary"]
cs_["south_width"] = round(bounds[1] - bounds[0], 1); cs_["north_mid_width"] = round(float(np.mean(cs_["widths"][2:])), 1)
# examples named in the text
ex = lambda name: P[P.identification == name].iloc[0]
for k, nm_ in (("aden", "Aden"), ("mecca", "Mecca"), ("cairo", "Fustat (Old Cairo)"), ("jerusalem", "Jerusalem"), ("baghdad", "Baghdad"),
               ("palermo", "Palermo"), ("constantinople", "Constantinople (Istanbul)"), ("paris", "Paris"), ("london", "London"), ("lincoln", "Lincoln"),
               ("ghana", "Koumbi Saleh (capital of Ghana)"), ("dongola", "Old Dongola"), ("aswan", "Aswan"), ("alexandria", "Alexandria"),
               ("rome", "Rome"), ("cordoba", "Cordoba"), ("samarkand", "Samarkand"), ("kyiv", "Kyiv"), ("seville", "Seville")):
    r = ex(nm_)
    R.setdefault("places", {})[k] = {"climate": int(r.climate), "lat": float(r.lat), "lon": float(r.lon), "fit_lat": round(float(r.fit_lat), 1),
                                     "fit_lon": round(float(r.fit_lon), 1), "resid_km": round(float(r.resid_km)), "local_km": round(float(r.local_km)),
                                     "lat_err": round(float(r.fit_lat - r.lat), 1), "lon_err": round(float(r.fit_lon - r.lon), 1)}

# ---------- the Nile ----------
EQ_ROW = med_rows[0]
MOON_ROW, MOON_X = 395, 8650                                     # Gebel al-Qamr, the Mountains of the Moon, as drawn (centre of the range)
SWAMP_ROW = 480                                                 # the two lakes the Nile rises from, as drawn
xs = IMG_W - MOON_X
R["nile"] = {"text_moon_deg_south": 16, "text_length_miles": 5654,
             "moon_px_south_of_equator": round(EQ_ROW - MOON_ROW), "climate_height_px": R["climate_summary"]["height_px"],
             "aswan_fit_lat": R["places"]["aswan"]["fit_lat"], "aswan_lat": R["places"]["aswan"]["lat"],
             "dongola_fit_lat": R["places"]["dongola"]["fit_lat"], "dongola_lat": R["places"]["dongola"]["lat"],
             "alexandria_fit_lat": R["places"]["alexandria"]["fit_lat"], "alexandria_lat": R["places"]["alexandria"]["lat"],
             "ruwenzori_lat": 0.39, "nile_km_real": 6650}
R["nile"]["moon_frac_climate"] = round(R["nile"]["moon_px_south_of_equator"] / R["nile"]["climate_height_px"], 2)
eg = P[P.region == "Egypt and Nubia"]
R["nile"]["egypt_lat_span_real"] = round(float(eg.lat.max() - eg.lat.min()), 1)
R["nile"]["egypt_lat_span_fit"] = round(float(eg.fit_lat.max() - eg.fit_lat.min()), 1)

# ---------- route distances from the text ----------
mi = RT[RT.miles.notna()].copy(); dy = RT[RT.days.notna()].copy(); both = RT[RT.miles.notna() & RT.days.notna()]
R["routes"] = {"n": len(RT), "n_miles": len(mi), "n_days": len(dy), "median_km_per_mile": round(float(mi.km_per_mile.median()), 2),
               "q1_km_per_mile": round(float(mi.km_per_mile.quantile(.25)), 2), "q3_km_per_mile": round(float(mi.km_per_mile.quantile(.75)), 2),
               "spearman_miles": round(float(spearmanr(mi.miles, mi.km).correlation), 3),
               "median_km_per_day": round(float(dy.km_per_day.median())), "q1_km_per_day": round(float(dy.km_per_day.quantile(.25))),
               "q3_km_per_day": round(float(dy.km_per_day.quantile(.75))), "spearman_days": round(float(spearmanr(dy.days, dy.km).correlation), 3),
               "miles_per_day": [round(float(m / d), 1) for m, d in zip(both.miles, both.days)], "n_both": len(both),
               "min_miles": int(mi.miles.min()), "max_miles": int(mi.miles.max()),
               "arab_mile_lo": ARAB_MILE_KM[0], "arab_mile_hi": ARAB_MILE_KM[1]}
R["routes"]["median_miles_per_day"] = round(float(np.median(R["routes"]["miles_per_day"])), 1)
R["routes"]["road_factor_lo"] = round(ARAB_MILE_KM[0] / R["routes"]["median_km_per_mile"], 2)
R["routes"]["road_factor_hi"] = round(ARAB_MILE_KM[1] / R["routes"]["median_km_per_mile"], 2)
R["routes"]["nile_km_at_median"] = round(5654 * R["routes"]["median_km_per_mile"], -2)
R["routes"]["nile_km_at_lo"] = round(5654 * ARAB_MILE_KM[0], -2); R["routes"]["nile_km_at_hi"] = round(5654 * ARAB_MILE_KM[1], -2)
# do the map's own distances follow the text? pairs where both ends are on the map
on = {r.identification: (r.X, r.Y) for r in P.itertuples()}
mm = [(r.miles, float(np.hypot(on[r["from"]][0] - on[r["to"]][0], on[r["from"]][1] - on[r["to"]][1])), r.km) for _, r in mi.iterrows() if r["from"] in on and r["to"] in on]
mm = np.array(mm)
R["routes"]["n_on_map"] = len(mm)
R["routes"]["spearman_map_miles"] = round(float(spearmanr(mm[:, 0], mm[:, 1]).correlation), 3)
R["routes"]["spearman_map_km"] = round(float(spearmanr(mm[:, 2], mm[:, 1]).correlation), 3)

# ---------- Britain ----------
E = P[P.region == "England"]
F = P[P.region == "France and the Low Countries"]
lon_shift = float((E.fit_lon - E.lon).median()); lat_shift = float((E.fit_lat - E.lat).median())
R["britain"] = {"n": len(E), "median_resid_km": round(float(E.resid_km.median())), "median_local_km": round(float(E.local_km.median())),
                "lat_shift": round(lat_shift, 1), "lon_shift": round(lon_shift, 1), "climates": sorted(set(E.climate.astype(int))),
                "stretch": G["England"]["stretch"], "grid_stretch": G["England"]["grid_stretch"], "brg_err": G["England"]["median_brg_err"],
                "london_climate": R["places"]["london"]["climate"], "lincoln_climate": R["places"]["lincoln"]["climate"],
                "france_median_resid_km": round(float(F.resid_km.median())), "hereford_names_pct": HF["britain_names_pct"]}
# the Channel: Dover to London against Dover to the French coast places, on the map and in reality
dv, ld, pa = (P[P.identification == k].iloc[0] for k in ("Dover", "London", "Paris"))
R["britain"]["london_paris_km"] = round(float(gc_km(ld.lat, ld.lon, pa.lat, pa.lon)))
R["britain"]["london_paris_map_km"] = round(float(np.hypot(ld.X - pa.X, ld.Y - pa.Y)) * MED_S ** -1 / 1) if False else None
R["britain"]["london_paris_brg_true"] = round(float(bearing(ld.lat, ld.lon, pa.lat, pa.lon)))
R["britain"]["london_paris_brg_map"] = round(float(mbrg(pa.X - ld.X, pa.Y - ld.Y)))

# ---------- Sicily ----------
S_ = P[P.region == "Sicily and Malta"]
R["sicily"] = {"n": len(S_), "median_local_km": round(float(S_.local_km.median())), "median_resid_km": round(float(S_.resid_km.median())),
               "brg_err": G["Sicily and Malta"]["median_brg_err"], "stretch": G["Sicily and Malta"]["stretch"],
               "grid_stretch": G["Sicily and Malta"]["grid_stretch"], "rank_local": R["rank_local"].index("Sicily and Malta") + 1,
               "rank_brg": R["rank_brg"].index("Sicily and Malta") + 1, "n_scored": int(RG.scored.sum())}

# ---------- sensitivity: clear readings only ----------
Hi = P[P.conf == "high"]
cuh, cvh = affine(Hi.X, Hi.Y, Hi.lon, Hi.lat)
Ah = np.c_[Hi.X, Hi.Y, np.ones(len(Hi))]
R["high_only"] = {"n": len(Hi), "median_resid_km": round(float(np.median(gc_km(Hi.lat, Hi.lon, Ah @ cvh, Ah @ cuh)))),
                  "median_local_km": round(float(Hi.local_km.median())), "r2_lat": round(r2(Hi.lat, Ah @ cvh), 3)}

# ---------- warped graticule and climate lines (thin plate spline, smoothed) ----------
SM = 30.0
fwd = RBFInterpolator(np.c_[P.lon, P.lat], np.c_[P.x_north, P.y_north], kernel="thin_plate_spline", smoothing=SM)
inv = RBFInterpolator(np.c_[P.x_north, P.y_north] / 100.0, np.c_[P.lon, P.lat], kernel="thin_plate_spline", smoothing=SM)


def near_ll(lon, lat, km=450):
    return gc_km(lat, lon, LAT, LON).min() <= km


grat = []
for lon0 in range(-10, 81, 10):
    seg, cur = [], []
    for lat0 in np.arange(0, 61, 1.0):
        if near_ll(lon0, lat0):
            x, y = fwd([[lon0, lat0]])[0]; cur.append([round(float(IMG_W - x), 1), round(float(IMG_H - y), 1)])   # back to the image as drawn
        elif cur:
            seg.append(cur); cur = []
    if cur: seg.append(cur)
    grat += [{"kind": "meridian", "v": lon0, "pts": s} for s in seg if len(s) > 2]
for lat0 in range(10, 61, 10):
    seg, cur = [], []
    for lon0 in np.arange(-15, 85, 1.0):
        if near_ll(lon0, lat0):
            x, y = fwd([[lon0, lat0]])[0]; cur.append([round(float(IMG_W - x), 1), round(float(IMG_H - y), 1)])
        elif cur:
            seg.append(cur); cur = []
    if cur: seg.append(cur)
    grat += [{"kind": "parallel", "v": lat0, "pts": s} for s in seg if len(s) > 2]
# climate lines on the modern map: each boundary row, section by section, mapped back to the globe where places are near
XY = np.c_[P.x_north, P.y_north]
cll = []
for k in range(0, 8):
    seg, cur = [], []
    for l in lines:
        row = l["rows"][k] if k < 7 else CL["bottom"]
        for x in np.arange(l["x0"], l["x1"], 100.0):
            xn, yn = IMG_W - x, IMG_H - row
            if np.hypot(XY[:, 0] - xn, XY[:, 1] - yn).min() <= 650:
                lo_, la_ = inv([[xn / 100.0, yn / 100.0]])[0]; cur.append([round(float(lo_), 2), round(float(la_), 2)])
            elif cur:
                seg.append(cur); cur = []
    if cur: seg.append(cur)
    cll += [{"k": k, "pts": s[::-1]} for s in seg if len(s) > 2]
R["warp"] = {"smoothing": SM, "graticule_lines": len(grat), "climate_lines": len(cll)}

# ---------- tables ----------
P["imp_lat"], P["imp_lon"] = P.fit_lat, P.fit_lon
cols = ["label", "identification", "conf", "region", "lat", "lon", "x", "y", "x_north", "y_north", "snap_px", "climate", "section",
        "fit_lat", "fit_lon", "resid_km", "local_km", "local_rot", "thurayya", "thurayya_km", "pleiades", "pleiades_km", "naturalearth", "naturalearth_km"]
P[cols].round(3).rename(columns={"x": "x_as_drawn", "y": "y_as_drawn", "fit_lat": "map_lat", "fit_lon": "map_lon"}).to_csv(f"{DATA}/located.csv", index=False)

# ---------- page data ----------
RI = {r: i for i, r in enumerate(RNAMES)}
loc_rows = []
for i, r in P.iterrows():
    loc_rows.append([i, r.label, r.identification, RI[r.region], round(float(r.x), 1), round(float(r.y), 1), round(float(r.lat), 3), round(float(r.lon), 3),
                     r.conf, int(r.climate), int(r.section), round(float(r.fit_lat), 2), round(float(r.fit_lon), 2), round(float(r.resid_km)), round(float(r.local_km)),
                     r.thurayya or "", r.pleiades or "", r.naturalearth or ""])
routes_site = [[r["from"], r["to"], None if pd.isna(r.miles) else int(r.miles), None if pd.isna(r.days) else int(r.days), r.from_lat, r.from_lon, r.to_lat, r.to_lon,
                round(float(r.km)), None if pd.isna(r.km_per_mile) else r.km_per_mile, int(r.ocr_line)] for _, r in RT.iterrows()]
site = {"regions": REGIONS, "located": loc_rows,
        "loc_cols": ["i", "label", "ident", "reg", "x", "y", "lat", "lon", "conf", "climate", "section", "fit_lat", "fit_lon", "resid_km", "local_km", "th", "pl", "ne"],
        "graticule": grat, "climate_lines": cll, "lines": [{"x0": l["x0"], "x1": l["x1"], "rows": l["rows"]} for l in lines], "bottom": CL["bottom"],
        "routes": routes_site, "route_cols": ["from", "to", "miles", "days", "from_lat", "from_lon", "to_lat", "to_lon", "km", "km_per_mile", "line"],
        "img": {"w": IMG_W, "h": IMG_H, "tz": TZ, "tx0": TX0, "ty0": TY0, "tworld": TWORLD, "small": "img/idrisi_2000.jpg"},
        "moon": [MOON_X, MOON_ROW], "jer": list(JER), "climates": cl}
jsave(site, f"{DATA}/site.json")
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "miller_url": MILLER_URL, "dozy_ia": DOZY_IA, "thurayya_url": THURAYYA_URL}
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("affine", "local", "pairs", "groups", "jerusalem", "climate_summary", "nile", "routes", "britain", "sicily", "high_only")}, indent=0)[:6000])
print(RG.to_string())
print(CLT.to_string())
