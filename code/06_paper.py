"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23882607 placeholder."""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Idrisi"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
G = R["regions"]
assert G["Iberia"]["median_local_km"] == G["Morocco and Algeria"]["median_local_km"]                     # "37 km each"
assert R["rank_local"][:5] == ["Sicily and Malta", "Syria and Palestine", "Morocco and Algeria", "Iberia", "Italy and Corsica"]
assert R["rank_stretch"][:5] == ["Sicily and Malta", "Greece and the Balkans", "England", "Italy and Corsica", "Syria and Palestine"]
assert abs(R["high_only"]["median_local_km"] - R["local"]["median_km"]) <= 5


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "abs": return f"{abs(int(round(float(v)))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


RG = pd.read_csv(f"{DATA}/regions.csv")
f2 = lambda v: "" if pd.isna(v) else f"{v:.2f}"
f0 = lambda v: "" if pd.isna(v) else f"{v:.0f}"
rows = "".join(f"{tex(r.region)} & {r.n} & {r.median_local_km} & {r.median_resid_km:,} & {f0(r.median_brg_err)} & {f2(r.stretch)} & {f2(r.grid_stretch)}\\\\\n" for r in RG.itertuples())
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{Located towns by region: number, median local error (km), median residual of the global affine fit (km), median bearing error between pairs (degrees), stretch relative to the map's average scale, and the stretch a perfect rectangular grid would give. Blank: fewer than five towns.}\\label{tab:regions}"
      "\\begin{tabular}{lrrrrrr}\\toprule Region & Towns & Local & Global & Bearing & Stretch & Grid\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
CL = pd.read_csv(f"{DATA}/climates.csv")
RN = ["", "I", "II", "III", "IV", "V", "VI", "VII"]
rows = "".join(f"{RN[r.climate]} & {r.n} & {r.lat_min:.1f} & {r.lat_median:.1f} & {r.lat_max:.1f} & {'' if pd.isna(r.implied_north) else f'{r.implied_north:.1f}'}\\\\\n" for r in CL.itertuples())
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Towns by climate: number, minimum, median and maximum true latitude (degrees north), and the implied boundary with the next climate.}\\label{tab:climates}"
      "\\begin{tabular}{lrrrrr}\\toprule Climate & Towns & Min & Median & Max & Boundary\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
RT = pd.read_csv(f"{DATA}/routes.csv")
rows = "".join(f"{tex(r['from'])} & {tex(r['to'])} & {'' if pd.isna(r.miles) else int(r.miles)} & {'' if pd.isna(r.days) else int(r.days)} & {r.km:.0f} & {r.ocr_line}\\\\\n" for _, r in RT.iterrows())
TRT = ("{\\footnotesize\\begin{longtable}{p{4.2cm}p{4.2cm}rrrr}\\caption{Distances stated by al-Idrisi in Dozy and de Goeje (1866): miles, day stages, great circle distance today (km) and the line of the Internet Archive text.}\\label{tab:routes}\\\\"
       "\\toprule From & To & Miles & Days & km & Line\\\\\\midrule\\endfirsthead\\toprule From & To & Miles & Days & km & Line\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
L = pd.read_csv(f"{DATA}/located.csv").sort_values(["region", "identification"])
rows = "".join(f"{tex(r.identification)} & {tex(r.label)} & {tex(r.region)} & {RN[int(r.climate)]} & {r.conf} & {r.local_km:.0f}\\\\\n" for r in L.itertuples())
TL = ("{\\footnotesize\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{p{4.6cm}p{3.0cm}p{3.6cm}llr}\\caption{The " + str(len(L)) + " located towns: identification, Miller's transcription, region, climate, my confidence in the reading, and local error (km).}\\label{tab:located}\\\\"
      "\\toprule Town & On the map & Region & Clim. & Reading & Local\\\\\\midrule\\endfirsthead\\toprule Town & On the map & Region & Clim. & Reading & Local\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("REGIONS", TR), ("CLIMATES", TC), ("ROUTES", TRT), ("LOCATED", TL)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
