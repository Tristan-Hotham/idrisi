"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json; positions from data/site.json and data/located.csv."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyArrowPatch
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
for f in os.listdir(PA):
    if f.startswith("f_"): os.remove(os.path.join(PA, f))
L = pd.DataFrame(SITE["located"], columns=SITE["loc_cols"])
L["region"] = L.reg.map(lambda i: RNAMES[i]); L["col"] = L.region.map(RCOL)
L["xn"], L["yn"] = nu(L.x, L.y)
OM = oldmap(); OW, OH = OM.size
HALO = [pe.withStroke(linewidth=3.2, foreground="#FFFBF2")]


def both(fig, name, blog=True, jpg=False):
    if jpg:                                             # photographic figures: JPEG in the paper keeps the PDF small
        fig.savefig(os.path.join(PA, "f_" + name + ".jpg"), dpi=200, facecolor=fig.get_facecolor(), pil_kwargs={"quality": 86})
    else:
        fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def label(ax, x, y, t, dx=0, dy=0, ha="left", fs=10, col=FG, weight=None):
    ax.annotate(t, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=fs, color=col, path_effects=HALO, zorder=8, fontweight=weight)


def find(name):
    return L[L.ident == name].iloc[0]


def regleg(fig, x, y, ncol=6, fs=9):
    regs = [r for r in RNAMES if (L.region == r).any()]
    fig.legend(handles=[Line2D([], [], marker="o", ls="", mfc=RCOL[r], mec="white", ms=7, label=r) for r in regs], loc="lower left",
               bbox_to_anchor=(x, y), ncol=ncol, frameon=False, fontsize=fs, handletextpad=.2, columnspacing=1)


LAB = [("Palermo", "Palermo"), ("Cordoba", "Cordoba"), ("Paris", "Paris"), ("London", "London"), ("Rome", "Rome"), ("Constantinople (Istanbul)", "Constantinople"),
       ("Fustat (Old Cairo)", "Cairo"), ("Mecca", "Mecca"), ("Baghdad", "Baghdad"), ("Samarkand", "Samarkand"), ("Aden", "Aden"), ("Multan", "Multan")]
OFF_O = {"Palermo": (0, -11, "center"), "Cordoba": (0, 10, "center"), "Paris": (0, 10, "center"), "London": (0, 10, "center"), "Rome": (0, 10, "center"),
         "Constantinople": (0, 10, "center"), "Cairo": (8, 0, "left"), "Mecca": (8, 0, "left"), "Baghdad": (0, 10, "center"), "Samarkand": (0, 10, "center"),
         "Aden": (0, -10, "center"), "Multan": (0, 10, "center")}
OFF_G = {"Palermo": (0, -10, "center"), "Cordoba": (-7, -7, "right"), "Paris": (7, 4, "left"), "London": (-7, 4, "right"), "Rome": (6, 7, "left"),
         "Constantinople": (6, 7, "left"), "Cairo": (-7, -5, "right"), "Mecca": (-7, 0, "right"), "Baghdad": (6, 6, "left"), "Samarkand": (0, 10, "center"),
         "Aden": (0, -10, "center"), "Multan": (6, 6, "left")}

# ---------- 1. the two maps ----------
fig = plt.figure(figsize=(12, 11.4), facecolor=BG)
a1 = fig.add_axes([.01, .5, .98, .42]); a1.imshow(OM); a1.set_xlim(0, OW); a1.set_ylim(OH, 0); a1.axis("off")
a1.scatter(L.xn, L.yn, s=12, c=L.col, edgecolors="white", linewidths=.35, zorder=5)
a2 = fig.add_axes([.01, .02, .66, .43]); world(a2, (-12, 82, 9, 57), aspect_lat=36); a2.set_anchor("W")
a2.scatter(L.lon, L.lat, s=12, c=L.col, edgecolors="white", linewidths=.35, zorder=5)
for nmx, t in LAB:
    r = find(nmx); dx, dy, ha = OFF_O[t]; label(a1, r.xn, r.yn, t, dx, dy, ha, fs=9)
    dx, dy, ha = OFF_G[t]; label(a2, r.lon, r.lat, t, dx, dy, ha, fs=9)
