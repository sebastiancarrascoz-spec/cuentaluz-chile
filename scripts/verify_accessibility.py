"""Auditoría automática WCAG 2.1 A/AA. No sustituye pruebas manuales con usuarios."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
axe = ROOT / ".qa" / "node_modules" / "axe-core" / "axe.min.js"
reports = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in [375, 1280]:
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.add_init_script(path=str(axe))
        for path in ["/", "/comunas", "/metodologia", "/fuentes", "/revisar", "/calcular"]:
            page.goto("http://127.0.0.1:8018/")
            if path == "/calcular":
                page.locator("#fuente").select_option("referencia")
                page.get_by_role("button", name="Entender mi cuenta").click()
                page.wait_for_url("**/calcular")
            else:
                page.goto("http://127.0.0.1:8018" + path)
            result = page.evaluate("async () => await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
            reports.append({"path": path, "width": width,
                "violations": [{"id": v["id"], "impact": v["impact"], "description": v["description"], "nodes": [n["target"] for n in v["nodes"]]} for v in result["violations"]],
                "incomplete": [{"id": v["id"], "nodes": [n["target"] for n in v["nodes"]]} for v in result["incomplete"]]})
        page.close()
    browser.close()
(ROOT / "artifacts" / "accessibility.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(reports, ensure_ascii=True))
assert not any(r["violations"] for r in reports)
