"""Recorridos nuevos con datos ficticios y diagnóstico anonimizado, sin PII."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8018'
reports=[]


def fill_account(page, *,kwh='100',energy='100',fixed='500'):
    for key,value in {'lectura_anterior':'2026-10-31','lectura_actual':'2026-11-30','kwh':kwh,
        'electricidad_neta_1':energy,'transporte_neto_1':'10','servicio_exento_1':'1','fijo_neto_1':fixed,
        'respaldo_precios':'Texto privado ficticio que no debe guardarse'}.items():page.locator('#'+key).fill(value)
    for key in ('demanda','reactiva','otros_afectos','otros_exentos','ajustes_finales'):
        page.locator('#'+key+'_estado').select_option('no_aplica')
        page.locator('#'+key+'_respaldo').fill('Otro texto privado ficticio')


def audit(page,width,label):
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,label)
    axe=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
    assert not axe['violations'],(label,[r['id'] for r in axe['violations']])
    page.screenshot(path=str(ROOT/f'artifacts/workspace-{label}-{width}.png'),full_page=True)


with sync_playwright() as p:
    browser=p.chromium.launch()
    for width in (375,768,1280):
        context=browser.new_context(viewport={'width':width,'height':1000},locale='es-CL')
        page=context.new_page();errors=[]
        page.add_init_script(path=str(ROOT/'.qa/node_modules/axe-core/axe.min.js'))
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(BASE)
        assert page.locator('.journey-card').count()==3
        audit(page,width,'inicio')
        page.goto(BASE+'/cuenta');fill_account(page)
        page.get_by_role('button',name='Consolidar mi cuenta').click()
        assert page.get_by_role('heading',name='Total del escenario: $13.785').is_visible()
        assert page.evaluate("localStorage.getItem('cuentaluz.escenarios.v1')")==None
        page.get_by_role('button',name='Guardar este escenario',exact=True).click()
        raw=page.evaluate("localStorage.getItem('cuentaluz.escenarios.v1')")
        assert 'Texto privado ficticio' not in raw and 'Otro texto privado ficticio' not in raw
        assert len(json.loads(raw))==1
        page.locator('#kwh').fill('150');page.locator('#electricidad_neta_1').fill('200');page.locator('#fijo_neto_1').fill('1000')
        assert page.get_by_role('button',name='Guardar este escenario',exact=True).is_disabled()
        page.get_by_role('button',name='Consolidar mi cuenta').click()
        assert page.get_by_role('heading',name='Total del escenario: $38.825').is_visible()
        page.get_by_role('button',name='Guardar este escenario',exact=True).click()
        records=json.loads(page.evaluate("localStorage.getItem('cuentaluz.escenarios.v1')"))
        page.locator('#comparar-anterior').select_option(records[0]['id']);page.locator('#comparar-actual').select_option(records[1]['id'])
        page.get_by_role('button',name='Recalcular comparación').click()
        page.get_by_role('heading',name='Comparación recalculada').wait_for(state='visible')
        assert '6.595' in page.locator('#comparacion-guardados').inner_text()
        page.get_by_role('button',name='Cargar valores').first.click()
        assert page.locator('#kwh').input_value()=='100' and page.locator('#respaldo_precios').input_value()==''
        page.get_by_role('button',name='Eliminar',exact=True).last.click()
        assert len(json.loads(page.evaluate("localStorage.getItem('cuentaluz.escenarios.v1')")))==1
        page.goto(BASE+'/cuenta');page.get_by_role('button',name='Ver escenarios guardados').click()
        assert page.get_by_role('button',name='Cargar valores').count()==1
        audit(page,width,'guardados')
        # Diagnóstico Enel: se conserva la discrepancia por cargo aunque el total cierre.
        d=json.loads((ROOT/'config/enel_macul_temporal_diagnostico.json').read_text(encoding='utf-8'))['entrada']
        for key in ('lectura_anterior','lectura_actual','kwh'):page.locator('#'+key).fill(d[key])
        page.locator('#cambio').fill('2026-10-01')
        for n,price in enumerate(d['precios'],1):
            for key in ('electricidad_neta','transporte_neto','servicio_exento','fijo_neto'):page.locator(f'#{key}_{n}').fill(price[key])
        page.locator('#respaldo_precios').fill('Diagnóstico anonimizado; red, tramo y aplicación temporal pendientes')
        for key in ('demanda','reactiva','otros_afectos','otros_exentos','ajustes_finales'):
            page.locator('#'+key+'_estado').select_option('no_aplica');page.locator('#'+key+'_respaldo').fill('Excluido según este caso de prueba')
        page.locator('#redondeo').select_option('sobre_subtotal')
        page.get_by_text('Comparar cada cargo con mi documento · opcional',exact=True).click()
        observed={'electricidad':26300,'transporte':2497,'administracion':614,'demanda':0,'reactiva':0,'otros_afectos':0,'neto_afecto':29411,'iva':5588,'exentos':124,'ajustes_finales':0,'total':35123}
        for key,value in observed.items():page.locator('#obs_'+key).fill(str(value))
        page.get_by_role('button',name='Consolidar mi cuenta').click()
        assert page.get_by_text('El total coincide, pero hay cargos distintos.',exact=True).is_visible()
        audit(page,width,'diferencias')
        page.evaluate("window.__originalPrint=window.print;window.print=()=>{window.dispatchEvent(new Event('beforeprint'));window.__printed=true;window.dispatchEvent(new Event('afterprint'));}")
        page.get_by_role('button',name='Descargar informe PDF / imprimir',exact=True).click()
        assert page.evaluate("window.__printed===true && !document.body.classList.contains('printing-account')")
        page.evaluate("window.print=window.__originalPrint")
        if width==1280:
            page.evaluate("document.body.classList.add('printing-account');document.querySelectorAll('#informe-cuenta details').forEach(e=>e.open=true)")
            page.pdf(path=str(ROOT/'artifacts/informe-cuenta-ejemplo.pdf'),format='A4',print_background=True,margin={'top':'15mm','bottom':'15mm','left':'14mm','right':'14mm'})
            page.evaluate("document.body.classList.remove('printing-account')")
        page.goto(BASE+'/cobertura-validada?cut=13118&empresa=ENEL&opcion=BT1&mes=2026-11')
        assert page.get_by_role('heading',name='Macul',exact=True).is_visible()
        assert page.get_by_text('Sin valores normalizados en este lote',exact=True).is_visible()
        audit(page,width,'cobertura')
        page.goto(BASE+'/comparar')
        for key,value in {'lectura_anterior':'2026-10-31','lectura_actual':'2026-11-30','kwh':'100'}.items():page.locator('#'+key).fill(value)
        for n,price in [(1,'100'),(2,'90'),(3,'110')]:
            page.locator(f'#opcion_{n}').select_option('BT3')
            for key,value in {'energia':price,'transporte':'10','exento':'1','fijo':'500','demanda':'0','reactiva':'0','otros_afectos':'0','otros_exentos':'0','ajustes_finales':'0','respaldo':'Escenario ficticio, aplicabilidad pendiente'}.items():page.locator(f'#{key}_{n}').fill(value)
        page.get_by_role('button',name='Comparar escenarios',exact=True).click()
        assert page.get_by_text('No se destaca un menor costo porque falta confirmar aplicabilidad.',exact=True).is_visible()
        audit(page,width,'comparar')
        assert not errors,errors
        reports.append({'width':width,'escenarios_locales':True,'sin_textos_libres_guardados':True,'descomposicion':True,'total_coincidente_no_oculta_diferencia':True,'comparador_no_recomienda_tarifa':True,'overflow':False,'errores_js':errors,'axe_violations':[]})
        context.close()
    browser.close()
(ROOT/'artifacts/workspace-browser.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(reports))
