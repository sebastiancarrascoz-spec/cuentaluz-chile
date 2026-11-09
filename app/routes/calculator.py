from pathlib import Path
import json
from datetime import date, timedelta
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from app.services.calculator_service import cargar_tarifas, cargar_aparatos
from app.services.estimate_service import EstimateInput, estimar
from app.services.invoice_service import InvoiceInput, conciliar
from app.services.demand_service import DemandInput, evaluar_demanda, month_index, month_name
from app.services.period_service import PeriodInput, evaluar_periodos
from app.services.demand3_service import Demand3Input, evaluar_demanda3
from app.services.account_service import AccountInput, CATEGORIES, Demand4Prices, evaluar_cuenta
from app.services.difference_service import LABELS as OBSERVED_LABELS

ROOT = Path(__file__).resolve().parents[2]
router = APIRouter()
templates = Jinja2Templates(directory=str(ROOT / "templates"))
templates.env.filters["clp"] = lambda v: "$" + f"{round(v):,}".replace(",", ".")


def contexto(request, **extra):
    return {"request": request, "vista_previa": os.getenv("VERCEL_ENV") == "preview" or os.getenv("APP_PREVIEW") == "1", "tarifas": {k: v for k, v in cargar_tarifas().items() if isinstance(v, dict) and "tarifas" in v},
        "aparatos": cargar_aparatos(), **extra}


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    valores = dict(request.query_params)
    valores.setdefault("fuente", "personalizada")
    return templates.TemplateResponse(request, "index.html", contexto(request, valores=valores))


@router.post("/api/estimar")
def api_estimar(entrada: EstimateInput):
    try:
        resultado = estimar(entrada)
        if catalogo_bloqueado(resultado):
            return JSONResponse({"detail": "El catálogo está pendiente de validación. Usa precios propios."}, status_code=503)
        return resultado
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)


def catalogo_bloqueado(resultado):
    return os.getenv("APP_ENV") == "production" and resultado["entrada"]["fuente"] == "referencia" and resultado["tarifa"]["estado"] != "validada"


@router.post("/calcular", response_class=HTMLResponse)
async def calcular(request: Request):
    form = await request.form(max_fields=100, max_files=0)
    valores = dict(form)
    try:
        if form.get("tarifa", "BT1") != "BT1":
            raise ValueError("BT2 está en revisión.")
        modo = form.get("modo", "kwh")
        if modo not in ("kwh", "aparatos"):
            raise ValueError("Selecciona un modo válido.")
        dias = int(form.get("dias", 30))
        kwh = form.get("kwh_directo", "")
        if modo == "aparatos":
            kwh = 0
            for id, aparato in cargar_aparatos().items():
                if form.get(f"aparato_{id}"):
                    horas = float(form.get(f"horas_{id}", aparato["horas_dia_default"]))
                    if not 0 <= horas <= 24:
                        raise ValueError("Las horas de uso deben estar entre 0 y 24.")
                    kwh += aparato["potencia_w"] / 1000 * horas * dias
        entrada = EstimateInput(kwh=kwh, distribuidora=form.get("distribuidora", "enel"), dias=dias,
            fuente=form.get("fuente", "referencia"), precio_kwh=form.get("precio_kwh") or None,
            cargo_fijo=form.get("cargo_fijo") or None, boleta_actual=form.get("boleta_actual") or None)
        resultado = estimar(entrada)
        if catalogo_bloqueado(resultado):
            return templates.TemplateResponse(request, "index.html", contexto(request, valores=valores,
                error="El catálogo está pendiente de validación documental. Selecciona «Ingresar mis propios precios» para construir tu escenario."), status_code=503)
        return templates.TemplateResponse(request, "resultados.html", contexto(request, resultado=resultado))
    except (ValidationError, ValueError, TypeError):
        return templates.TemplateResponse(request, "index.html", contexto(request, valores=valores,
            error="Revisa tus datos: consumo mayor que cero y hasta 10.000 kWh, días entre 1 y 62 y una distribuidora disponible. Si usas tus precios, completa ambos valores. Solo está habilitado BT1."), status_code=422)