fig.text(.01, .968, "Al-Idrisi's map of 1154, turned north up (Miller's reconstruction)", fontproperties=DISPB, fontsize=16, color=FG)
fig.text(.01, .945, f"{R['source']['n']} towns I read and placed; the map is drawn with south at the top", fontsize=10, color=MUT)
fig.text(.01, .467, "The same towns today", fontproperties=DISPB, fontsize=16, color=FG)
regs = [r for r in RNAMES if (L.region == r).any()]
fig.legend(handles=[Line2D([], [], marker="o", ls="", mfc=RCOL[r], mec="white", ms=8, label=r) for r in regs], loc="upper left",
           bbox_to_anchor=(.69, .44), ncol=1, frameon=False, fontsize=10, title="Region", title_fontsize=10, alignment="left")
both(fig, "maps", jpg=True)

# ---------- 2. climates ----------
B = R["climate_summary"]["bounds"]
fig, ax = plt.subplots(figsize=(12, 6.2), facecolor=BG); ax.set_facecolor(BG); fig.subplots_adjust(left=.12, right=.97, top=.84, bottom=.12)
rng = np.random.default_rng(1)
for k in range(1, 8):
    d = L[L.climate == k]
    ax.scatter(d.lat, k + rng.uniform(-.25, .25, len(d)), s=26, c=d.col, edgecolors="white", linewidths=.5, zorder=3)
for b in B:
    ax.axvline(b, color=RED, ls="--", lw=1.3, zorder=2)
ax.set_yticks(range(1, 8)); ax.set_yticklabels([f"Climate {r}" for r in ["I", "II", "III", "IV", "V", "VI", "VII"]], fontsize=11)
ax.set_xticks([10, 20, 30, 40, 50]); ax.set_xticklabels(["10° N", "20° N", "30° N", "40° N", "50° N"]); ax.set_xlim(10, 56); ax.set_ylim(.4, 7.6)
spines(ax); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True); ax.set_xlabel("true latitude of the town")
fig.text(.02, .93, "Seven climates: the map's bands of latitude against the towns' real latitude", fontproperties=DISPB, fontsize=16, color=FG)
fig.text(.02, .885, f"Red dashes: the latitudes that best separate neighbouring climates ({', '.join(f'{b:.0f}' for b in B)} degrees N). {R['climate_summary']['right_climate_pct']:.0f}% of towns fall in the right band.", fontsize=9.5, color=MUT)
both(fig, "climates")

# ---------- 3. local error by region ----------
D = sorted([r for r in R["regions"].values() if r["scored"]], key=lambda r: -r["median_local_km"])
fig, ax = plt.subplots(figsize=(12, 6.6), facecolor=BG); ax.set_facecolor(BG); fig.subplots_adjust(left=.22, right=.95, top=.86, bottom=.11)
for i, r in enumerate(D):
    ax.barh(i, r["median_local_km"], color=RCOL[r["region"]], height=.66)
    ax.text(r["median_local_km"] + 3, i, f"{r['median_local_km']} km  ({r['n']} towns)", va="center", fontsize=10, color=FG)
ax.set_yticks(range(len(D))); ax.set_yticklabels([r["region"] for r in D], fontsize=11); ax.tick_params(axis="y", length=0)
spines(ax); ax.spines["left"].set_visible(False); ax.grid(axis="x", color=RULE); ax.set_axisbelow(True); ax.set_xlim(0, 310)
ax.set_xlabel("median local error (km): how far each town is from where its eight nearest neighbours put it")
fig.text(.02, .93, f"Most faithful at home: Sicily {R['sicily']['median_local_km']} km, Sind and India {R['regions']['Sind and India']['median_local_km']} km", fontproperties=DISPB, fontsize=17, color=FG)
both(fig, "regions")

# ---------- 4. displacement arrows ----------
fig = plt.figure(figsize=(12, 7.0), facecolor=BG); ax = fig.add_axes([.01, .1, .98, .76])
world(ax, (-12, 82, 9, 57), aspect_lat=36)
for l in SITE["climate_lines"]:
    p = np.array(l["pts"]); ax.plot(p[:, 0], p[:, 1], color=RED, ls="--", lw=1.1, alpha=.75, zorder=2)
