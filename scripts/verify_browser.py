"""Pruebas de navegador y capturas contra la instancia local (sin red externa)."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8018"


def run():
    report = {"viewports": [], "errors": [], "external_requests": [], "flows": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in [375, 768, 1280, 1920]:
            page = browser.new_page(viewport={"width": width, "height": 1000}, device_scale_factor=1)
            page.on("pageerror", lambda e: report["errors"].append(str(e)))
            page.on("request", lambda r: report["external_requests"].append(r.url) if not r.url.startswith(BASE) else None)
            page.goto(BASE, wait_until="networkidle")
            page.screenshot(path=str(OUT / f"inicio-{width}.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow inicio {width}"
            page.locator("#kwh_directo").fill("250")
            page.locator("#fuente").select_option("referencia")
            page.get_by_role("button", name="Entender mi cuenta").click()
            page.wait_for_url("**/calcular")
            assert page.locator(".total-number").inner_text().startswith("$51.642")
            page.screenshot(path=str(OUT / f"resultado-{width}.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Overflow resultado {width}"
            page.locator("#saving-slider").fill("30")
            page.wait_for_function("() => !document.getElementById('saving-total').textContent.includes('Calculando')")
            assert page.locator("#saving-error").is_hidden()
            with page.expect_download() as download:
                page.locator("#export-csv").click()
            download.value.save_as(str(OUT / f"resultado-{width}.csv"))
            assert "Metodología" in (OUT / f"resultado-{width}.csv").read_text(encoding="utf-8-sig")
            if width == 1280:
                page.locator(".calculation-details").evaluate("e=>e.open=true")
                page.pdf(path=str(OUT / "resultado-ejemplo.pdf"), format="A4", print_background=True)
            page.goto(BASE + "/comunas")
            page.locator("#buscar-comuna").fill("valparaiso")
            assert page.locator(".comuna-tag:visible").count() == 1
            page.locator("#buscar-comuna").fill("no existe esta comuna")
            assert page.locator("#search-empty").is_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.goto(BASE + "/metodologia")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(OUT / f"metodologia-{width}.png"), full_page=True)
            report["viewports"].append({"width": width, "overflow": False, "flows": "inicio, resultados, slider, CSV, cobertura, metodología"})
            page.close()
        page = browser.new_page()
        page.goto(BASE)
        page.locator("#fuente").select_option("personalizada")
        page.locator("#precio_kwh").fill("240")
        page.locator("#cargo_fijo").fill("750")
        page.locator("#boleta_actual").evaluate("e => e.closest('details').open=true")
        page.locator("#boleta_actual").fill("65000")
        page.get_by_role("button", name="Entender mi cuenta").click()
        assert "$60.750" in page.locator(".total-number").inner_text()
        assert "$4.250" in page.locator(".comparison-card").inner_text()
        report["flows"].append("Precios propios: 250 × 240 + 750 = 60.750; diferencia 4.250")
        page.goto(BASE)
        page.get_by_role("button", name="Estimar por aparatos").click()
        page.locator("#fuente").select_option("referencia")
        page.locator("#aparato_tv").check()
        page.locator("[name=horas_tv]").fill("5")
        page.locator("#dias").fill("10")
        assert page.locator("#appliance-kwh").inner_text() == "5 kWh"
        page.get_by_role("button", name="Entender mi cuenta").click()
        assert "5.0 kWh" in page.locator(".result-heading").inner_text()
        report["flows"].append("Aparatos: TV 100 W × 5 h × 10 días = 5 kWh")
        page.close()
        browser.close()
    assert not report["errors"], report["errors"]
    assert not report["external_requests"], report["external_requests"]
    (OUT / "browser-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True))


if __name__ == "__main__":
    run()
