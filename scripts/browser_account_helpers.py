"""Datos ficticios comunes para el flujo visual de demanda a cuenta."""
def consolidate_transferred_account(page, expected, *, prices4=False):
    page.get_by_role('button',name='Incorporar demanda a mi cuenta').click()
    assert page.locator('[name=datos_demanda]').count()==1
    assert page.locator('[name=demanda_importe]').count()==0
    fields={"lectura_anterior":"2026-10-31","lectura_actual":"2026-11-30","kwh":"100",
        "electricidad_neta_1":"100","transporte_neto_1":"10","servicio_exento_1":"1","fijo_neto_1":"500",
        "respaldo_precios":"Precios ficticios para probar el flujo", "demanda_respaldo":"Históricos y precios ficticios"}
    if prices4:fields.update(precio_punta_neto='1000',precio_suministrada_o_contratada_neto='2000')
    for key,value in fields.items():page.locator('#'+key).fill(value)
    for key in ('reactiva','otros_afectos','otros_exentos','ajustes_finales'):
        page.locator('#'+key+'_estado').select_option('no_aplica')
        page.locator('#'+key+'_respaldo').fill('Excluido en el caso ficticio')
    page.get_by_role('button',name='Consolidar mi cuenta').click()
    formatted=f'{expected:,}'.replace(',','.')
    assert page.get_by_role('heading',name='Total del escenario: $'+formatted).is_visible()
    page.get_by_text('Registros y método utilizados',exact=True).click()
    assert page.get_by_role('rowheader',name='2026-05',exact=True).is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    axe=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
    assert not axe['violations'], [v['id'] for v in axe['violations']]
