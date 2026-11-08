# Normalización y actualización de fuentes nacionales

La biblioteca sigue conteniendo 362 documentos únicos. La normalización convierte parte de los respaldos existentes en datos candidatos; no agrega documentos ni aprueba modelos tarifarios.

## Primer lote

`python scripts/normalize_saesa_sources.py` comprueba SHA-256 de los originales indexados y procesa la primera hoja de publicación de 12 Excel de suministro regulado de Saesa, Frontel, Luz Osorno y Edelaysen. Publicaciones de septiembre, octubre y noviembre de 2026: 63.120 celdas de precio neto, 21.040 por mes.

El lector usa ZIP/XML sin ejecutar fórmulas ni convertir precios a float. Conserva el valor XML, formato, valor publicado a tres decimales, fórmula presente, hoja, celda, URL y hash. Solo admite el diseño y formato reconocidos; lo demás queda como incidencia. No sustituye celdas vacías por cero.

Los encabezados territoriales se comparan por nombre exacto tras normalizar mayúsculas, tildes y espacios. Hay correspondencia con 113 CUT. Aisén, Coihaique, Alto Bío Bío, S. Juan De La Costa y Sta. Bárbara permanecen sin equivalencia automática. No se usa proximidad geográfica ni el antiguo mapa de cuatro distribuidoras.

El archivo `artifacts/normalizacion/saesa-8a8e5693185f45bf.jsonl` tiene SHA-256 `8a8e5693185f45bf3a86f76fe019ccdac3726e45fb166b8e3fea6a12e6c0a859`. La matriz `artifacts/normalizacion/matriz-comunas-8a8e5693185f45bf.csv` incluye todas las 346 comunas: identifica las 233 sin valores normalizados de este lote y conserva aparte los encabezados sin CUT. La asociación de este lote no acredita cobertura tarifaria completa.

Hay 786 incidencias, incluidas filas agregadas sin importe. Las secciones combinadas, tramos ETR y alternativas se conservan como aparecen; no se expanden ni se suman todas las filas para simular una factura. En particular, «Transporte de Electricidad» es un agregado que puede contener servicio público exento: sumarlo junto al desglose duplicaría cargos y podría aplicar IVA incorrectamente. Todo tratamiento no expresamente exento queda pendiente, sin deducirlo automáticamente de la relación entre columnas neta/con IVA.

## Cotejo de muestra

Se leyó y renderizó la página 1 del PDF de Saesa de noviembre, cotejando la columna Ancud–Aéreo con `Pub. PDF`: D14 fijo 1.047,466; D15 agregado transporte 27,187; D16 servicio público 0,855; D17 transmisión 26,332; D19 energía 109,639; D20 compras de potencia 25,952; D21 distribución ETR 1 49,072. Son siete celdas cotejadas, no una revisión integral de 63.120 valores ni de elegibilidad.

Hash PDF: `a1a2b5bb2e1706add5309a1f9eccdc202873ed66afe9b354074fe0d9f3ca2dd0`. Hash Excel: `3052ab2a91a41e10e12cd21c9bd177ca1f9b86ec13cdaad16550beda053dc3cc`. Ambos provienen del ZIP oficial indexado en `config/fuentes_nacionales.json`. Evidencia local: `artifacts/saesa-noviembre-pagina1.png`. Falta cotejar notas, rangos, otras columnas y opciones, precisión de facturación y casos reales.

## Comparación controlada

```powershell
python scripts/review_tariff_changes.py artifacts/normalizacion/saesa-8a8e5693185f45bf.jsonl --anterior 2026-10 --nuevo 2026-11 --salida artifacts/normalizacion/cambios-octubre-noviembre.json
```

El informe existente conserva 13.626 precios modificados y 7.414 sin cambio. La clave de serie reúne empresa, hoja, territorio, sección, cargo y unidad; el período identifica cada publicación. Duplicados o ausencia de un período impiden la comparación. Cambios de nombre figuran como altas/bajas para revisión; no se inventan equivalencias. La salida no sobrescribe un informe existente ni modifica el catálogo web.

Antes de integrar: cotejar originales PDF, confirmar equivalencias y red, impuestos y unidades, vigencias, condiciones de aplicación, fórmulas y casos independientes por componente. La fecha final de vigencia permanece nula; no se presupone que cada publicación termina al finalizar su mes. Todos los candidatos y cero perfiles oficiales aprobados permanecen separados del cálculo público.