@router.get("/comunas", response_class=HTMLResponse)
def comunas(request: Request):
    cobertura = json.loads((ROOT / "config/cobertura_nacional.json").read_text(encoding="utf-8"))
    return templates.TemplateResponse(request, "comunas.html", contexto(request, cobertura=cobertura))


@router.get("/fuentes", response_class=HTMLResponse)
def fuentes(request: Request):
    catalogo = json.loads((ROOT / "config/fuentes_nacionales.json").read_text(encoding="utf-8"))
    normalizacion = json.loads((ROOT / "config/normalizacion_saesa.json").read_text(encoding="utf-8"))
    return templates.TemplateResponse(request, "fuentes.html", contexto(request, catalogo=catalogo, normalizacion=normalizacion))


@router.post("/api/conciliar")
def api_conciliar(entrada: InvoiceInput):
    return conciliar(entrada)


@router.post("/api/evaluar-periodos")
def api_periodos(entrada: PeriodInput):
    return evaluar_periodos(entrada)


@router.post("/api/evaluar-cuenta")
def api_cuenta(entrada: AccountInput):
    try:
        return evaluar_cuenta(entrada)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)


@router.get("/cuenta", response_class=HTMLResponse)
def cuenta(request: Request):
    return templates.TemplateResponse(request, "periodos.html", contexto(request, valores={}, cuenta=True, observed_labels=OBSERVED_LABELS))


def demanda_desde_transferencia(form):
    kind, raw = form.get("tipo_demanda"), form.get("datos_demanda")
    if not kind and not raw:
        return None, None
    if kind == "3":
        data = Demand3Input.model_validate_json(raw)
        result = evaluar_demanda3(data)
        if result["resultado"] is None:
            raise ValueError("La demanda no tiene un importe único.")
        return data, {**result, "registros":[m.model_dump(mode="json") for m in data.historico]}
    if kind == "4":
        data = DemandInput.model_validate_json(raw)
        return data, {**evaluar_demanda(data), "registros":[m.model_dump(mode="json") for m in data.historico]}
    raise ValueError("Tipo de demanda no reconocido.")


@router.post("/cuenta/preparar-demanda", response_class=HTMLResponse)
async def preparar_demanda(request: Request):
    form = await request.form(max_fields=3, max_files=0)
    try:
        data, result = demanda_desde_transferencia(form)
        if data is None:
            raise ValueError("Faltan registros de demanda.")
        valores = {"tipo_demanda":form["tipo_demanda"], "datos_demanda":data.model_dump_json(),
            "demanda_estado":"calculada"}
        return templates.TemplateResponse(request, "periodos.html", contexto(request, valores=valores,
            cuenta=True, demanda_importada=result, observed_labels=OBSERVED_LABELS))
    except (ValidationError, ValueError, TypeError):
        return templates.TemplateResponse(request, "periodos.html", contexto(request, valores={}, cuenta=True, observed_labels=OBSERVED_LABELS,
            error="No se pudieron incorporar los registros. Vuelve a revisar la demanda antes de consolidar."), status_code=422)


@router.post("/cuenta", response_class=HTMLResponse)
async def cuenta_formulario(request: Request):
    form = await request.form(max_fields=60, max_files=0)
    valores = dict(form)
    imported = None
    try:
        demand, imported = demanda_desde_transferencia(form)
        priced4 = Demand4Prices(datos=demand, precio_punta_neto=form.get("precio_punta_neto"),
            precio_suministrada_o_contratada_neto=form.get("precio_suministrada_o_contratada_neto"),
            respaldo=form.get("demanda_respaldo")) if isinstance(demand, DemandInput) else None
        entrada = AccountInput(periodo=periodo_desde_formulario(form),
            respaldo_precios=form.get("respaldo_precios"),
            adicionales={key:{"estado":form.get(key + "_estado"),
                "importe":form.get(key + "_importe") or None,
                "respaldo":form.get(key + "_respaldo")} for key in CATEGORIES},
            demanda4=priced4, demanda3=demand if isinstance(demand, Demand3Input) else None,
            total_documento=int(form["total_documento"]) if form.get("total_documento") else None,
            observado={k:int(form['obs_'+k]) for k in OBSERVED_LABELS if form.get('obs_'+k)} or None)
        resultado = evaluar_cuenta(entrada)
        return templates.TemplateResponse(request, "periodos.html", contexto(request, valores=valores, cuenta=True,
            consolidada=resultado, demanda_importada=imported, observed_labels=OBSERVED_LABELS,
            cuenta_entrada=entrada.model_dump(mode="json")))
    except (ValidationError, ValueError, TypeError, OverflowError):
        return templates.TemplateResponse(request, "periodos.html", contexto(request, valores=valores, cuenta=True, demanda_importada=imported, observed_labels=OBSERVED_LABELS,
            error="Completa fechas, precios netos y respaldo. Declara cada categoría como importe conocido o no aplica con su motivo. Deja vacío el importe de no aplica; los ajustes finales son pesos enteros con signo. El total no puede resultar negativo."), status_code=422)


