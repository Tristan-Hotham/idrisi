"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json) is embedded; the map tiles and images are in img/. Facts
stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before </body>.
10.5281/zenodo.23882607 and https://blog.tristanhotham.com/2026/10/31/idrisi/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
KEEP = {"DOI", "BLOG_URL", "DOI_URL"}
G, C = R["regions"], R["climates"]

# facts stated in words (page, blog, paper, collage)
assert R["rank_local"][0] == "Sicily and Malta" and R["rank_local"][1] == "Syria and Palestine"
assert R["rank_local"][-3:] == ["Arabia", "Central and Eastern Europe", "Sind and India"]
assert R["rank_stretch"][0] == "Sicily and Malta" and R["rank_stretch"][-2:] == ["Morocco and Algeria", "Arabia"]
assert f"{G['Italy and Corsica']['stretch']:.2f}" == f"{G['England']['stretch']:.2f}"            # "Italy and England 1.25"
assert R["sicily"]["rank_brg"] >= R["sicily"]["n_scored"] - 4                                         # "one of the larger figures"
assert G["Sicily and Malta"]["rotation"] < 0 < G["England"]["rotation"]                               # anticlockwise; clockwise
assert R["sicily"]["n"] > G["England"]["n"] + G["Central and Eastern Europe"]["n"]
assert R["groups"]["Mediterranean"]["median_local_km"] < R["groups"]["Northern Europe"]["median_local_km"] < R["groups"]["Asia beyond the Euphrates"]["median_local_km"]
assert 1.8 <= R["groups"]["ratio_local_asia"] <= 2.3                                                  # "about twice as faithfully"
assert R["climate_summary"]["monotonic"] and R["climate_summary"]["within_one_pct"] == 100
assert C["7"]["n"] == 3 and C["1"]["n"] >= 5
assert abs(R["britain"]["lat_shift"]) < .1 and R["britain"]["climates"] == [6, 7]
assert 170 <= R["britain"]["london_paris_brg_map"] <= 195                                             # "nearly due south"
assert abs(R["places"]["mecca"]["lon"] - 39.8) < 1 and R["places"]["mecca"]["climate"] == 2
mx = [r for r in SITE["located"] if r[2] == "Mecca"][0][4]
assert abs(mx - IMG_W / 2) < .1 * IMG_W                                                              # "close to the middle of the map"
assert R["jerusalem"]["sim_r2"] > R["hereford"]["fit_r2"] and R["jerusalem"]["sim_median_disp_km"] < R["hereford"]["median_disp_km"]
assert R["jerusalem"]["median_brg_err"] < R["hereford"]["bearing_median_err"]
assert all(24 <= v <= 27 for v in R["routes"]["miles_per_day"])                                       # "a day is about 25 miles"
assert 1.3 <= R["routes"]["road_factor_lo"] and R["routes"]["road_factor_hi"] <= 1.45                  # "a third to two fifths longer"
assert R["routes"]["spearman_map_miles"] > R["routes"]["spearman_map_km"]
assert .15 <= R["nile"]["moon_frac_climate"] <= .19                                                  # "a sixth of the height of a climate"
assert abs(R["affine"]["true_scale_lat"] - 21) < 1.5


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\}|DOI_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = set(re.findall(r"\{\{([^}]*)\}\}", html))
    assert left <= KEEP, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
