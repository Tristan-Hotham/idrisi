# Al-Idrisi's world

Al-Idrisi's world map, finished in Palermo in 1154 for Roger II of Sicily and drawn with south at the top, set against a modern map: 431 towns read on Konrad Miller's 1928 reconstruction, how far each is out, how the seven climates compare with true latitude, the Nile, Britain, al-Idrisi's own road distances, and a comparison with the Hereford Mappa Mundi.

Interactive page: https://maps.tristanhotham.com/idrisi/
Paper: https://doi.org/10.5281/zenodo.23882607
Blog post: https://blog.tristanhotham.com/2026/10/31/idrisi/

## Headline results

- Towns: 431 labels read on Miller's reconstruction (362 clearly, 69 with some doubt) in 18 regions; 90% snapped to the town symbols detected on the image; 85% confirmed in al-Thurayya, Pleiades or Natural Earth (median 0.7 km apart).
- Direction: over 92,193 pairs of towns at least 100 km apart, the median bearing error (map turned north up) is 10 degrees; 99% are within 45 degrees.
- Whole map: the best affine fit puts the median town 239 km from its real position (R squared 0.98 for longitude, 0.90 for latitude).
- Local shape: median local error (eight nearest neighbours) 55 km; Mediterranean 44 km, northern Europe 71 km, Asia beyond the Euphrates 92 km.
- Sicily: best drawn region (21 km) and drawn largest (1.42 times the map's average scale; Arabia 0.59).
- Climates: in order of latitude, with implied boundaries at 18.0, 28.6, 35.8, 40.4, 47.3, 53.2 degrees north; 74% of towns in the right climate, all within one.
- Road distances (Dozy and de Goeje 1866): 63 routes; median 1.42 km of straight line per stated mile and 36 km per day stage.
- Against Hereford (same method, from Jerusalem): R squared 0.94 against 0.84; median miss 330 km against 516 km; median bearing error 13 against 19 degrees.

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
| `data/routes.csv` | The 63 distances from Dozy and de Goeje (1866), with the OCR line they come from and the true distance. |
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
- Distances: 63 stated distances between identifiable places in Dozy and de Goeje (1866), each checked against its OCR line.
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

- Miller, K. (1928) Charta Rogeriana, Weltkarte des Idrisi vom Jahr 1154. Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Tabula_Rogeriana_1929_copy_by_Konrad_Miller.jpg. Public domain.
- Dozy, R. and de Goeje, M. J. (1866) Description de l'Afrique et de l'Espagne par Edrisi. Leiden: Brill. https://archive.org/details/bub_gb_6EMNNqPF2zAC. Public domain.
- al-Thurayya Gazetteer (M. Seydi and M. Romanov), https://github.com/althurayya/althurayya.github.io. CC BY 4.0.
- Pleiades: a gazetteer of past places, version 4.1, https://pleiades.stoa.org/. CC BY 3.0.
- Natural Earth (public domain). Optional relief tiles on the page: Esri.
- Hotham, T. (2026) The world according to the Hereford Mappa Mundi. https://doi.org/10.5281/zenodo.23878612

## Citation

Hotham, T. (2026) Al-Idrisi's World: The Map Made for Roger II of Sicily in 1154, Set Against a Modern Map. Zenodo. https://doi.org/10.5281/zenodo.23882607

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