def periodo_desde_formulario(form):
    anterior = date.fromisoformat(form.get("lectura_anterior", ""))
    actual = date.fromisoformat(form.get("lectura_actual", ""))
    cambio = date.fromisoformat(form["cambio"]) if form.get("cambio") else None
    intervals = [(1,anterior + timedelta(days=1),cambio - timedelta(days=1)),(2,cambio,actual)] if cambio else [(1,anterior + timedelta(days=1),actual)]
    precios = [{"desde":desde, "hasta":hasta, **{k:form.get(f"{k}_{i}") or None for k in
        ("electricidad_neta", "transporte_neto", "servicio_exento", "fijo_neto")}} for i,desde,hasta in intervals]
    if not cambio and any(form.get(k + "_2") for k in ("electricidad_neta", "transporte_neto", "servicio_exento", "fijo_neto")):
        raise ValueError("Hay precios nuevos sin fecha de cambio.")
    return PeriodInput(lectura_anterior=anterior, lectura_actual=actual, kwh=form.get("kwh"), precios=precios,
        asignacion="dias", modo_fijo=form.get("modo_fijo"), redondeo=form.get("redondeo"),
        fijo_neto_periodo=form.get("fijo_neto_periodo") or None)


@router.get("/periodos", response_class=HTMLResponse)
def periodos(request: Request):
    return templates.TemplateResponse(request, "periodos.html", contexto(request, valores={}))


@router.post("/periodos", response_class=HTMLResponse)
async def periodos_formulario(request: Request):
    form = await request.form(max_fields=30, max_files=0)
    valores = dict(form)
    try:
        anterior = date.fromisoformat(form.get("lectura_anterior", ""))
        actual = date.fromisoformat(form.get("lectura_actual", ""))
        cambio = date.fromisoformat(form.get("cambio", ""))
        precios = []
        for i, desde, hasta in [(1,anterior + timedelta(days=1),cambio - timedelta(days=1)),(2,cambio,actual)]:
            precios.append({"desde":desde, "hasta":hasta, **{k:form.get(f"{k}_{i}") or None for k in
                ("electricidad_neta", "transporte_neto", "servicio_exento", "fijo_neto")}})
        entrada = PeriodInput(lectura_anterior=anterior, lectura_actual=actual, kwh=form.get("kwh"), precios=precios,
            asignacion="dias", modo_fijo=form.get("modo_fijo"), redondeo=form.get("redondeo"),
            fijo_neto_periodo=form.get("fijo_neto_periodo") or None)
        return templates.TemplateResponse(request, "periodos.html", contexto(request, valores=valores, temporal=evaluar_periodos(entrada)))
    except (ValidationError, ValueError, TypeError, OverflowError):
        return templates.TemplateResponse(request, "periodos.html", contexto(request, valores=valores,
            error="Revisa fechas y precios: el cambio debe dejar días a ambos lados, el intervalo debe tener entre 1 y 366 días y los precios deben ser netos no negativos. Completa el fijo total solo si eliges fijo declarado."), status_code=422)


@router.post("/api/evaluar-demanda")
def api_demanda(entrada: DemandInput):
    return evaluar_demanda(entrada)


