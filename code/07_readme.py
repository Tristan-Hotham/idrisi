"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, g, a, lo, gr, J, H, rt = R["source"], R["regions"], R["affine"], R["local"], R["groups"], R["jerusalem"], R["hereford"], R["routes"]
cb = R["climate_summary"]["bounds"]
TITLE = "Al-Idrisi's World: The Map Made for Roger II of Sicily in 1154, Set Against a Modern Map"
readme = f"""# Al-Idrisi's world

Al-Idrisi's world map, finished in Palermo in 1154 for Roger II of Sicily and drawn with south at the top, set against a modern map: {s['n']} towns read on Konrad Miller's 1928 reconstruction, how far each is out, how the seven climates compare with true latitude, the Nile, Britain, al-Idrisi's own road distances, and a comparison with the Hereford Mappa Mundi.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Towns: {s['n']} labels read on Miller's reconstruction ({s['high']} clearly, {s['medium']} with some doubt) in {s['regions']} regions; {s['snapped_pct']:.0f}% snapped to the town symbols detected on the image; {s['checked_pct']:.0f}% confirmed in al-Thurayya, Pleiades or Natural Earth (median {s['check_median_km']} km apart).
- Direction: over {R['pairs']['n']:,} pairs of towns at least 100 km apart, the median bearing error (map turned north up) is {R['pairs']['median_brg_err']} degrees; {R['pairs']['within45_pct']:.0f}% are within 45 degrees.
- Whole map: the best affine fit puts the median town {a['median_resid_km']} km from its real position (R squared {a['r2_lon']:.2f} for longitude, {a['r2_lat']:.2f} for latitude).
- Local shape: median local error (eight nearest neighbours) {lo['median_km']} km; Mediterranean {gr['Mediterranean']['median_local_km']} km, northern Europe {gr['Northern Europe']['median_local_km']} km, Asia beyond the Euphrates {gr['Asia beyond the Euphrates']['median_local_km']} km.
- Sicily: best drawn region ({g['Sicily and Malta']['median_local_km']} km) and drawn largest ({g['Sicily and Malta']['stretch']:.2f} times the map's average scale; Arabia {g['Arabia']['stretch']:.2f}).
- Climates: in order of latitude, with implied boundaries at {', '.join(f'{b:.1f}' for b in cb)} degrees north; {R['climate_summary']['right_climate_pct']:.0f}% of towns in the right climate, all within one.
- Road distances (Dozy and de Goeje 1866): {rt['n']} routes; median {rt['median_km_per_mile']:.2f} km of straight line per stated mile and {rt['median_km_per_day']} km per day stage.
- Against Hereford (same method, from Jerusalem): R squared {J['sim_r2']:.2f} against {H['fit_r2']:.2f}; median miss {J['sim_median_disp_km']} km against {H['median_disp_km']} km; median bearing error {J['median_brg_err']} against {H['bearing_median_err']} degrees.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded; map tiles in `img/tiles/`). |
| `header.png` | Social card, 1200 x 630. |
| `img/tiles/` | Miller's reconstruction as WebP web tiles (zoom 1 to 7, full resolution at 7), public domain. |
| `img/idrisi_2000.jpg`, `img/idrisi_4000.jpg` | The whole map, reduced (fallback view and figures). |
| `data/map_positions.csv` | My readings: Miller's transcription, identification, pixel on the image as drawn, confidence (input). |
| `data/map_points.csv` | The readings snapped to the detected town symbols, with climate, section and north-up pixel. |
| `data/located.csv` | Every located town: identification, region, modern position, map position, climate, fitted position, global residual, local error, gazetteer checks. |
| `data/routes.csv` | The {rt['n']} distances from Dozy and de Goeje (1866), with the OCR line they come from and the true distance. |
| `data/regions.csv`, `data/climates.csv` | Measures by region and by climate. |
| `data/climate_lines.json` | The climate lines detected on the image, by section. |
| `data/results.json`, `data/site.json`, `data/world.json`, `data/places.json`, `data/fit.json`, `data/hereford.json`, `data/sources.json` | Every number used; page data; outlines; places with gazetteer checks; image facts; the Hereford numbers; source facts. |
| `code/` | Scripts, run in order, the page, paper and blog templates, `coords_hand.py` (my modern positions and regions), `reading.py` (the route distances read from the text) and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Positions: town labels read by eye at full resolution on Miller's sheet; positions snapped to town symbols detected by shape and by template matching; unsnapped positions checked on close-ups.
- Modern positions: mine, checked by name against al-Thurayya, Pleiades and Natural Earth (matches within 150 km; over 30 km reviewed).
- Measures (map turned north up): global affine fit to longitude and latitude; local error from an affine fit to the eight nearest neighbours; pairwise bearing error and stretch by region (at least five towns); implied climate boundaries; the Hereford study's similarity fit and bearings about Jerusalem.
- Distances: {rt['n']} stated distances between identifiable places in Dozy and de Goeje (1866), each checked against its OCR line.
- Caveats: Miller's reconstruction is a modern redrawing; the sample is the legible, identifiable towns and is thin in India, eastern Europe and Africa south of the Sahara; identifications are mine; the Arab mile's length is uncertain.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely, pyproj, matplotlib, Pillow, OpenCV and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Steps 01 and 02 read `raw/` (not published: the map image, the OCR of Dozy and de Goeje, al-Thurayya), Pleiades from `/home/claude/rawstore/mappa-mundi/pleiades/`, Natural Earth from `/home/claude/newdata/raw/geo/` and the Hereford results from `../mappa-mundi/data/results.json`; from step 03 on only `data/` and `img/` are needed. Intermediate files go to `/dev/shm/idrisi/work` (set `IDTMP` to change).

```
python3 code/01_map.py          # town symbols, snapping, climate lines, web tiles
python3 code/02_geo.py          # outlines, gazetteer checks, route distances, Hereford numbers
python3 code/03_results.py      # results.json, tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Miller, K. (1928) Charta Rogeriana, Weltkarte des Idrisi vom Jahr 1154. Wikimedia Commons, {MILLER_URL}. Public domain.
- Dozy, R. and de Goeje, M. J. (1866) Description de l'Afrique et de l'Espagne par Edrisi. Leiden: Brill. {DOZY_IA}. Public domain.
- al-Thurayya Gazetteer (M. Seydi and M. Romanov), {THURAYYA_URL}. CC BY 4.0.
- Pleiades: a gazetteer of past places, version {PLEIADES_VER}, https://pleiades.stoa.org/. CC BY 3.0.
- Natural Earth (public domain). Optional relief tiles on the page: Esri.
- Hotham, T. (2026) The world according to the Hereford Mappa Mundi. https://doi.org/10.5281/zenodo.23878612

## Citation

Hotham, T. (2026) {TITLE}. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/rocket-launches/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. Konrad Miller's 1928
reconstruction of al-Idrisi's map (img/, from Wikimedia Commons) and the text
of Dozy and de Goeje (1866) quoted in data/routes.csv are in the public
domain. Gazetteer checks use the al-Thurayya Gazetteer (M. Seydi and
M. Romanov, github.com/althurayya), CC BY 4.0, and Pleiades
(pleiades.stoa.org), CC BY 3.0: please credit both. Natural Earth is public
domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] I measured al-Idrisi's 1154 world map, drawn with south at the top, against a real one: {s['n']} towns, directions right to a median {R['pairs']['median_brg_err']} degrees, and the best drawn place is Sicily, where it was made

## Body

Al-Idrisi drew this map in Palermo for Roger II, the Norman king of Sicily, on a grid of seven climates (bands of latitude) and ten sections, with south at the top. I read {s['n']} town labels on Konrad Miller's 1928 reconstruction, matched them to real places, and turned the map north up. Between pairs of towns, directions are right to a median {R['pairs']['median_brg_err']} degrees. Locally the map is most faithful around the Mediterranean (median {gr['Mediterranean']['median_local_km']} km off, judged from each town's 8 nearest neighbours) and worst in Asia beyond the Euphrates ({gr['Asia beyond the Euphrates']['median_local_km']} km). Sicily is both the best drawn region ({g['Sicily and Malta']['median_local_km']} km) and drawn biggest ({g['Sicily and Malta']['stretch']:.2f}x the map's average scale). Measured exactly like my earlier study of the Hereford Mappa Mundi (about 1300), the median town lands {J['sim_median_disp_km']} km from where it should be, against {H['median_disp_km']} km on Hereford. Caveats: positions read by eye on a modern redrawing; thin coverage in India, eastern Europe and West Africa. Interactive side by side map (you can turn the old map north up): {PAGE}

## Source comment

Sources: Konrad Miller's 1928 reconstruction (Wikimedia Commons, public domain); Dozy and de Goeje (1866) for al-Idrisi's road distances (public domain); al-Thurayya gazetteer (CC BY 4.0) and Pleiades (CC BY 3.0) to check identifications; Natural Earth.

Tools: Python (pandas, scipy, pyproj, OpenCV, matplotlib); MapLibre for the interactive maps.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
