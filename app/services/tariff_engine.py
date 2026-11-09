"""Motor decimal de componentes para perfiles documentados.

No deriva demanda facturable de kWh ni selecciona red, tramo o concesionaria.
Esas reglas deben validarse antes de aprobar cada perfil. Aún no se expone como
calculadora oficial: el catálogo nacional no tiene perfiles aprobados.
"""
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.services.invoice_service import peso


class DocumentedCharge(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    nombre: str = Field(min_length=1, max_length=120)
    cantidad: str = Field(pattern=r"^[a-z][a-z0-9_]{0,59}$")
    unidad: Literal["$/mes", "$/kWh", "$/kW/mes", "$/kVArh"]
    precio_neto: Decimal = Field(ge=0, le=1000000000)
    tratamiento: Literal["afecto", "exento"]
    pagina_o_celda: str = Field(min_length=1, max_length=100)


class QuantityRange(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    minimo: Decimal = Field(ge=0, le=1000000000000)
    maximo: Decimal = Field(ge=0, le=1000000000000)

    @model_validator(mode="after")
    def orden(self):
        if self.minimo > self.maximo:
            raise ValueError("Límite de cantidad invertido.")
        return self


class TariffProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str
    empresa: str
    cut: str = Field(pattern=r"^\d{5}$")
    sector: str
    red: str
    opcion: str
    condicion: str
    desde: date
    hasta: date
    fuente: str = Field(pattern=r"^https://")
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    estado: Literal["pendiente", "aprobado"] = "pendiente"
    revision_reglas: str | None = None
    casos_contrastados: list[str] = Field(default_factory=list)
    limites_cantidades: dict[str, QuantityRange] = Field(default_factory=dict)
    cargos: list[DocumentedCharge] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def fechas_y_aprobacion(self):
        if self.desde > self.hasta:
            raise ValueError("Intervalo de aplicación invertido.")
        if self.estado == "aprobado" and not (self.sha256 and self.revision_reglas and self.casos_contrastados):
            raise ValueError("La aprobación exige original con hash, revisión de reglas y casos contrastados.")
        if self.estado == "aprobado" and set(self.limites_cantidades) != {c.cantidad for c in self.cargos}:
            raise ValueError("La aprobación exige límites explícitos para todas las cantidades facturables.")
        return self


class SupplyContext(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    empresa: str
    cut: str = Field(pattern=r"^\d{5}$")
    sector: str
    red: str
    opcion: str
    condicion: str
    desde: date
    hasta: date


def calcular_componentes(perfil: TariffProfile, suministro: SupplyContext,
        cantidades: dict[str, Decimal], *, revision_interna=False):
    if perfil.estado != "aprobado" and not revision_interna:
        raise ValueError("Perfil pendiente de aprobación documental y numérica.")
    if not perfil.desde <= suministro.desde <= suministro.hasta <= perfil.hasta:
        raise ValueError("El período no está íntegramente cubierto. Divide el cálculo según las vigencias.")
    for campo in ("empresa", "cut", "sector", "red", "opcion", "condicion"):
        if getattr(perfil, campo) != getattr(suministro, campo):
            raise ValueError("El perfil no corresponde al suministro: " + campo)
    requeridas = {c.cantidad for c in perfil.cargos}
    if set(cantidades) != requeridas:
        raise ValueError("Se requieren exactamente estas cantidades facturables: " + ", ".join(sorted(requeridas)))
    values = {k: Decimal(str(v)) for k, v in cantidades.items()}
    if any(not v.is_finite() or v < 0 or v > Decimal("1e12") for v in values.values()):
        raise ValueError("Cantidades facturables no válidas.")
    for clave, limite in perfil.limites_cantidades.items():
        if clave not in values or not limite.minimo <= values[clave] <= limite.maximo:
            raise ValueError("Cantidad fuera de las condiciones del perfil: " + clave)
    componentes = []
    for cargo in perfil.cargos:
        importe = peso(cargo.precio_neto * values[cargo.cantidad])
        componentes.append({"nombre": cargo.nombre, "neto": importe,
            "cantidad": str(values[cargo.cantidad]), "precio_neto": str(cargo.precio_neto),
            "unidad": cargo.unidad, "tratamiento": cargo.tratamiento,
            "fuente": perfil.fuente, "sha256": perfil.sha256, "pagina_o_celda": cargo.pagina_o_celda})
    afecto = sum(c["neto"] for c in componentes if c["tratamiento"] == "afecto")
    exento = sum(c["neto"] for c in componentes if c["tratamiento"] == "exento")
    iva = peso(Decimal(afecto) * Decimal("0.19"))
    return {"perfil": perfil.id, "estado": perfil.estado, "componentes": componentes,
        "neto_afecto": afecto, "exento": exento, "iva": iva, "total": afecto + iva + exento,
        "alcance": "Importes de componentes netos. Las cantidades deben ser facturables y haber sido obtenidas con las reglas revisadas del perfil; no se infiere demanda ni elegibilidad."}
