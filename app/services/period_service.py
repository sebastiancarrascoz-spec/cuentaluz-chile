"""Escenarios de precios declarados con reparto temporal y aritmética racional.

El reparto de energía por días se relaciona con 5T/2024, 5.1. La ponderación
del fijo y la política de redondeo son supuestos explícitos del escenario, no
reglas acreditadas de una distribuidora. No aprueba tarifas ni calcula FET.
"""
from datetime import date, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PeriodPrice(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    desde: date
    hasta: date
    electricidad_neta: Decimal = Field(ge=0, le=100000, decimal_places=6)
    transporte_neto: Decimal = Field(ge=0, le=100000, decimal_places=6)
    servicio_exento: Decimal = Field(ge=0, le=100000, decimal_places=6)
    fijo_neto: Decimal | None = Field(default=None, ge=0, le=1000000, decimal_places=6)
    kwh_medido: Decimal | None = Field(default=None, ge=0, le=1000000000, decimal_places=4)


class PeriodInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    lectura_anterior: date
    lectura_actual: date
    kwh: Decimal = Field(ge=0, le=1000000000, decimal_places=4)
    precios: list[PeriodPrice] = Field(min_length=1, max_length=24)
    asignacion: Literal["dias", "lecturas"]
    modo_fijo: Literal["ponderado", "declarado"]
    fijo_neto_periodo: Decimal | None = Field(default=None, ge=0, le=1000000, decimal_places=6)
    redondeo: Literal["por_cargo", "sobre_subtotal"]

    @model_validator(mode="after")
    def cobertura(self):
        if self.lectura_actual == date.max:
            raise ValueError("La fecha de lectura actual excede el límite del calendario admitido.")
        days = (self.lectura_actual - self.lectura_anterior).days
        if not 1 <= days <= 366:
            raise ValueError("El intervalo entre lecturas debe tener entre 1 y 366 días.")
        cursor = self.lectura_anterior + timedelta(days=1)
        for p in sorted(self.precios, key=lambda p: p.desde):
            if p.desde > p.hasta:
                raise ValueError("Intervalo de precios invertido.")
            start, end = max(p.desde, self.lectura_anterior + timedelta(days=1)), min(p.hasta, self.lectura_actual)
            if start > end:
                raise ValueError("Hay un intervalo de precios que no participa en el período.")
            if start != cursor:
                raise ValueError("Los precios deben cubrir todos los días sin huecos ni superposiciones.")
            cursor = end + timedelta(days=1)
        if cursor != self.lectura_actual + timedelta(days=1):
            raise ValueError("Faltan precios para el final del período.")
        if self.asignacion == "lecturas":
            if any(p.kwh_medido is None for p in self.precios):
                raise ValueError("Completa los consumos medidos de todos los intervalos.")
            if sum((p.kwh_medido for p in self.precios), Decimal(0)) != self.kwh:
                raise ValueError("Los consumos medidos no suman el consumo total.")
        elif any(p.kwh_medido is not None for p in self.precios):
            raise ValueError("El reparto por días no admite consumos medidos por intervalo.")
        if (self.modo_fijo == "declarado") != (self.fijo_neto_periodo is not None):
            raise ValueError("El fijo declarado exige su importe total; el fijo ponderado no admite ese importe adicional.")
        if self.modo_fijo == "ponderado" and any(p.fijo_neto is None for p in self.precios):
            raise ValueError("El fijo ponderado requiere un precio fijo en cada intervalo.")
        return self


def round_peso(value: Fraction):
    sign = -1 if value < 0 else 1
    v = abs(value)
    return sign * ((2 * v.numerator + v.denominator) // (2 * v.denominator))


def decimal_text(value: Fraction):
    with localcontext() as ctx:
        ctx.prec = 50
        return format(Decimal(value.numerator) / Decimal(value.denominator), ".6f")


def importes_periodo(entrada: PeriodInput):
    days = (entrada.lectura_actual - entrada.lectura_anterior).days
    sums = {k: Fraction(0) for k in ("electricidad", "transporte", "administracion", "exentos")}
    rows = []
    for p in sorted(entrada.precios, key=lambda p: p.desde):
        start, end = max(p.desde, entrada.lectura_anterior + timedelta(days=1)), min(p.hasta, entrada.lectura_actual)
        n = (end - start).days + 1
        energy = Fraction(p.kwh_medido) if entrada.asignacion == "lecturas" else Fraction(entrada.kwh) * Fraction(n, days)
        amounts = {"electricidad":energy * Fraction(p.electricidad_neta),
            "transporte":energy * Fraction(p.transporte_neto), "exentos":energy * Fraction(p.servicio_exento)}
        for key, value in amounts.items():
            sums[key] += value
        if entrada.modo_fijo == "ponderado":
            sums["administracion"] += Fraction(p.fijo_neto) * Fraction(n, days)
        rows.append({"desde":start.isoformat(), "hasta":end.isoformat(), "dias":n,
            "fraccion_dias":str(Fraction(n,days)), "kwh":decimal_text(energy), "kwh_fraccion":str(energy),
            "electricidad_sin_redondear":decimal_text(amounts["electricidad"]),
            "transporte_sin_redondear":decimal_text(amounts["transporte"]),
            "exentos_sin_redondear":decimal_text(amounts["exentos"])})
    if entrada.modo_fijo == "declarado":
        sums["administracion"] = Fraction(entrada.fijo_neto_periodo)
    return days, rows, sums


def evaluar_periodos(entrada: PeriodInput):
    days, rows, sums = importes_periodo(entrada)
    displayed = {k:round_peso(v) for k,v in sums.items()}
    affect = sums["electricidad"] + sums["transporte"] + sums["administracion"]
    rounded_lines = displayed["electricidad"] + displayed["transporte"] + displayed["administracion"]
    options = {}
    for method in ("por_cargo", "sobre_subtotal"):
        net = rounded_lines if method == "por_cargo" else round_peso(affect)
        iva = round_peso(Fraction(net * 19, 100))
        options[method] = {"neto_afecto":net, "iva":iva, "exentos":displayed["exentos"],
            "ajuste_redondeo":net - rounded_lines, "total":net + iva + displayed["exentos"]}
    return {"dias":days, "intervalos":rows, "asignacion":entrada.asignacion,
        "modo_fijo":entrada.modo_fijo, "redondeo":entrada.redondeo,
        "componentes_redondeados":displayed,
        "componentes_sin_redondear":{k:decimal_text(v) for k,v in sums.items()},
        "neto_afecto_fraccion":str(affect), "alternativas":options, **options[entrada.redondeo],
        "estado":"escenario_con_precios_declarados",
        "convencion_fechas":"Se excluye la lectura anterior y se incluye la actual. Las vigencias de precios incluyen ambos extremos.",
        "alcance":"No valida precios ni aplicabilidad. El reparto por días estima energía; no representa mediciones diarias. El fijo ponderado es un supuesto explícito, sin dividirlo por días del mes calendario ni duplicarlo por intervalo. El redondeo elegido requiere cotejo con la distribuidora. No calcula automáticamente FET, ETR, demanda, reactiva, subsidios ni saldos."}
