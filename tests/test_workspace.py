from copy import deepcopy
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from main import app
from app.services.account_service import AccountInput, evaluar_cuenta
from app.services.comparison_service import ComparisonInput, SavedComparisonInput, compare_scenarios, compare_saved
from app.services.coverage_service import CoverageQuery, validation_coverage
from tests.test_account import case


def enel_case(rounding):
    d=case()
    d['periodo']=json.loads((Path(__file__).parents[1]/'config/enel_macul_temporal_diagnostico.json').read_text(encoding='utf-8'))['entrada']
    d['periodo']['redondeo']=rounding
    d['observado']={'electricidad':26300,'transporte':2497,'administracion':614,'demanda':0,'reactiva':0,'otros_afectos':0,
        'neto_afecto':29411,'iva':5588,'exentos':124,'ajustes_finales':0,'total':35123}
    return d


def test_enel_equal_total_does_not_hide_electricity_difference_or_reassign_rounding():
    result=evaluar_cuenta(AccountInput(**enel_case('sobre_subtotal')))
    r=result['revision']
    assert result['total']==35123 and r['total_coincide_con_cargos_distintos']
    electricity=next(x for x in r['filas'] if x['id']=='electricidad')
    assert electricity['diferencia']==-1 and electricity['diferencia_de_un_peso']
    assert r['ajuste_observado_entre_cargos_y_neto']==0
    assert r['ajuste_calculado_entre_cargos_y_neto']==-1
    assert result['tarifa_oficial_validada'] is False


def test_enel_line_rounding_preserves_gap_instead_of_fitting_total():
    r=evaluar_cuenta(AccountInput(**enel_case('por_cargo')))
    assert r['total']==35124 and not r['revision']['total_coincide']


def test_missing_observed_is_not_zero_and_bad_summary_is_identified():
    d=case();d['observado']={'neto_afecto':100,'iva':19,'exentos':0,'ajustes_finales':0,'total':120}
    r=evaluar_cuenta(AccountInput(**d))['revision']
    assert next(x for x in r['filas'] if x['id']=='demanda')['observado'] is None
    assert r['avisos'] and r['ajuste_observado_entre_cargos_y_neto'] is None
    d['total_documento']=999
    with pytest.raises(ValidationError):AccountInput(**d)


def scenarios():
    a=case();b=case();b['periodo']['precios'][0]['electricidad_neta']='90'
    return {'escenarios':[{'nombre':'Actual','opcion':'BT3','aplicabilidad_declarada':True,'respaldo_aplicabilidad':'Ficticio','cuenta':a},
        {'nombre':'Alternativa','opcion':'AT3','aplicabilidad_declarada':False,'respaldo_aplicabilidad':'Pendiente','cuenta':b}]}


def test_no_lowest_cost_highlight_without_declared_applicability():
    d=scenarios();r=compare_scenarios(ComparisonInput(**d))
    assert r['menor_costo_declarado']==[] and r['recomendacion_tarifaria'] is None
    assert r['escenarios'][1]['diferencia_respecto_base']==-1190
    d['escenarios'][1]['aplicabilidad_declarada']=True
    r=compare_scenarios(ComparisonInput(**d))
    assert r['menor_costo_declarado']==['Alternativa'] and not r['tarifas_oficiales_validadas']


@pytest.mark.parametrize('change',['consumo','fecha','nombre','opcion','historicos'])
def test_tariff_comparison_rejects_different_basis(change):
    d=scenarios();b=d['escenarios'][1]
    if change=='consumo':b['cuenta']['periodo']['kwh']='101'
    if change=='fecha':b['cuenta']['periodo']['lectura_actual']='2026-11-29'
    if change=='nombre':b['nombre']='ACTUAL'
    if change=='opcion':b['opcion']='NO_EXISTE'
    if change=='historicos':
        from tests.test_demand3 import caso
        for s in d['escenarios']:
            s['opcion']='BT3';s['cuenta']['demanda3']=caso();s['cuenta']['adicionales']['demanda']['estado']='calculada'
        b['cuenta']['demanda3']['historico'][-1]['maxima_kw']='51'
    with pytest.raises(ValidationError):ComparisonInput(**d)


def test_saved_decomposition_is_exact_and_residual_is_explicit():
    a=case();b=case();b['periodo']['kwh']='150';b['periodo']['precios'][0]['electricidad_neta']='200'
    b['periodo']['precios'][0]['fijo_neto']='1000'
    r=compare_saved(SavedComparisonInput(anterior=a,actual=b))
    assert (r['anterior_total'],r['actual_total'])==(13785,38825)
    assert r['descomposicion']['efecto_consumo']==6595
    assert r['descomposicion']['efecto_precio_medio']==17850
    assert r['descomposicion']['otros_cargos_impuestos_y_redondeos']==595
    b['periodo']['lectura_actual']='2026-11-29'
    assert compare_saved(SavedComparisonInput(anterior=a,actual=b))['descomposicion'] is None
    b=case();b['periodo']['kwh']='0'
    assert compare_saved(SavedComparisonInput(anterior=a,actual=b))['descomposicion'] is None


