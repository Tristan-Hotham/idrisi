// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server PORT; set PORT). MapLibre comes from a local npm
// copy (the CDN is not reachable from the build container); relief tiles and fonts are blocked here. NOML=1 blocks
// MapLibre too, to check that the page degrades gracefully.
const { chromium } = require("playwright");
const fs = require("fs");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  const sizes = process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]];
  for (const [nm, vw, vh] of sizes) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    if (process.env.NOML) await p.route(/maplibre-gl/, r => r.abort());
    else {
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    }
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + process.env.PORT + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(4500);
    const tag = process.env.NOML ? "noml_" : "";
    await p.screenshot({ path: `qa/${tag}${nm}_top.png` });
    const shot = async (sel, f, wait = 1500) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(wait); await p.locator(sel).screenshot({ path: `qa/${tag}${nm}_${f}.png` }); };
    await shot("#atlas", "atlas", 3000);
    await p.fill("#q", "Palermo"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(3000); await shot("#atlas", "palermo");
    await p.click('#viewRow .btn[data-north]'); await p.waitForTimeout(2500); await shot("#atlas", "north");
    await p.click('#viewRow .btn[data-grid]'); await p.waitForTimeout(1200); await shot("#atlas", "grid");
    await p.click('#viewRow .btn[data-col="error"]'); await p.waitForTimeout(1200); await shot("#atlas", "error");
    await p.click('#viewRow .btn[data-col="region"]'); await p.click('#viewRow .btn[data-grid]'); await p.click('#viewRow .btn[data-north]');
    await p.click('#focusRow .btn:nth-child(5)'); await p.waitForTimeout(2500); await shot("#atlas", "nile");
    await p.fill("#q", "London"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(3000); await shot("#atlas", "london");
    if (!process.env.NOML) {
      await p.locator("#wmap .lyrBtn").click(); await p.waitForTimeout(300);
      await p.locator('#wmap input[data-l="arrows"]').check(); await p.locator('#wmap input[data-l="routes"]').check(); await p.waitForTimeout(400);
      await p.locator("#wmap .lyrBtn").click();
      await p.click('#focusRow .btn:nth-child(2)'); await p.waitForTimeout(2500); await shot("#atlas", "layers");
      await p.locator("#wmap .lyrBtn").click(); await p.waitForTimeout(300); await shot("#atlas", "layerpanel", 500);
      await p.locator('#wmap input[data-l="arrows"]').uncheck(); await p.locator('#wmap input[data-l="routes"]').uncheck(); await p.locator("#wmap .lyrBtn").click();
      await p.click('#regTable tr[data-k="Iberia"]'); await p.waitForTimeout(2500); await shot("#atlas", "iberia");
    }
    for (const c of ["climChart", "regChart", "routeChart", "cmpChart", "regTable"]) await shot("#" + c, c, 600);
    if (nm === "phone" && !process.env.NOML) {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_atlas"); await shot("#climChart", "dark_clim");
      await p.locator("#wmap").scrollIntoViewIfNeeded(); await p.locator("#wmap .mfs-btn").click(); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
