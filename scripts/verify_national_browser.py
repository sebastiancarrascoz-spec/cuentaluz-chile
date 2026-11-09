"""Verifica los nuevos flujos nacionales contra el servidor local."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
report = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (375, 768, 1280, 1920):
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto("http://127.0.0.1:8018/revisar")
        for field, value in {"electricidad":26300, "transporte":2497, "administracion":614,
                "exentos":124, "total_documento":35123}.items():
            page.locator("#" + field).fill(str(value))
        page.get_by_role("button", name="Comprobar el total").click()
        assert page.get_by_role("heading", name="Los importes coinciden").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(OUT / f"revision-{width}.png"), full_page=True)
        page.goto("http://127.0.0.1:8018/comunas")
        assert page.locator(".comuna-tag").count() == 346
        page.locator("#buscar-comuna").fill("punta arenas")
        assert "EDELMAG" in page.locator(".comuna-tag:visible").inner_text()
        page.screenshot(path=str(OUT / f"cobertura-nacional-{width}.png"), full_page=True)
        page.goto("http://127.0.0.1:8018/fuentes")
        page.locator(".coverage-grid details").first.evaluate("e=>e.open=true")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(OUT / f"fuentes-{width}.png"), full_page=True)
        report.append({"width": width, "conciliacion":35123, "comunas":346, "overflow":False})
        page.close()
    browser.close()
(OUT / "national-browser.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
