"""Cuenta consolidada: formulario, conservación de datos, teclado y diseño."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
reports=[]
with sync_playwright() as p:
    browser=p.chromium.launch()
    for width in (375,768,1280,1920):
        page=browser.new_page(viewport={"width":width,"height":1000},locale='es-CL')
        page.add_init_script(path=str(ROOT/'.qa/node_modules/axe-core/axe.min.js'))
        errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8018/cuenta')
        page.screenshot(path=str(ROOT/f'artifacts/cuenta-inicio-{width}.png'),full_page=True)
        fields={"lectura_anterior":"2026-10-31","lectura_actual":"2026-11-30","kwh":"100",
            "electricidad_neta_1":"100","transporte_neto_1":"10","servicio_exento_1":"1","fijo_neto_1":"500",
            "respaldo_precios":"Precios ficticios para prueba visual", "total_documento":"13785"}
        for key,value in fields.items(): page.locator('#'+key).fill(value)
        for key in ('demanda','reactiva','otros_afectos','otros_exentos','ajustes_finales'):
            page.locator('#'+key+'_estado').select_option('no_aplica')
            page.locator('#'+key+'_respaldo').fill('Excluido en este escenario ficticio')
        page.get_by_role('button',name='Consolidar mi cuenta').click()
        assert page.get_by_role('heading',name='Total del escenario: $13.785').is_visible()
        assert page.locator('#respaldo_precios').input_value()==fields['respaldo_precios']
        page.locator('#demanda_estado').select_option('declarado')
        # El faltante se rechaza; no se transforma en cero.
        page.get_by_role('button',name='Consolidar mi cuenta').click()
        assert page.get_by_role('alert').is_visible()
        page.locator('#demanda_importe').fill('2000')
        page.get_by_role('button',name='Consolidar mi cuenta').click()
        assert page.get_by_role('heading',name='Total del escenario: $16.165').is_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        axe=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
        assert not axe['violations'],[v['id'] for v in axe['violations']]
        page.screenshot(path=str(ROOT/f'artifacts/cuenta-resultado-{width}.png'),full_page=True)
        for path in ('/','/periodos','/revisar','/fuentes'):
            page.goto('http://127.0.0.1:8018'+path)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,path)
        assert not errors
        reports.append({"width":width,"sin_demanda":13785,"con_demanda":16165,"faltante_rechazado":True,"overflow":False,"errores_js":errors,"infracciones_axe":[]})
        page.close()
    browser.close()
(ROOT/'artifacts/account-browser.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(reports))