@router.post("/api/evaluar-demanda-3")
def api_demanda3(entrada: Demand3Input):
    return evaluar_demanda3(entrada)


def contexto_demanda3(request, valores, **extra):
    mes = valores.get("mes_facturacion") or date.today().strftime("%Y-%m")
    last = month_index(mes)
    return contexto(request, valores=valores, mes=mes,
        meses=[month_name(i) for i in range(last - 12,last + 1)], **extra)


@router.get("/demanda-3", response_class=HTMLResponse)
def demanda3(request: Request):
    return templates.TemplateResponse(request, "demanda3.html", contexto_demanda3(request, {}))


@router.post("/demanda-3", response_class=HTMLResponse)
async def demanda3_formulario(request: Request):
    form = await request.form(max_fields=70, max_files=0)
    valores = dict(form)
    try:
        last = month_index(form.get("mes_facturacion"))
        months = [month_name(i) for i in range(last - 12,last + 1)]
        rows = [{"mes":m, "maxima_kw":form.get("max_" + m) or None,
            "contiene_horas_punta":form.get("calendario_" + m) == "on",
            "cargo_demanda_neto":form.get("cargo_" + m) or None} for m in months]
        entrada = Demand3Input(opcion=form.get("opcion"), mes_facturacion=form.get("mes_facturacion"),
            clasificacion=form.get("clasificacion"), precio_demanda_neto=form.get("precio_demanda_neto"),
            historico=rows, ventana_minimo_confirmada=form.get("ventana_minimo_confirmada") or None,
            cargo_observado_neto=form.get("cargo_observado_neto") or None)
        return templates.TemplateResponse(request, "demanda3.html", contexto_demanda3(request, valores,
            revision3=evaluar_demanda3(entrada), demanda_transferible=entrada.model_dump_json()))
    except (ValidationError, ValueError, TypeError, AttributeError):
        try:
            ctx = contexto_demanda3(request, valores)
        except (ValueError, TypeError, AttributeError):
            valores["mes_facturacion"] = date.today().strftime("%Y-%m")
            ctx = contexto_demanda3(request, valores)
        ctx["error"] = "Revisa opción, clasificación, precio y registros: completa doce cargos netos anteriores y los máximos de los doce meses que incluyen el facturado. Marca el calendario de punta aplicable; se necesitan al menos dos meses con punta. Un dato faltante no equivale a cero."
        return templates.TemplateResponse(request, "demanda3.html", ctx, status_code=422)


def contexto_demanda(request, valores, **extra):
    mes = valores.get("mes_facturacion") or date.today().strftime("%Y-%m")
    fin = month_index(mes)
    meses = [month_name(i) for i in range(fin - 11, fin + 1)]
    return contexto(request, valores=valores, meses=meses, mes=mes, **extra)


@router.get("/demanda", response_class=HTMLResponse)
def demanda(request: Request):
    valores = {"mes_facturacion": date.today().strftime("%Y-%m"), "opcion":"BT4.3"}
    return templates.TemplateResponse(request, "demanda.html", contexto_demanda(request, valores))


@router.post("/demanda", response_class=HTMLResponse)
async def demanda_formulario(request: Request):
    form = await request.form(max_fields=70, max_files=0)
    valores = dict(form)
    try:
        months = [month_name(i) for i in range(month_index(form.get("mes_facturacion")) - 11, month_index(form.get("mes_facturacion")) + 1)]
        rows = [{"mes":m, "maxima_kw":form.get("max_" + m),
            "punta_kw":form.get("punta_" + m) or None,
            "contiene_horas_punta":form.get("calendario_" + m) == "on"} for m in months]
        entrada = DemandInput(opcion=form.get("opcion"), mes_facturacion=form.get("mes_facturacion"),
            historico=rows, potencia_contratada_kw=form.get("potencia_contratada_kw") or None,
            meses_punta_anterior=[m.strip() for m in form.get("meses_punta_anterior", "").split(",") if m.strip()])
        return templates.TemplateResponse(request, "demanda.html", contexto_demanda(request, valores,
            demanda=evaluar_demanda(entrada), demanda_transferible=entrada.model_dump_json()))
    except (ValidationError, ValueError, TypeError, AttributeError):
        try:
            ctx = contexto_demanda(request, valores)
        except (ValueError, TypeError, AttributeError):
            valores["mes_facturacion"] = date.today().strftime("%Y-%m")
            ctx = contexto_demanda(request, valores)
        ctx["error"] = "Revisa los 12 meses, sus máximos y el calendario. Completa punta solo en meses con horas de punta y declara el período anterior completo si el mes facturado está fuera de punta. En 4.2 completa potencia contratada; en 4.3 déjala vacía."
        return templates.TemplateResponse(request, "demanda.html", ctx, status_code=422)


