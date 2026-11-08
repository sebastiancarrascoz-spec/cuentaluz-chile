"""Nómina oficial territorial y asociaciones documentadas en tabla 31 CNE.

Una asociación regulatoria no equivale a polígono de concesión ni a cálculo validado.
"""
import csv
import json
import re
from pathlib import Path
from collections import Counter
import pymupdf as fitz
import xlrd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/fuentes_nacionales"
records = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
territory = next(r for r in records if r["id"] == "subdere_comunas" and r["estado"] == "respaldado")
sheet = xlrd.open_workbook(ROOT / territory["archivo"]).sheet_by_index(0)
communes = {}
for i in range(1, sheet.nrows):
    region, region_name, abbreviation, province, province_name, cut, name = sheet.row_values(i)
    communes[str(cut).zfill(5)] = {"cut": str(cut).zfill(5), "nombre": name, "region_codigo": region,
        "region": region_name, "provincia": province_name, "concesionarias_cne": [],
        "estado_calculo": "pendiente", "fuente_territorial": territory["url"], "sha256_territorial": territory["sha256"]}
assert len(communes) == 346
source = next(r for r in records if "2026.06-ITD-PNP-julio" in r["url"] and r["estado"] == "respaldado")
doc = fitz.open(ROOT / source["archivo"])
pattern = re.compile(r"(?m)^(\d{1,2})\s*\n([^\n]+?)\s*\n(\d{4,5}|\*)\s*\n([\s\S]{1,65}?)\s*\n(STX\s+[A-Z]|SM)\s*\n([A-Z0-9a-z.]+)\s*\n((?:BT|AT)_[A-Z]{1,2})\s*\n(-?\d+,\d+)\s*\n(-?\d+,\d+)")
rows, anomalies = [], []
for page_no in range(103, 142):
    text = doc[page_no].get_text()
    for match in pattern.finditer(text):
        id, company, cut, name, system, tariff, network, residential, nonresidential = match.groups()
        row = {"id_cne": id, "empresa": company.strip(), "cut": cut.zfill(5) if cut != "*" else None,
            "comuna_documento": " ".join(name.split()), "sistema": system, "tarifa": tariff, "red": network,
            "fetr_residencial": residential, "fetr_no_residencial": nonresidential, "pagina": page_no + 1,
            "fuente": source["url"], "sha256": source["sha256"]}
        rows.append(row)
        if row["cut"]:
            if row["cut"] not in communes:
                anomalies.append(row)
            elif company.strip() not in communes[row["cut"]]["concesionarias_cne"]:
                communes[row["cut"]]["concesionarias_cne"].append(company.strip())
for commune in communes.values():
    commune["concesionarias_cne"].sort()
    commune["estado_asociacion"] = "documentada_tabla31" if commune["concesionarias_cne"] else "sin_asociacion_en_tabla31"
    commune["fuente_asociacion"] = source["url"] if commune["concesionarias_cne"] else None
result = {"fecha_revision": "2026-11-07", "alcance": "Nómina SUBDERE y asociaciones CNE PNP 2026-2, tabla 31; no identifica proveedor por domicilio ni aprueba tarifas.",
    "comunas": list(communes.values()), "resumen": {"comunas": len(communes),
        "con_asociacion_documentada": sum(bool(c["concesionarias_cne"]) for c in communes.values()),
        "sin_asociacion_tabla31": sum(not c["concesionarias_cne"] for c in communes.values()),
        "filas_regulatorias_extraidas": len(rows), "empresas_tabla31": sorted({r["empresa"] for r in rows}),
        "comunas_con_varias_empresas": sum(len(c["concesionarias_cne"]) > 1 for c in communes.values()), "calculos_validados": 0,
        "anomalias_cut": len(anomalies)}}
(ROOT / "config" / "cobertura_nacional.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "tabla31_extraida.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "anomalias_tabla31.json").write_text(json.dumps(anomalies, ensure_ascii=False, indent=2), encoding="utf-8")
with (OUT / "cobertura_346_comunas.csv").open("w", encoding="utf-8-sig", newline="") as f:
    fields = ["cut", "nombre", "region_codigo", "region", "provincia", "concesionarias_cne", "estado_asociacion", "estado_calculo", "fuente_asociacion"]
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", delimiter=";")
    writer.writeheader()
    writer.writerows({**c, "concesionarias_cne": " | ".join(c["concesionarias_cne"])} for c in communes.values())
print(json.dumps(result["resumen"], ensure_ascii=True, indent=2))
