"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23882607, https://doi.org/10.5281/zenodo.23882607 and https://blog.tristanhotham.com/2026/10/31/idrisi/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
import pandas as pd
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Idrisi"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
G = R["regions"]

# numbers written in words or alt text in the blog and collage
P = pd.read_csv(f"{DATA}/located.csv")
med = lambda r, c: float((P[P.region == r]["map_" + c] - P[P.region == r][c]).median())
assert med("Arabia", "lat") > 2 and med("Sind and India", "lon") < -5 and med("Central Asia and Afghanistan", "lat") < -3   # Arabia north, India west, central Asia south
assert [round(b) for b in R["climate_summary"]["bounds"]] == [18, 29, 36, 40, 47, 53]
assert (round(R["jerusalem"]["sim_r2"] * 100), round(R["hereford"]["fit_r2"] * 100), R["jerusalem"]["sim_median_disp_km"], R["hereford"]["median_disp_km"]) == (94, 84, 330, 516)
assert (R["jerusalem"]["median_brg_err"], R["hereford"]["bearing_median_err"], round(R["jerusalem"]["within45_pct"]), round(R["hereford"]["bearing_within45_pct"])) == (13, 19, 99, 81)
assert all(37 <= G[k]["median_local_km"] <= 38 for k in ("Morocco and Algeria", "Iberia", "Italy and Corsica"))
assert 35 <= round(100 * (R["routes"]["road_factor_lo"] - 1)) and round(100 * (R["routes"]["road_factor_hi"] - 1)) <= 41   # "some 35 to 40%"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
from PIL import Image
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Al-Idrisi's world: the map made for Roger II of Sicily, set against a modern one",
        "slug": "idrisi",
        "excerpt": f"In 1154 a Muslim geographer in Palermo drew the known world for the Norman king of Sicily, south at the top. I read {R['source']['n']} of its towns and measured it: directions right to a median {R['pairs']['median_brg_err']} degrees, and Sicily drawn best and biggest of all.",
        "seo_description": f"Al-Idrisi's 1154 world map beside a modern one: {R['source']['n']} towns, seven climates, Sicily drawn best, and a test against the Hereford map.",
        "tags": ["maps", "history", "medieval", "al-Idrisi", "Tabula Rogeriana", "Sicily", "Islamic geography", "cartography", "data visualisation"],
        "header_alt": f"Title card reading 'Al-Idrisi's World' in black and blue on pale paper, beside Konrad Miller's reconstruction of al-Idrisi's map as drawn, with south at the top, and a small modern map of Europe, North Africa and Asia dotted with {R['source']['n']} coloured towns. Text: the map made for Roger II of Sicily in 1154, south at the top, set against a modern one."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/idrisi_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"idrisi/{d}/{fn}")
    for fn in ("idrisi_2000.jpg", "idrisi_4000.jpg"):
        z.write(os.path.join(IMG, fn), f"idrisi/img/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"idrisi/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "idrisi/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Al-Idrisi's World: The Map Made for Roger II of Sicily in 1154, Set Against a Modern Map",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Sources: K. Miller's 1928 reconstruction (Wikimedia Commons, public domain); Dozy and de Goeje (1866), public domain; al-Thurayya Gazetteer (CC BY 4.0); Pleiades (CC BY 3.0); Natural Earth.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["medieval cartography", "Islamic geography", "al-Idrisi", "Tabula Rogeriana", "Roger II", "Sicily", "map distortion", "climates", "Hereford Mappa Mundi", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": DOZY_IA, "relation": "isDerivedFrom", "resource_type": "publication"},
                                 {"identifier": THURAYYA_URL, "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://pleiades.stoa.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.5281/zenodo.23878612", "relation": "references", "resource_type": "publication"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
