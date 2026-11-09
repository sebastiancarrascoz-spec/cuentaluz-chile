"""Flujo ficticio de demandas: comprueba históricos, interfaz y accesibilidad."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_account_helpers import consolidate_transferred_account
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
reports = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (375, 768, 1280):
        page = browser.new_page(viewport={"width":width, "height":1000})
        page.add_init_script(path=str(ROOT / ".qa/node_modules/axe-core/axe.min.js"))
        page.goto("http://127.0.0.1:8018/demanda")
        page.locator("#mes_facturacion").fill("2026-11")
        page.locator("#actualizar-meses").click()
        assert page.locator("#historial-demanda h3").first.inner_text() == "2025-12"
        for m in ["2025-12"] + [f"2026-{i:02d}" for i in range(1,12)]:
            maximum = 120 if m == "2026-05" else 100 if m == "2026-08" else 50
            page.locator("#max_" + m).fill(str(maximum))
            if m in [f"2026-{i:02d}" for i in range(4,10)]:
                page.locator(f"[name=calendario_{m}]").check()
                peak = 80 if m == "2026-05" else 60 if m == "2026-08" else 20
                page.locator("#punta_" + m).fill(str(peak))
        page.locator("#meses_punta_anterior").fill(",".join(f"2026-{i:02d}" for i in range(4,10)))
        page.get_by_role("button", name="Revisar demandas").click()
        assert page.get_by_text("110 kW", exact=True).is_visible()
        assert page.get_by_text("70 kW", exact=True).is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(OUT / f"demanda-{width}.png"), full_page=True)
        axe = page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
        consolidate_transferred_account(page,358885,prices4=True)
        page.screenshot(path=str(OUT / f"cuenta-desde-bt43-{width}.png"),full_page=True)
        reports.append({"width":width, "demanda_suministrada_kw":110, "punta_kw":70,"cuenta_consolidada_total":358885,
            "overflow":False, "violations":[{"id":v["id"], "nodes":[n["target"] for n in v["nodes"]]} for v in axe["violations"]]})
        page.close()
    browser.close()
(OUT / "demand-browser.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(reports))
assert not any(r["violations"] for r in reports)
