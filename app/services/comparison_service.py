"""Comparaciones reproducibles de escenarios declarados, sin recomendar tarifa."""
from fractions import Fraction
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.services.account_service import AccountInput, evaluar_cuenta
from app.services.period_service import importes_periodo, round_peso, decimal_text

OPTIONS=["BT1","BT2","BT3","BT4.1","BT4.2","BT4.3","BT5","BT6","AT2","AT3","AT4.1","AT4.2","AT4.3","AT5","AT6","TRBT","TRBT2","TRBT3","TRAT","TRAT1","TRAT2","TRAT3"]


class Scenario(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    nombre:str=Field(min_length=1,max_length=80)
    opcion:str=Field(min_length=2,max_length=12)
    aplicabilidad_declarada:bool
    respaldo_aplicabilidad:str=Field(min_length=1,max_length=240)
    cuenta:AccountInput

    @model_validator(mode="after")
    def option(self):
        if self.opcion not in OPTIONS:raise ValueError("Opción no incluida en esta comparación.")
        automatic=self.cuenta.demanda3 or (self.cuenta.demanda4.datos if self.cuenta.demanda4 else None)
        if automatic and automatic.opcion!=self.opcion:raise ValueError("La opción no coincide con los históricos de demanda.")
        return self


class ComparisonInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    escenarios:list[Scenario]=Field(min_length=2,max_length=6)

    @model_validator(mode="after")
    def same_basis(self):
        base=self.escenarios[0].cuenta.periodo
        names=[s.nombre.casefold() for s in self.escenarios]
        if len(set(names))!=len(names):raise ValueError("Usa nombres distintos para los escenarios.")
        measurements={};peaks={};past_charges={}
        for scenario in self.escenarios:
            p=scenario.cuenta.periodo
            if (p.lectura_anterior,p.lectura_actual,p.kwh,p.asignacion)!=(base.lectura_anterior,base.lectura_actual,base.kwh,base.asignacion):
                raise ValueError("Compara el mismo período, consumo y método de reparto.")
            if p.asignacion=="lecturas" and [(r.desde,r.hasta,r.kwh_medido) for r in sorted(p.precios,key=lambda r:r.desde)]!=[(r.desde,r.hasta,r.kwh_medido) for r in sorted(base.precios,key=lambda r:r.desde)]:
                raise ValueError("Las lecturas por intervalo deben ser iguales.")
            automatic=scenario.cuenta.demanda3 or (scenario.cuenta.demanda4.datos if scenario.cuenta.demanda4 else None)
            if automatic:
                for row in automatic.historico:
                    peak=getattr(row,'punta_kw',None)
                    if peak is not None:
                        if row.mes in peaks and peaks[row.mes]!=peak:raise ValueError("Los escenarios usan lecturas de punta distintas para el mismo mes.")
                        peaks[row.mes]=peak
                    charge=getattr(row,'cargo_demanda_neto',None)
                    if charge is not None:
                        if row.mes in past_charges and past_charges[row.mes]!=charge:raise ValueError("Los cargos históricos observados deben ser iguales en la comparación.")
                        past_charges[row.mes]=charge
                    # Solo la intersección de mediciones disponibles; los cargos
                    # históricos de BT3 no se confunden con máximos de potencia.
                    if row.maxima_kw is None:continue
                    values=(row.maxima_kw,row.contiene_horas_punta)
                    if row.mes in measurements and measurements[row.mes]!=values:raise ValueError("Los escenarios usan máximos o calendarios distintos para el mismo mes.")
                    measurements[row.mes]=values
        return self


def compare_scenarios(data:ComparisonInput):
    rows=[]
    for s in data.escenarios:
        result=evaluar_cuenta(s.cuenta)
        rows.append({"nombre":s.nombre,"opcion":s.opcion,"aplicabilidad_declarada":s.aplicabilidad_declarada,
            "respaldo_aplicabilidad":s.respaldo_aplicabilidad,"total":result["total"],"neto_afecto":result["neto_afecto"],
            "iva":result["iva"],"exentos":result["exentos"],"ajustes_finales":result["ajustes_finales"],
            "componentes":result["componentes"],"alcance":result["alcance"]})
    base=rows[0]["total"]
    for r in rows:r["diferencia_respecto_base"]=r["total"]-base
    complete=all(r["aplicabilidad_declarada"] for r in rows)
    lowest=min(r["total"] for r in rows) if complete else None
    return {"escenarios":rows,"todos_con_aplicabilidad_declarada":complete,
        "menor_costo_declarado":[r["nombre"] for r in rows if r["total"]==lowest] if complete else [],
        "tarifas_oficiales_validadas":False,"recomendacion_tarifaria":None,
        "alcance":"Comparación monetaria con los mismos kWh y período. Precios, cantidades, contrato y elegibilidad son declarados; incluso la menor alternativa no constituye recomendación de cambio ni oferta. Sin aplicabilidad declarada de todas las alternativas no se destaca un menor costo. Cambios de contrato, medición, reactiva y condiciones especiales requieren revisión independiente."}


class SavedComparisonInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    anterior:AccountInput
    actual:AccountInput


def compare_saved(data:SavedComparisonInput):
    a,b=data.anterior,data.actual
    ra,rb=evaluar_cuenta(a),evaluar_cuenta(b)
    da,_,sa=importes_periodo(a.periodo);db,_,sb=importes_periodo(b.periodo)
    ka,kb=Fraction(a.periodo.kwh),Fraction(b.periodo.kwh)
    same=(a.periodo.lectura_anterior,a.periodo.lectura_actual)==(b.periodo.lectura_anterior,b.periodo.lectura_actual)
    decomposition=None
    if same and ka>0 and kb>0 and a.periodo.asignacion==b.periodo.asignacion=="dias":
        pa=((sa['electricidad']+sa['transporte'])*Fraction(119,100)+sa['exentos'])/ka
        pb=((sb['electricidad']+sb['transporte'])*Fraction(119,100)+sb['exentos'])/kb
        consumption=round_peso((kb-ka)*pa)
        price=round_peso(kb*(pb-pa))
        decomposition={"efecto_consumo":consumption,"efecto_precio_medio":price,
            "otros_cargos_impuestos_y_redondeos":rb['total']-ra['total']-consumption-price,
            "metodo":"Primero cambia el consumo a precios medios del escenario anterior y después cambia el precio medio con el consumo actual. Energía y transporte se valorizan antes del redondeo con IVA teórico, más precio exento. El residual conserva fijo, demanda, demás cargos e impuestos/redondeos efectivos; no se presenta como ahorro garantizado."}
    return {"anterior_total":ra['total'],"actual_total":rb['total'],"diferencia_total":rb['total']-ra['total'],
        "anterior_kwh_dia":decimal_text(ka/da),"actual_kwh_dia":decimal_text(kb/db),
        "mismo_periodo":same,"descomposicion":decomposition,
        "alcance":"Comparación de escenarios guardados, sin acreditar facturas. Si cambian las fechas, hay lecturas por intervalo o consumo cero, no se atribuye la diferencia a precio y consumo. El cambio diario permite comparar duración; el total conserva los períodos originales."}