for _, r in L.iterrows():
    ax.add_patch(FancyArrowPatch((r.lon, r.lat), (r.fit_lon, r.fit_lat), arrowstyle="-|>", mutation_scale=6, color=r.col, lw=.7, alpha=.8, zorder=4))
ax.scatter(L.lon, L.lat, s=8, c=L.col, zorder=5, edgecolors="white", linewidths=.3)
fig.text(.01, .935, "If al-Idrisi's map were an ordinary map: from each town to where the map puts it", fontproperties=DISPB, fontsize=16, color=FG)
fig.text(.01, .895, f"Best affine fit of the whole map to longitude and latitude; median shift {R['affine']['median_resid_km']} km. Red dashes: the map's climate lines laid on the globe.", fontsize=9.5, color=MUT)
regleg(fig, .01, .0, ncol=6, fs=8)
both(fig, "arrows")

# ---------- 5. Sicily close up ----------
S = L[L.region == "Sicily and Malta"]
S = S[S.ident != "Malta"]
fig = plt.figure(figsize=(12, 5.6), facecolor=BG)
a1 = fig.add_axes([.01, .06, .47, .78]); a2 = fig.add_axes([.52, .06, .47, .78])
x0, x1, y0, y1 = S.xn.min() - 22, S.xn.max() + 22, S.yn.min() - 22, S.yn.max() + 22
ax0, ay0 = IMG_W - x1 / SCALE, IMG_H - y1 / SCALE                     # the same box on the full-resolution image as drawn
a1.imshow(crop_full(ax0, ay0, IMG_W - x0 / SCALE, IMG_H - y0 / SCALE), extent=(x0, x1, y1, y0)); a1.set_xlim(x0, x1); a1.set_ylim(y1, y0); a1.axis("off")
a1.scatter(S.xn, S.yn, s=40, c=RCOL["Sicily and Malta"], edgecolors="white", linewidths=.8, zorder=5)
world(a2, (12.2, 15.9, 36.5, 38.5))
a2.scatter(S.lon, S.lat, s=40, c=RCOL["Sicily and Malta"], edgecolors="white", linewidths=.8, zorder=5)
for nmx, o1, o2 in (("Palermo", (0, 10, "center"), (0, 10, "center")), ("Messina", (0, 10, "center"), (-8, 0, "right")), ("Syracuse", (8, 0, "left"), (8, 0, "left")),
                    ("Trapani", (0, -11, "center"), (-8, 0, "right")), ("Agrigento", (0, -11, "center"), (0, -11, "center")), ("Enna (Castrogiovanni)", (8, 0, "left"), (0, 10, "center"))):
    r = find(nmx); t = nmx.split(" (")[0]
    label(a1, r.xn, r.yn, t, *o1[:2], o1[2], fs=9.5); label(a2, r.lon, r.lat, t, *o2[:2], o2[2], fs=9.5)
fig.text(.01, .92, "Sicily on al-Idrisi's map (turned north up) and today", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.01, .875, f"Median local error {R['sicily']['median_local_km']} km, the best on the map; drawn at {R['regions']['Sicily and Malta']['stretch']:.2f} times the map's average scale, but turned about {abs(R['regions']['Sicily and Malta']['rotation']):.0f} degrees.", fontsize=9.5, color=MUT)
both(fig, "sicily", jpg=True)

# ---------- 6. route distances ----------
RT = pd.read_csv(f"{DATA}/routes.csv"); M = RT[RT.miles.notna()]
fig, ax = plt.subplots(figsize=(12, 6.4), facecolor=BG); ax.set_facecolor(BG); fig.subplots_adjust(left=.09, right=.97, top=.85, bottom=.12)
k = R["routes"]["median_km_per_mile"]; xs = np.array([4, 700])
ax.plot(xs, xs * 2, color=SAFF, ls="--", lw=1.6); ax.plot(xs, xs * k, color=LAPIS, lw=1.6)
ax.text(170, 170 * 2 * 1.12, "2 km a mile", color=SAFF, fontsize=10, ha="right")
ax.text(200, 200 * k / 1.35, f"median {k:.2f} km a mile", color=LAPIS, fontsize=10)
ax.scatter(M.miles, M.km, s=40, c=LAPIS, edgecolors="white", linewidths=.6, zorder=3)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(4, 700); ax.set_ylim(4, 1500); spines(ax); ax.grid(color=RULE, which="major"); ax.set_axisbelow(True)
for a in (ax.xaxis, ax.yaxis):
    a.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_xlabel("distance stated by al-Idrisi (Arab miles)"); ax.set_ylabel("straight line today (km)")
