"""Casos ficticios BT3/AT3: cargo, ventanas, precisión y accesibilidad."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_account_helpers import consolidate_transferred_account
ROOT = Path(__file__).resolve().parents[1]
reports = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (375,768,1280):
        page = browser.new_page(viewport={"width":width,"height":1000}, locale="es-CL")
        page.add_init_script(path=str(ROOT / ".qa/node_modules/axe-core/axe.min.js"))
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://127.0.0.1:8018/demanda-3")
        page.locator("#mes_facturacion").fill("2026-11")
        page.locator("#actualizar-meses").click()
        assert page.locator("#historial-demanda h3").first.inner_text() == "2025-11"
        page.locator("#clasificacion").select_option("presente_en_punta")
        page.locator("#precio_demanda_neto").fill("1000")
        months = ["2025-11","2025-12"] + [f"2026-{i:02d}" for i in range(1,12)]
        for index, m in enumerate(months):
            if index:
                maximum = 120 if m == "2026-05" else 100 if m == "2026-08" else 50
                page.locator("#max_" + m).fill(str(maximum))
                if m in [f"2026-{i:02d}" for i in range(4,10)]:
                    page.locator(f"[name=calendario_{m}]").check()
            if index < 12:
                charge = 400000 if m == "2026-05" else 100000 if m == "2026-08" else 50000
                page.locator("#cargo_" + m).fill(str(charge))
        page.get_by_role("button",name="Revisar cargo de demanda").click()
        assert page.get_by_role("heading",name="Cargo de demanda neto: $160.000").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(ROOT / f"artifacts/demanda3-{width}.png"),full_page=True)
        page.locator("#cargo_2025-11").fill("1000000")
        page.get_by_role("button",name="Revisar cargo de demanda").click()
        assert page.get_by_role("heading",name="La ventana del mínimo cambia el resultado.").is_visible()
        assert page.get_by_role("heading",name="Cargo de demanda neto:").count() == 0
        page.locator("#ventana_minimo_confirmada").select_option("doce_previos")
        page.get_by_role("button",name="Revisar cargo de demanda").click()
        assert page.get_by_role("heading",name="Cargo de demanda neto: $400.000").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        axe = page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
        assert not axe["violations"], [v["id"] for v in axe["violations"]]
        consolidate_transferred_account(page,489785)
        page.screenshot(path=str(ROOT / f"artifacts/cuenta-desde-bt3-{width}.png"),full_page=True)
        page.get_by_role('button',name='Guardar este escenario',exact=True).click()
        page.goto('http://127.0.0.1:8018/cuenta')
        page.get_by_role('button',name='Ver escenarios guardados').click()
        page.get_by_role('button',name='Cargar valores',exact=True).click()
        page.locator('[name=datos_demanda]').wait_for(state='attached')
        page.wait_for_function("() => document.getElementById('kwh').value === '100'")
        assert page.locator('#demanda_respaldo').input_value()==''
        assert len(json.loads(page.locator('[name=datos_demanda]').input_value())['historico'])==13
        assert not errors
        reports.append({"width":width,"caso_comun_neto":160000,"ventana_alternativa_neto":400000,
            "cuenta_consolidada_total":489785,"bloqueo_cargo_unico_sin_ventana":True,"overflow":False,"errores_js":errors,"infracciones_axe":[]})
        page.close()
    browser.close()
(ROOT / "artifacts/demand3-browser.json").write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(reports))
