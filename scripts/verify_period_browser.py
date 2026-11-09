"""Escenario diagnóstico de dos precios: interfaz, redondeo y accesibilidad."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "config/enel_macul_temporal_diagnostico.json").read_text(encoding="utf-8"))["entrada"]
reports = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (375, 768, 1280):
        page = browser.new_page(viewport={"width":width, "height":1000}, locale="es-CL")
        page.add_init_script(path=str(ROOT / ".qa/node_modules/axe-core/axe.min.js"))
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://127.0.0.1:8018/periodos")
        for key in ("lectura_anterior", "lectura_actual", "kwh"):
            page.locator("#" + key).fill(data[key])
        page.locator("#cambio").fill("2026-10-01")
        for i, price in enumerate(data["precios"],1):
            for key in ("electricidad_neta", "transporte_neto", "servicio_exento", "fijo_neto"):
                page.locator(f"#{key}_{i}").fill(price[key])
        page.get_by_role("button", name="Calcular escenario por períodos").click()
        assert page.get_by_role("heading", name="Total del escenario: $35.124").is_visible()
        assert page.get_by_text("36,250000", exact=True).is_visible()
        page.locator("#redondeo").select_option("sobre_subtotal")
        page.get_by_role("button", name="Calcular escenario por períodos").click()
        assert page.get_by_role("heading", name="Total del escenario: $35.123").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(ROOT / f"artifacts/periodos-{width}.png"), full_page=True)
        axe = page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
        assert not axe["violations"], [v["id"] for v in axe["violations"]]
        page.locator("#modo_fijo").select_option("declarado")
        page.locator("#fijo_neto_periodo").fill("614")
        for n in (1,2):
            page.locator(f"#fijo_neto_{n}").fill("")
        page.get_by_role("button", name="Calcular escenario por períodos").click()
        assert page.get_by_role("heading", name="Total del escenario: $35.123").is_visible()
        assert not errors
        reports.append({"width":width, "por_cargo":35124, "sobre_subtotal":35123,
            "overflow":False, "errores_js":errors, "infracciones_axe":[]})
        page.close()
    browser.close()
(ROOT / "artifacts/period-browser.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(reports))