fig.text(.02, .93, f"{R['routes']['n_miles']} road distances from the Book of Roger against the straight line", fontproperties=DISPB, fontsize=17, color=FG)
fig.text(.02, .89, f"North Africa and Spain, from Dozy and de Goeje (1866). Rank correlation {R['routes']['spearman_miles']:.2f}.", fontsize=9.5, color=MUT)
both(fig, "routes")

# ---------- 7. Hereford comparison ----------
J, H = R["jerusalem"], R["hereford"]
MS = [("Spread of real positions\nexplained (%)", J["sim_r2"] * 100, H["fit_r2"] * 100), ("Median miss from the\nfitted map (km)", J["sim_median_disp_km"], H["median_disp_km"]),
      ("Median direction error\nfrom Jerusalem (degrees)", J["median_brg_err"], H["bearing_median_err"]), ("Within 45 degrees of\nthe right way (%)", J["within45_pct"], H["bearing_within45_pct"])]
fig, axs = plt.subplots(1, 4, figsize=(12, 5.0), facecolor=BG); fig.subplots_adjust(left=.03, right=.98, top=.72, bottom=.18, wspace=.45)
for ax, (t, a, b) in zip(axs, MS):
    ax.set_facecolor(BG); ax.bar([0, 1], [a, b], color=[LAPIS, RED], width=.62)
    for i, v in enumerate((a, b)): ax.text(i, v * 1.02, f"{v:.0f}", ha="center", va="bottom", fontsize=12, color=FG)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["al-Idrisi", "Hereford"], fontsize=10); ax.set_yticks([]); ax.set_ylim(0, max(a, b) * 1.2)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.set_title(t, fontsize=10, color=FG, pad=6)
fig.text(.02, .92, "Palermo 1154 against Hereford about 1300: the same tests, measured from Jerusalem", fontproperties=DISPB, fontsize=16, color=FG)
fig.text(.02, .865, f"Similarity fit (rotation, scale, shift) about Jerusalem, as in my Hereford study. Al-Idrisi {J['n']} towns; Hereford {H['located_real']} places.", fontsize=9.5, color=MUT)
both(fig, "compare")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
a1 = fig.add_axes([.47, .1, .52, .8]); a1.imshow(oldmap(north=False)); a1.axis("off")
a2 = fig.add_axes([.04, .03, .4, .19]); world(a2, (-12, 82, 9, 57), aspect_lat=36); a2.set_anchor("W"); a2.scatter(L.lon, L.lat, s=4, c=L.col, linewidths=0, zorder=5)
fig.text(.04, .74, "Al-Idrisi's", fontproperties=DISP, fontsize=56, color=FG)
fig.text(.04, .58, "World", fontproperties=DISP, fontsize=56, color=LAPIS)
fig.text(.045, .46, "The map made for Roger II of Sicily in 1154,", fontproperties=SERP, fontsize=17, color=FG)
fig.text(.045, .405, "south at the top, set against a modern one", fontproperties=SERP, fontsize=17, color=FG)
fig.text(.045, .33, f"{R['source']['n']} towns  ·  seven climates", fontsize=11, color=MUT)
fig.text(.045, .285, f"directions right to a median {R['pairs']['median_brg_err']} degrees", fontsize=11, color=MUT)
fig.text(.47, .04, "Konrad Miller's 1928 reconstruction, as drawn: south at the top", fontsize=9, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
assert Image.open(os.path.join(ROOT, "header.png")).size == (1200, 630)
for f in os.listdir(BL):
    if f.endswith(".png"): assert Image.open(os.path.join(BL, f)).size[0] == 1800, f
print("figures", sorted(os.listdir(BL)))
