from datetime import date, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError
from app.routes.calculator import contexto, templates
from app.services.comparison_service import ComparisonInput, SavedComparisonInput, OPTIONS, compare_scenarios, compare_saved
from app.services.coverage_service import CoverageQuery, validation_coverage
router=APIRouter()


@router.post('/api/comparar-tarifas')
def api_compare(data:ComparisonInput):
    try:return compare_scenarios(data)
    except ValueError as e:return JSONResponse({'detail':str(e)},status_code=422)


@router.post('/api/comparar-guardados')
def api_saved_compare(data:SavedComparisonInput):
    try:return compare_saved(data)
    except ValueError as e:return JSONResponse({'detail':str(e)},status_code=422)


@router.get('/comparar',response_class=HTMLResponse)
def comparison(request:Request):
    return templates.TemplateResponse(request,'comparar.html',contexto(request,valores={},opciones=OPTIONS))


@router.post('/comparar',response_class=HTMLResponse)
async def comparison_form(request:Request):
    form=await request.form(max_fields=65,max_files=0);values=dict(form)
    try:
        old=date.fromisoformat(form.get('lectura_anterior',''));new=date.fromisoformat(form.get('lectura_actual',''))
        scenarios=[]
        for n in (1,2,3):
            if n==3 and not any(value for key,value in form.items() if key.endswith('_3')):continue
            source=form.get(f'respaldo_{n}')
            def value(key):return form.get(f'{key}_{n}')
            additional={k:{'estado':'declarado','importe':value(k),'respaldo':source} for k in ('demanda','reactiva','otros_afectos','otros_exentos','ajustes_finales')}
            scenarios.append({'nombre':'Escenario '+str(n),'opcion':value('opcion'),
                'aplicabilidad_declarada':value('aplicabilidad')=='on','respaldo_aplicabilidad':source,
                'cuenta':{'respaldo_precios':source,'adicionales':additional,'periodo':{
                    'lectura_anterior':old,'lectura_actual':new,'kwh':form.get('kwh'),'asignacion':'dias','modo_fijo':'declarado',
                    'fijo_neto_periodo':value('fijo'),'redondeo':'por_cargo','precios':[{'desde':old+timedelta(days=1),'hasta':new,
                        'electricidad_neta':value('energia'),'transporte_neto':value('transporte'),'servicio_exento':value('exento')} ]}}})
        result=compare_scenarios(ComparisonInput(escenarios=scenarios))
        return templates.TemplateResponse(request,'comparar.html',contexto(request,valores=values,opciones=OPTIONS,comparacion=result))
    except (ValueError,ValidationError,TypeError,OverflowError):
        return templates.TemplateResponse(request,'comparar.html',contexto(request,valores=values,opciones=OPTIONS,
            error='Revisa fechas, consumo, opción y todos los precios/importes netos. Declara cero solo cuando conozcas que el cargo es cero; no reemplaces un dato faltante. Los ajustes finales son pesos enteros.'),status_code=422)


@router.get('/cobertura-validada',response_class=HTMLResponse)
def coverage(request:Request,cut:str='',empresa:str='',opcion:str='',mes:str=''):
    values={'cut':cut,'empresa':empresa,'opcion':opcion,'mes':mes or date.today().strftime('%Y-%m')}
    try:
        q=CoverageQuery(**{k:v or None for k,v in values.items()})
        result=validation_coverage(q)
        return templates.TemplateResponse(request,'cobertura_validada.html',contexto(request,valores=values,opciones=OPTIONS,cobertura=result))
    except (ValidationError,ValueError):
        return templates.TemplateResponse(request,'cobertura_validada.html',contexto(request,valores=values,opciones=OPTIONS,error='Usa un CUT de cinco dígitos y un mes válido.'),status_code=422)