def test_coverage_never_confuses_candidates_with_approved_models():
    r=validation_coverage(CoverageQuery(mes='2026-11'))
    assert r['total']==346 and r['comunas_con_candidatos']==113 and r['comunas_con_perfiles']==0
    assert r['total_perfiles_biblioteca']==0
    r=validation_coverage(CoverageQuery(mes='2026-11',cut='13118',empresa='ENEL',opcion='BT1'))
    assert len(r['comunas'])==1 and r['comunas'][0]['estado']=='sin_valores_en_lote'
    r=validation_coverage(CoverageQuery(mes='2026-08'))
    assert r['comunas_con_candidatos']==0


def test_workspace_routes_and_revision_transfer_preserve_privacy_controls():
    c=TestClient(app)
    for path in ['/','/cuenta','/comparar','/cobertura-validada?mes=2026-11']:
        assert c.get(path).status_code==200
    r=c.post('/api/evaluar-cuenta',json=enel_case('sobre_subtotal'))
    assert r.status_code==200 and r.json()['revision']['total_coincide_con_cargos_distintos']
    r=c.post('/api/comparar-tarifas',json=scenarios())
    assert r.status_code==200 and r.headers['cache-control']=='no-store'
    r=c.post('/api/comparar-guardados',json={'anterior':case(),'actual':case()})
    assert r.status_code==200 and r.headers['cache-control']=='no-store'
    r=c.post('/cuenta/desde-revision',data={'electricidad':'26300','total':'35123','kwh':'145','lectura_anterior':'2026-09-23','lectura_actual':'2026-10-21'})
    assert r.status_code==200 and 'value="26300"' in r.text and r.headers['cache-control']=='no-store'
    assert c.post('/cuenta/desde-revision',data={'electricidad':'NaN'}).status_code==422


def test_comparison_form_accepts_two_alternatives_without_inventing_a_third():
    form={'lectura_anterior':'2026-10-31','lectura_actual':'2026-11-30','kwh':'100'}
    for n in (1,2):
        for key,value in {'opcion':'BT3','energia':'100','transporte':'10','exento':'1','fijo':'500','demanda':'0','reactiva':'0','otros_afectos':'0','otros_exentos':'0','ajustes_finales':'0','respaldo':'Caso ficticio'}.items():form[f'{key}_{n}']=value
    r=TestClient(app).post('/comparar',data=form)
    assert r.status_code==200 and 'Escenario 3</th>' not in r.text
    form['energia_3']='1'
    assert TestClient(app).post('/comparar',data=form).status_code==422


def test_section_detection_preserves_both_sides_of_combined_headings():
    from scripts.build_validation_index import detected_options
    assert detected_options('Tarifa BT2 y BT3')=={'BT2','BT3'}
    assert detected_options('Tarifa AT2 y AT3')=={'AT2','AT3'}
    assert detected_options('Tarifa BT 4.1, 4.2, 4.3 (***)')=={'BT4.1','BT4.2','BT4.3'}
    assert detected_options('Tarifa TRAT2-TRAT3 (*)')=={'TRAT2','TRAT3'}


@pytest.mark.parametrize('kind',['punta','cargo_anterior'])
def test_comparison_keeps_peak_readings_and_past_money_on_same_basis(kind):
    d=scenarios()
    if kind=='punta':
        from tests.test_demand import caso
        for s in d['escenarios']:
            s['opcion']='BT4.3';s['cuenta']['demanda4']={'datos':caso(),'precio_punta_neto':'1000','precio_suministrada_o_contratada_neto':'2000','respaldo':'Ficticio'}
            s['cuenta']['adicionales']['demanda']['estado']='calculada'
        row=next(r for r in d['escenarios'][1]['cuenta']['demanda4']['datos']['historico'] if r['mes']=='2026-05')
        row['punta_kw']=79
    else:
        from tests.test_demand3 import caso
        for s in d['escenarios']:
            s['opcion']='BT3';s['cuenta']['demanda3']=caso();s['cuenta']['adicionales']['demanda']['estado']='calculada'
        d['escenarios'][1]['cuenta']['demanda3']['historico'][0]['cargo_demanda_neto']='999999'
    with pytest.raises(ValidationError):ComparisonInput(**d)