@router.get("/revisar", response_class=HTMLResponse)
def revisar(request: Request):
    return templates.TemplateResponse(request, "revisar.html", contexto_revision(request, valores={}))


def contexto_revision(request, **extra):
    comunas = json.loads((ROOT / "config/cobertura_nacional.json").read_text(encoding="utf-8"))["comunas"]
    return contexto(request, comunas_lector=[c["nombre"] for c in comunas], **extra)


@router.post("/cuenta/desde-revision", response_class=HTMLResponse)
async def cuenta_desde_revision(request: Request):
    form=await request.form(max_fields=15,max_files=0)
    valores={}
    try:
        for field in ("electricidad","transporte","administracion","exentos","neto_afecto","iva","total"):
            raw=form.get(field)
            if raw not in (None,""):
                amount=int(raw)
                if not 0<=amount<=1000000000000000:raise ValueError("Importe no válido.")
                valores['obs_'+field]=str(amount)
        if form.get('total'):valores['total_documento']=form['total']
        for key in ('lectura_anterior','lectura_actual'):
            if form.get(key):valores[key]=date.fromisoformat(form[key]).isoformat()
        if form.get('kwh'):
            from decimal import Decimal
            kwh=Decimal(form['kwh'])
            if not kwh.is_finite() or not 0<=kwh<=1000000000:raise ValueError('Consumo no válido.')
            valores['kwh']=str(kwh)
        return templates.TemplateResponse(request,'periodos.html',contexto(request,valores=valores,cuenta=True,observed_labels=OBSERVED_LABELS,
            mensaje_revision='Importes observados incorporados. Completa y verifica los precios del escenario; los importes de la factura no se convierten en precios ni validan red o ETR.'))
    except (ValueError,TypeError,ArithmeticError):
        return templates.TemplateResponse(request,'periodos.html',contexto(request,valores={},cuenta=True,observed_labels=OBSERVED_LABELS,error='No se pudieron incorporar los datos. Vuelve a revisar el documento.'),status_code=422)


@router.post("/revisar", response_class=HTMLResponse)
async def revisar_documento(request: Request):
    form = await request.form(max_fields=30, max_files=0)
    valores = dict(form)
    try:
        lineas = [{"nombre": nombre, "neto": form.get(campo) or "0", "tratamiento": tratamiento}
            for campo, nombre, tratamiento in [
                ("electricidad", "Electricidad consumida", "afecto"),
                ("transporte", "Transporte", "afecto"),
                ("administracion", "Administración del servicio", "afecto"),
                ("potencia", "Potencia y demanda", "afecto"),
                ("otros", "Otros cargos afectos", "afecto"),
                ("exentos", "Cargos exentos", "exento")]]
        resultado = conciliar(InvoiceInput(lineas=lineas, total_documento=form.get("total_documento"),
            ajustes_finales=form.get("ajustes_finales") or "0"))
        return templates.TemplateResponse(request, "revisar.html", contexto_revision(request, valores=valores, revision=resultado))
    except (ValidationError, ValueError, TypeError):
        return templates.TemplateResponse(request, "revisar.html", contexto_revision(request, valores=valores,
            error="Revisa los importes: usa valores netos positivos, total en pesos enteros y ajustes finales con su signo."), status_code=422)


@router.get("/metodologia", response_class=HTMLResponse)
def metodologia(request: Request):
    return templates.TemplateResponse(request, "metodologia.html", contexto(request))
