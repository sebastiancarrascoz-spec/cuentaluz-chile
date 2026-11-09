from datetime import date
import pytest
from app.services.estimate_service import EstimateInput, estimar, estado_tarifa


def test_fecha_y_aprobacion_son_ambas_necesarias():
    metadata = {"vigente_desde": "2026-01-01", "vigente_hasta": "2026-12-31"}
    dist = {"datos_verificados": True}
    assert estado_tarifa(dist, metadata, date(2026, 6, 1))["estado"] == "referencia"
    dist["revision_documental"] = {"estado": "aprobada"}
    assert estado_tarifa(dist, metadata, date(2026, 6, 1))["estado"] == "validada"
    assert estado_tarifa(dist, metadata, date(2027, 1, 1))["estado"] == "referencia"
    assert estado_tarifa(dist, {}, date(2026, 6, 1))["estado"] == "referencia"


@pytest.mark.parametrize("kwh", [0.01, 150, 350, 350.01, 500, 1000, 5000, 10000])
@pytest.mark.parametrize("dist", ["enel", "cge", "chilquinta", "frontel"])
def test_desglose_reconcilia_y_ahorro_no_reduce_fijo(kwh, dist):
    r = estimar(EstimateInput(kwh=kwh, distribuidora=dist))
    assert sum(c["valor"] for c in r["componentes"]) == r["total"]
    assert 0 <= r["escenarios"][0]["ahorro"] <= r["escenarios"][1]["ahorro"] <= r["escenarios"][2]["ahorro"]
    assert r["tarifa"]["estado"] == "referencia"


def test_personalizado_redondeo_y_fijo_cero():
    r = estimar(EstimateInput(kwh=1.5, fuente="personalizada", precio_kwh=1, cargo_fijo=0.5))
    assert sum(c["valor"] for c in r["componentes"]) == r["total"] == 2
    assert estimar(EstimateInput(kwh=250, fuente="personalizada", precio_kwh=240, cargo_fijo=0))["total"] == 60000


def test_updater_guarda_candidato_sin_tocar_catalogo(tmp_path, monkeypatch):
    from services import updater
    active = tmp_path / "config" / "tarifas.json"
    active.parent.mkdir()
    active.write_text('{"original": true}', encoding="utf-8")
    monkeypatch.setattr(updater, "_ROOT", tmp_path)
    monkeypatch.setattr(updater, "_TARIFAS_PATH", active)
    updater._guardar_tarifas({"candidato": True})
    assert active.read_text() == '{"original": true}'
    assert (tmp_path / "data" / "revision" / "tarifas_candidatas.json").exists()
