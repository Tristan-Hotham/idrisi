"""Reddit collage (2400 x 3200): al-Idrisi's map as drawn and turned north up, the same towns on a modern map, how
faithfully each region is drawn, and the comparison with the Hereford map. Light background; labels sit on plain paper
or sea, never over the maps; numbers from data/results.json."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import pandas as pd
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
L = pd.DataFrame(SITE["located"], columns=SITE["loc_cols"])
L["region"] = L.reg.map(lambda i: RNAMES[i]); L["col"] = L.region.map(RCOL)
L["xn"], L["yn"] = nu(L.x, L.y)
OM = oldmap(); OW, OH = OM.size
fig = plt.figure(figsize=(8, 32 / 3), dpi=300, facecolor=BG)
fig.text(.05, .962, "The world from Palermo, 1154", fontproperties=DISP, fontsize=27, color=LAPIS)
fig.text(.05, .935, "Al-Idrisi's map for King Roger II of Sicily, against a real one", fontproperties=DISPB, fontsize=14, color=FG)
fig.text(.05, .917, f"{R['source']['n']} towns read on Konrad Miller's 1928 reconstruction and placed on a modern map.", fontsize=7.6, color=MUT)

# the map as drawn (small) and turned north up
a0 = fig.add_axes([.05, .79, .4, .11]); a0.imshow(oldmap(north=False)); a0.axis("off"); a0.set_anchor("W")
fig.text(.05, .782, "As drawn: south at the top", fontsize=7, color=MUT)
fig.text(.56, .875, "Seven climates, ten sections,", fontsize=8.2, color=FG)
fig.text(.56, .86, "drawn in Palermo by a Muslim", fontsize=8.2, color=FG)
fig.text(.56, .845, "scholar for a Norman king.", fontsize=8.2, color=FG)
fig.text(.56, .82, "Below: turned north up, with", fontsize=8.2, color=MUT)
fig.text(.56, .805, "every town I could read.", fontsize=8.2, color=MUT)
fig.text(.05, .762, "Al-Idrisi's map, turned north up", fontproperties=DISPB, fontsize=11, color=FG)
a1 = fig.add_axes([.03, .43, .94, .325]); a1.imshow(OM); a1.set_xlim(0, OW); a1.set_ylim(OH, 0); a1.axis("off")
a1.scatter(L.xn, L.yn, s=5, c=L.col, edgecolors="white", linewidths=.25, zorder=5)

# modern map and legend
fig.text(.05, .41, "The same towns today; red dashes: the map's climate lines", fontproperties=DISPB, fontsize=9.5, color=FG)
a2 = fig.add_axes([.03, .2, .6, .2]); world(a2, (-12, 82, 9, 57), aspect_lat=36); a2.set_anchor("W")
a2.scatter(L.lon, L.lat, s=5, c=L.col, edgecolors="white", linewidths=.25, zorder=5)
for l in SITE["climate_lines"]:
    p = np.array(l["pts"]); a2.plot(p[:, 0], p[:, 1], color=RED, ls="--", lw=.6, alpha=.7, zorder=2)
regs = [r for r in RNAMES if (L.region == r).any()]
fig.legend(handles=[Line2D([], [], marker="o", ls="", mfc=RCOL[r], mec="white", ms=4, label=r) for r in regs] +
           [Line2D([], [], color=RED, ls="--", lw=.9, label="climate boundary")], loc="upper left", bbox_to_anchor=(.6, .405), ncol=2, frameon=False, fontsize=5.4,
           handletextpad=.3, labelspacing=.5, columnspacing=.8, title="Region", title_fontsize=6, alignment="left")

# local error by region
D = sorted([r for r in R["regions"].values() if r["scored"]], key=lambda r: -r["median_local_km"])
a3 = fig.add_axes([.3, .052, .26, .108]); a3.set_facecolor(BG)
for i, r in enumerate(D):
    a3.barh(i, r["median_local_km"], color=RCOL[r["region"]], height=.7)
    a3.text(r["median_local_km"] + 4, i, f"{r['median_local_km']}", va="center", fontsize=4.6, color=FG)
a3.set_yticks(range(len(D))); a3.set_yticklabels([r["region"] for r in D], fontsize=4.8); a3.tick_params(axis="y", length=0, pad=1)
a3.set_xlim(0, 290); a3.set_xticks([]); a3.set_ylim(-.6, len(D) - .4)
for s_ in ("top", "right", "left", "bottom"): a3.spines[s_].set_visible(False)
fig.text(.05, .182, "How faithfully each region is drawn", fontproperties=DISPB, fontsize=9.5, color=FG)
fig.text(.05, .171, "median km between each town and where its 8 nearest neighbours on the map put it (lower is better)", fontsize=5.8, color=MUT)

# stats, two by two
J, H = R["jerusalem"], R["hereford"]
st = [(f"{R['pairs']['median_brg_err']}°", "median error in direction\nbetween pairs of towns", LAPIS),
      (f"{R['regions']['Sicily and Malta']['median_local_km']} km", f"local error in Sicily, the best\ndrawn region, also drawn\nbiggest (x{R['regions']['Sicily and Malta']['stretch']:.2f})", RED),
      (f"{R['groups']['Mediterranean']['median_local_km']} v {R['groups']['Asia beyond the Euphrates']['median_local_km']} km", "local error: Mediterranean\nagainst Asia beyond\nthe Euphrates", GREEN),
      (f"{J['sim_median_disp_km']} v {H['median_disp_km']} km", "median miss from Jerusalem:\nal-Idrisi 1154 against\nHereford c. 1300", SAFF)]
for i, (big, small, c) in enumerate(st):
    x = .62 + (i % 2) * .19; y = .162 - (i // 2) * .062
    fig.text(x, y, big, fontproperties=DISP, fontsize=13, color=c, va="top")
    fig.text(x, y - .02, small, fontsize=5.6, color=FG, va="top", linespacing=1.3)
fig.text(.05, .035, "Sources: K. Miller (1928) reconstruction, Wikimedia Commons (public domain); al-Thurayya gazetteer (CC BY 4.0); Pleiades (CC BY 3.0);", fontsize=5.8, color=MUT)
fig.text(.05, .024, "Natural Earth; Hereford figures from my own study. Positions read by eye. Dr Tristan Hotham · maps.tristanhotham.com/idrisi", fontsize=5.8, color=MUT)
out = os.path.join(ROOT, "reddit", "idrisi_world_map.png")
fig.savefig(out, dpi=300, facecolor=BG); plt.close(fig)
from PIL import Image as _I
_I.open(out).convert("RGB").quantize(256, method=_I.Quantize.MEDIANCUT).save(out, optimize=True)   # 256 colours keeps the file small
assert _I.open(out).size == (2400, 3200), _I.open(out).size
print("collage", out)
