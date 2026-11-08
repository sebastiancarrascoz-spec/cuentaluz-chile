"""Cuenta consolidada con datos declarados; no selecciona tarifas oficiales.

Conserva fracciones hasta el redondeo final. Las categorías adicionales se
declaran expresamente; una ausencia nunca se interpreta como importe cero.
"""
from decimal import Decimal
from fractions import Fraction
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.services.period_service import PeriodInput, importes_periodo, round_peso, decimal_text
from app.services.demand_service import DemandInput, evaluar_demanda
from app.services.demand3_service import Demand3Input, evaluar_demanda3

CATEGORIES = ("demanda", "reactiva", "otros_afectos", "otros_exentos", "ajustes_finales")


class AdditionalAmount(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)
    estado: Literal["no_aplica", "declarado", "calculada"]
    importe: Decimal | None = Field(default=None, ge=-1000000000000, le=1000000000000, decimal_places=6)
    respaldo: str = Field(min_length=1, max_length=240)

    @model_validator(mode="after")
    def explicit_amount(self):
        if (self.estado == "declarado") != (self.importe is not None):
            raise ValueError("Un cargo declarado exige importe; no aplica exige dejarlo vacío.")
        return self


class Demand4Prices(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)
    datos: DemandInput
    precio_punta_neto: Decimal = Field(ge=0, le=1000000000, decimal_places=6)
    precio_suministrada_o_contratada_neto: Decimal = Field(ge=0, le=1000000000, decimal_places=6)
    respaldo: str = Field(min_length=1, max_length=240)


class AccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)
    periodo: PeriodInput
    respaldo_precios: str = Field(min_length=1, max_length=240)
    adicionales: dict[str, AdditionalAmount]
    demanda4: Demand4Prices | None = None
    demanda3: Demand3Input | None = None
    total_documento: int | None = Field(default=None, ge=0, le=1000000000000000, strict=True)

    @model_validator(mode="after")
    def completeness(self):
        if set(self.adicionales) != set(CATEGORIES):
            raise ValueError("Declara expresamente demanda, reactiva, otros afectos, otros exentos y ajustes finales.")
        for key, amount in self.adicionales.items():
            if amount.estado == "calculada" and key != "demanda":
                raise ValueError("Solo la demanda admite cálculo desde históricos en esta versión.")
            if key != "ajustes_finales" and amount.importe is not None and amount.importe < 0:
                raise ValueError("Los créditos o descuentos se declaran aparte como ajustes finales.")
            if key == "ajustes_finales" and amount.importe is not None and amount.importe != int(amount.importe):
                raise ValueError("Los ajustes finales deben estar expresados en pesos enteros.")
        if self.demanda3 and self.demanda4:
            raise ValueError("Solo se admite un método de demanda por cuenta.")
        automatic = self.demanda3 or (self.demanda4.datos if self.demanda4 else None)
        if automatic:
            if self.adicionales["demanda"].estado != "calculada":
                raise ValueError("No dupliques demanda calculada con un importe manual.")
            if automatic.mes_facturacion != self.periodo.lectura_actual.strftime("%Y-%m"):
                raise ValueError("El mes de demanda debe coincidir con el mes de lectura actual del escenario.")
        elif self.adicionales["demanda"].estado == "calculada":
            raise ValueError("Faltan los datos para calcular la demanda.")
        return self


