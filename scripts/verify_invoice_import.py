"""Comprueba la lectura local del PDF privado sin guardar ni imprimir su texto."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2:
    raise SystemExit("Uso: python scripts/verify_invoice_import.py ruta_al_pdf_local_de_prueba")
PRIVATE_PDF = Path(sys.argv[1])
OUT = ROOT / "artifacts"
BASE = "http://127.0.0.1:8018"
reports = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (375, 1280):
        page = browser.new_page(viewport={"width":width, "height":1000}, locale="es-CL")
        page.add_init_script(path=str(ROOT / ".qa/node_modules/axe-core/axe.min.js"))
        requests, errors = [], []
        page.on("request", lambda r: requests.append((r.method,r.url)))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + "/revisar")
        page.locator("#electricidad").fill("123")
        page.locator("#pdf-archivo").set_input_files(str(PRIVATE_PDF))
        page.wait_for_function("() => !document.getElementById('pdf-archivo').disabled", timeout=20000)
        assert page.locator("#pdf-usar").is_enabled(), page.locator("#pdf-estado").inner_text()
        assert page.locator("#electricidad").input_value() == "123", "No copiar sin confirmación"
        assert not any(method != "GET" for method,url in requests), "El PDF no debe enviarse al servidor"
        assert all(url.startswith(BASE) for method,url in requests), "Sin llamadas a terceros"
        assert page.locator("#pdf-archivo").input_value() == ""
        axe = page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
        assert not axe["violations"], [v["id"] for v in axe["violations"]]
        page.screenshot(path=str(OUT / f"pdf-importacion-{width}.png"), full_page=True)
        page.locator("#pdf-usar").click()
        assert page.locator("#electricidad").input_value() == "26300"
        assert page.locator("#total_documento").input_value() == "35123"
        page.get_by_role("button", name="Comprobar el total").click()
        assert page.get_by_role("heading", name="Los importes coinciden").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        reports.append({"width":width, "total":35123, "pdf_transmitido":False, "terceros":False, "errores_js":errors, "infracciones_axe":[]})
        assert not errors
        page.goto(BASE + "/revisar")
        page.locator("#pdf-archivo").set_input_files({"name":"incorrecto.pdf", "mimeType":"application/pdf", "buffer":b"esto no es PDF"})
        page.wait_for_function("() => !document.getElementById('pdf-archivo').disabled")
        assert "cabecera PDF" in page.locator("#pdf-estado").inner_text()
        page.locator("#pdf-archivo").set_input_files({"name":"grande.pdf", "mimeType":"application/pdf", "buffer":b"%PDF-" + b" " * (6 * 1024 * 1024)})
        page.wait_for_function("() => !document.getElementById('pdf-archivo').disabled")
        assert "hasta 6 MB" in page.locator("#pdf-estado").inner_text()
        page.locator("#pdf-archivo").set_input_files(str(ROOT / "artifacts/fuentes_nacionales/cne_decreto5t2024_c081864796bb.pdf"))
        page.wait_for_function("() => !document.getElementById('pdf-archivo').disabled", timeout=20000)
        assert "12 páginas" in page.locator("#pdf-estado").inner_text()
        page.close()
    browser.close()
(OUT / "invoice-import-browser.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(reports))
