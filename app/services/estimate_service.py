"""Estimación pública BT1. El catálogo heredado no acredita una revisión vigente."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.services.calculator_service import cargar_tarifas, calcular_boleta


class EstimateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    kwh: float = Field(gt=0, le=10000)
    distribuidora: Literal["enel", "cge", "chilquinta", "frontel"] = "enel"
    fuente: Literal["referencia", "personalizada"] = "referencia"
    precio_kwh: float | None = Field(default=None, gt=0, le=5000)
    cargo_fijo: float | None = Field(default=None, ge=0, le=100000)
    boleta_actual: float | None = Field(default=None, gt=0, le=10000000)
    dias: int = Field(default=30, ge=1, le=62)


def estado_tarifa(dist, metadata, hoy=None):
    hoy = hoy or date.today()
    inicio = dist.get("vigente_desde") or metadata.get("vigente_desde")
    fin = dist.get("vigente_hasta") or metadata.get("vigente_hasta")
    revisada = dist.get("revision_documental", {}).get("estado") == "aprobada"
    try:
        vigente = date.fromisoformat(inicio) <= hoy <= date.fromisoformat(fin)
    except (ValueError, TypeError):
        vigente = False
    return {"vigente": vigente, "revisada": revisada,
        "estado": "validada" if vigente and revisada else "referencia",
        "vigente_desde": inicio, "vigente_hasta": fin,
        "fuente": dist.get("fuente", "Catálogo histórico"),
        "url_fuente": dist.get("url_fuente", "https://www.cne.cl/tarificacion/electrica/"),
        "mensaje": "Tarifa revisada y dentro de su período de vigencia." if vigente and revisada else
            "Referencia histórica pendiente de validación. No representa una tarifa vigente confirmada."}


def estimar(entrada: EstimateInput):
    data = cargar_tarifas()
    dist = data[entrada.distribuidora]
    estado = estado_tarifa(dist, data.get("metadata", {}))
    if entrada.fuente == "personalizada" and (entrada.precio_kwh is None or entrada.cargo_fijo is None):
        raise ValueError("Completa el precio por kWh y el cargo fijo de tu escenario.")

    def calcular(kwh):
        if entrada.fuente == "personalizada":
            variable = kwh * entrada.precio_kwh
            return {"total": round(variable + entrada.cargo_fijo), "componentes": [
                {"nombre": "Consumo a tu precio", "valor": round(variable), "color": "#204e45"},
                {"nombre": "Cargo fijo informado", "valor": round(entrada.cargo_fijo), "color": "#bdcd8d"}]}
        r = calcular_boleta(kwh, entrada.distribuidora, "BT1")
        componentes = [{"nombre": nombre, "valor": valor, "color": color} for nombre, valor, color in [
            ("Energía", r["cargo_energia"], "#204e45"),
            ("Potencia y distribución", r["cargo_potencia"], "#7d9b72"),
            ("Transporte", r["cargo_transporte"], "#bdcd8d"),
            ("Cargo fijo", r["cargo_fijo"], "#d7b77b"),
            ("Servicio público y recargo", r["cargo_serv_publico"] + r["cargo_fet_recargo"], "#9895b9")]]
        ajuste = r["total"] - sum(c["valor"] for c in componentes)
        if ajuste:
            componentes.append({"nombre": "Ajuste de redondeo", "valor": ajuste, "color": "#aaaaaa"})
        return {"total": r["total"], "componentes": componentes}

    base = calcular(entrada.kwh)
    if entrada.fuente == "personalizada":
        ajuste = base["total"] - sum(c["valor"] for c in base["componentes"])
        if ajuste:
            base["componentes"].append({"nombre": "Ajuste de redondeo", "valor": ajuste, "color": "#aaaaaa"})
    for c in base["componentes"]:
        c["porcentaje"] = round(c["valor"] / base["total"] * 100, 1) if base["total"] else 0
    escenarios = []
    for porcentaje in (10, 20, 30):
        nuevo_kwh = entrada.kwh * (1 - porcentaje / 100)
        nuevo = calcular(nuevo_kwh)
        ahorro = base["total"] - nuevo["total"]
        escenarios.append({"reduccion": porcentaje, "kwh": round(nuevo_kwh, 1),
            "total": nuevo["total"], "ahorro": ahorro, "ahorro_12_periodos": ahorro * 12})
    return {**base, "entrada": entrada.model_dump(), "distribuidora": dist["nombre"],
        "fecha": date.today().isoformat(), "tarifa": estado, "escenarios": escenarios,
        "kwh_dia": round(entrada.kwh / entrada.dias, 2),
        "precio_efectivo": round(base["total"] / entrada.kwh, 2),
        "diferencia_boleta": round(entrada.boleta_actual - base["total"]) if entrada.boleta_actual else None,
        "metodologia": "Precio variable y cargo fijo finales, con impuestos incluidos, proporcionados por el usuario. No se agregan otros cargos." if entrada.fuente == "personalizada" else
            "Modelo BT1 heredado: cargo fijo, energía, potencia/distribución y transporte afectos a IVA; servicio público exento y recargo por tramos. Requiere validación documental por comuna y suministro."}