def evaluar_cuenta(entrada: AccountInput):
    days, intervals, sums = importes_periodo(entrada.periodo)
    rows = [{"id":key, "nombre":name, "importe":sums[key], "tratamiento":tax,
        "respaldo":entrada.respaldo_precios, "origen":"precios_del_periodo"}
        for key, name, tax in [("electricidad","Electricidad consumida","afecto"),
            ("transporte","Transporte","afecto"), ("administracion","Administración","afecto"),
            ("exentos","Servicio público y recargos incluidos en el precio exento","exento")]]
    demand = None
    if entrada.demanda4:
        p = entrada.demanda4
        demand = evaluar_demanda(p.datos)
        quantities = demand["cantidades"]
        key = "potencia_contratada_kw" if p.datos.opcion.endswith("4.2") else "demanda_facturable_suministrada_kw"
        for id, name, quantity, price in [
            ("demanda_punta","Demanda en punta",quantities["demanda_facturable_punta_kw"],p.precio_punta_neto),
            ("demanda_base","Demanda suministrada o potencia contratada",quantities[key],p.precio_suministrada_o_contratada_neto)]:
            rows.append({"id":id,"nombre":name,"importe":Fraction(quantity)*Fraction(price),
                "tratamiento":"afecto","respaldo":p.respaldo,"origen":"historicos_declarados",
                "cantidad":quantity,"precio_neto":str(price),"unidad":"$/kW/mes"})
    if entrada.demanda3:
        demand = evaluar_demanda3(entrada.demanda3)
        if demand["resultado"] is None:
            raise ValueError("La demanda BT3/AT3 no tiene un importe único; resuelve la ventana monetaria antes de consolidar.")
        rows.append({"id":"demanda_base","nombre":"Demanda con mínimo monetario",
            "importe":Fraction(demand["resultado"]["cargo_demanda_neto_sin_redondear"]),
            "tratamiento":"afecto","respaldo":entrada.adicionales["demanda"].respaldo,
            "origen":"historicos_y_precio_declarados"})
    names = {"demanda":"Demanda declarada", "reactiva":"Energía reactiva o recargo declarado",
        "otros_afectos":"Otros cargos afectos", "otros_exentos":"Otros cargos exentos",
        "ajustes_finales":"Ajustes finales después del impuesto"}
    for key in CATEGORIES:
        amount = entrada.adicionales[key]
        if amount.estado == "declarado":
            rows.append({"id":key,"nombre":names[key],"importe":Fraction(amount.importe),
                "tratamiento":"final" if key == "ajustes_finales" else "exento" if key == "otros_exentos" else "afecto",
                "respaldo":amount.respaldo,"origen":"importe_declarado"})
    rounded_affect = sum(round_peso(r["importe"]) for r in rows if r["tratamiento"] == "afecto")
    raw_affect = sum((r["importe"] for r in rows if r["tratamiento"] == "afecto"), Fraction())
    # La política se aplica a todos los cargos, incluida demanda; nunca se
    # vuelve a agregar el IVA calculado por un módulo parcial.
    net = rounded_affect if entrada.periodo.redondeo == "por_cargo" else round_peso(raw_affect)
    raw_exempt = sum((r["importe"] for r in rows if r["tratamiento"] == "exento"), Fraction())
    exempt = sum(round_peso(r["importe"]) for r in rows if r["tratamiento"] == "exento") if entrada.periodo.redondeo == "por_cargo" else round_peso(raw_exempt)
    finals = sum(round_peso(r["importe"]) for r in rows if r["tratamiento"] == "final")
    iva = round_peso(Fraction(net*19,100))
    total = net + iva + exempt + finals
    if total < 0:
        raise ValueError("Los ajustes producen un total negativo; revisa su alcance y signo.")
    for r in rows:
        amount = r.pop("importe")
        r.update(neto=round_peso(amount), sin_redondear=decimal_text(amount), fraccion=str(amount))
    return {"estado":"escenario_con_datos_declarados", "tarifa_oficial_validada":False,
        "dias":days,"intervalos":intervals,"componentes":rows,"demanda":demand,
        "neto_afecto":net,"iva":iva,"exentos":exempt,"ajustes_finales":finals,
        "ajuste_redondeo_afecto":net-rounded_affect,
        "ajuste_redondeo_exento":exempt-sum(r["neto"] for r in rows if r["tratamiento"]=="exento"),
        "total":total,"total_documento":entrada.total_documento,
        "diferencia":entrada.total_documento-total if entrada.total_documento is not None else None,
        "declaraciones":{k:v.model_dump(mode="json") for k,v in entrada.adicionales.items()},
        "alcance":"Cuenta consolidada con precios, aplicabilidad e importes declarados. La electricidad debe incluir todos sus componentes netos. No selecciona pliegos oficiales, FET, ETR, reactiva ni subsidios automáticamente. Los ajustes finales se añaden después del IVA y no representan descuentos sobre la base imponible. Una coincidencia del total no valida la tarifa. El mes de demanda se vincula por convención al mes de lectura actual."}
