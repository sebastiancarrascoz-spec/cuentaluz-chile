# CuentaLuz Chile — Verificación de la versión 2

Fecha: 7 de noviembre de 2026. Entorno de aplicación: Windows, Python 3.11, SQLite local. No corresponde a una certificación normativa ni a una prueba del hosting remoto.

## Ampliación nacional: resultados posteriores a la v2 inicial

Comprobación remota posterior: la ejecución https://github.com/sebastiancarrascoz-spec/cuentaluz-chile/actions/runs/42510260109 terminó aprobada para el commit `34822ea545a695b0e6e12c47a06ba9458a26efbb`, árbol idéntico al local `c31b2fe`. Pasaron pruebas, auditoría, construcción Docker, arranque, controles HTTP, respaldo/restauración con usuario del contenedor, reinicio y repetición de controles. Se conserva la distinción entre CI y hosting: dominio, HTTPS, volumen de destino, respaldo remoto y PostgreSQL siguen pendientes. Las referencias históricas a CI pendiente describen estados anteriores.

Actualización de cuenta consolidada y normalización del 8 de noviembre: **223 pruebas Python aprobadas, cinco omitidas; 10 pruebas JavaScript aprobadas**. Se verificaron impuestos conjuntos, créditos finales, faltantes, duplicación, precisión racional, demanda BT3 ambigua, mínimos monetarios y transferencia de históricos. El flujo completo desde demanda 4.3 produjo 358.885 y desde BT3 con mínimo declarado de 400.000 produjo 489.785, ambos con precios ficticios. Navegador 375/768/1280 para transferencias y 375/768/1280/1920 para cuenta manual, sin desbordes ni infracciones axe detectadas. Se conservaron formularios tras errores. Capturas e informes: `artifacts/account-browser.json`, `artifacts/demand-browser.json` y `artifacts/demand3-browser.json`.

Se inspeccionaron la captura de la cuenta consolidada y la página 1 del PDF Saesa noviembre; siete celdas de Ancud–Aéreo coinciden con la extracción del Excel. Este muestreo no valida todo el lote. La extracción completa conserva 63.120 candidatos y 786 incidencias. Se comprobaron lector XML, formatos, precios cero, celdas vacías, agregados, hash alterado y comparación en cuarentena. Los datos extensos y matriz permanecen fuera de Git.

Pasaron respaldo SQLite con WAL, conservación de versiones, restauración aislada, integridad y conteos. Se ejecutó el respaldo de la base activa y la sonda de salud local. El proceso real en modo producción pasó cuenta consolidada, `no-store`, rechazo de host, cierre de documentación API, límite 413 y catálogo 503. CI se amplió para contenedor y reinicio; su ejecución remota aún debe comprobarse. No hay validación de PostgreSQL, HTTPS ni hosting ni perfiles oficiales aprobados.

Actualización BT3/AT3 del 8 de noviembre: **196 pruebas Python aprobadas y cinco omitidas; 10 pruebas JavaScript aprobadas**. Las nuevas pruebas cubren memoria mensual, mínimo monetario, faltantes, clasificación declarada, ventanas con resultados distintos, comparación independiente del cargo actual y productos exactos cerca del medio peso. El navegador local pasó a 375/768/1280 sin desborde, errores JS ni infracciones axe en los estados auditados; se inspeccionó la captura móvil. Se volvió a probar 4.2/4.3 tras cambiar el script compartido de meses. Evidencia: `artifacts/demand3-browser.json` y `artifacts/demand-browser.json`. La ventana monetaria y la aplicabilidad a una concesionaria continúan pendientes; ver [DEMANDA_BT3_AT3.md](DEMANDA_BT3_AT3.md).

8 de noviembre de 2026: **179 pruebas Python aprobadas y cinco omitidas** tras incorporar escenarios temporales; las 10 pruebas JavaScript también pasan. Se verificaron huecos, superposiciones, fechas invertidas, años bisiestos, fracciones periódicas, consumos medidos que no suman el total y el cobro único del fijo. Dividir un precio idéntico no cambia el total. El navegador local pasó a 375/768/1280 sin desborde, errores JS ni infracciones axe detectadas (`artifacts/period-browser.json`); se inspeccionó la captura móvil. El diagnóstico temporal da 35.124 por cargo y 35.123 sobre subtotal. La diferencia de electricidad se conserva y documenta; no se considera una validación de precios ni de la factura. Ver [PRECISION_TEMPORAL.md](PRECISION_TEMPORAL.md).

Actualización de lectura PDF local: **165 pruebas Python aprobadas, cinco omitidas y 10 pruebas JavaScript aprobadas**. Se verificó la integridad del lector y su worker. El PDF privado existente se leyó en el navegador a 375/1280: detectó los importes, no modificó el formulario antes de confirmar y la conciliación posterior produjo 35.123. No hubo transmisión del PDF, solicitudes a terceros, errores JavaScript ni infracciones axe detectadas. Se inspeccionó la captura móvil y se comprobaron archivos inválidos, mayores a 6 MB y mayores a 12 páginas. Evidencia: `artifacts/invoice-import-browser.json`. Auditoría npm: cero vulnerabilidades conocidas detectadas. El smoke test local de producción conserva 503 para catálogo sin aprobar y 200 para precios propios. No se ha desplegado.

Actualización posterior: **164 pruebas pasan y cinco se omiten** tras agregar demandas BT/AT 4.2 y 4.3. Se verificaron máximos históricos, temporada de punta declarada, potencia contratada, cero frente a faltante, rechazo de NaN, cobertura mensual y flujo HTML/API. El navegador local comprobó formulario y resultados a 375/768/1280, sin desbordes ni infracciones axe detectadas (`artifacts/demand-browser.json`). Se inspeccionó la captura móvil. Los casos son ficticios y no certifican calendarios ni tarifas de una concesionaria.

- **150 pruebas pasan, cinco omitidas.** Incluyen conciliación anónima de factura por 35.123, rechazo de valores no finitos, directorio oficial, límites de perfiles, vigencias y demanda separada. Los cinco casos omitidos son del extractor legado de Enel: no se obtuvo su original requerido.
- **362 PDF/Excel únicos con SHA-256 verificado**, de los cuales 338 son PDF, 23 XLSX y uno XLS. Se excluyen de ese conteo ZIP, índices HTML y páginas de control. La cantidad no certifica cobertura de precios ni vigencia.
- El directorio incluye 346 CUT únicos y 16 regiones; 330 comunas tienen asociación documental y 16 siguen pendientes. La tabla CNE admite varias empresas en 117 comunas. Todos los estados de cálculo son pendientes.
- La conciliación aritmética devuelve exactamente 35.123. El perfil diagnóstico de octubre devuelve 35.124 y conserva la diferencia de un peso. No está aprobado ni validado para el período real que cruza septiembre/octubre.
- Navegador: flujos anteriores y nuevos de revisión, fuentes y cobertura a 375/768/1280/1920, sin desborde. El buscador identifica Punta Arenas con EDELMAG y no una de las cuatro distribuidoras del mapa antiguo. Se inspeccionaron capturas del formulario de revisión móvil y de la biblioteca de escritorio.
- Axe WCAG 2.1 A/AA: sin infracciones detectadas en inicio, resultados, cobertura, metodología, fuentes y revisión, a 375 y 1280. Persisten comprobaciones incompletas en decoraciones; no se afirma certificación de accesibilidad.
- Proceso local en modo producción: catálogo no aprobado bloqueado 503, precios propios 200, rechazo de host ajeno 400 y documentación API deshabilitada. Se mantiene sin publicar.
- Auditoría de todo el entorno, incluidas herramientas documentales: sin vulnerabilidades conocidas detectadas (`artifacts/auditoria-fuentes.json`). Las herramientas documentales no se añaden al runtime del contenedor.

Evidencia nueva: `national-browser.json`, capturas `revision-*`, `cobertura-nacional-*`, `fuentes-*`, `boleta-revision/diagnostico_anonimizado.json`, manifiestos y CSV de `fuentes_nacionales/`. Las brechas y fuentes están en [RESPALDOS_NACIONALES.md](RESPALDOS_NACIONALES.md).

## Registro histórico de la v2 inicial

La tabla y las limitaciones siguientes describen el primer rediseño, antes de la recopilación nacional. Los resultados anteriores prevalecen para esta actualización.

| Revisión | Resultado comprobado |
|---|---|
| Pruebas automatizadas | 137 correctas, 5 omitidas por ausencia del PDF de origen de Enel |
| Dependencias del entorno | `pip check`: sin incompatibilidades |
| Vulnerabilidades conocidas del entorno | Ninguna detectada después de actualizar pip y setuptools |
| Dependencias de producción fijadas | 20 paquetes; auditoría de `requirements.lock` sin vulnerabilidades conocidas |
| Navegador | Chromium con Playwright 1.57; inicio, resultados, cobertura y metodología |
| Tamaños comprobados | 375, 768, 1280 y 1920 px; sin desbordamiento horizontal en las páginas comprobadas |
| JavaScript | Sin errores de página en los recorridos automatizados; sintaxis verificada con Node |
| Recursos de terceros | Ninguna solicitud externa de la interfaz en los recorridos comprobados |
| Exportación | CSV descargado y leído como UTF-8 con BOM; incluye entradas, desglose, escenarios y alcance |
| Impresión | PDF A4 de ejemplo, una página; render revisado visualmente con fuente y limitaciones incluidas |
| Accesibilidad automática | axe-core, reglas WCAG 2.1 A/AA: sin infracciones detectadas en cuatro páginas a 375 y 1280 px |
| Modo producción | Proceso local separado: cálculo con precios propios 200, catálogo sin aprobar 503, host no autorizado 400, documentación API 404 |
| Integridad del catálogo recuperado | `config/tarifas.json` conserva el contenido del commit original |

## Casos funcionales

- Precios propios: 250 kWh × $240/kWh + $750 = $60.750. Boleta ingresada de $65.000: diferencia de $4.250. Reducción del 20 %: $48.750, ahorro de $12.000, conservando el cargo fijo.
- Aparatos: TV de referencia de 100 W, 5 horas/día y 10 días = 5 kWh. Se comprobó tanto el contador del navegador como el resultado del servidor.
- Desglose y total: reconciliación de redondeos, consumos próximos a umbrales y escenarios de reducción para las cuatro empresas del catálogo.
- Entradas: rechazo de negativos, valores no finitos, consumos fuera de rango, días inválidos, empresas desconocidas, BT2 y cuerpos superiores a 32 KiB. No se cambia silenciosamente a Enel ante una empresa inválida.
- Publicación tarifaria: la escritura del actualizador prepara un candidato y no modifica el catálogo activo.

## Revisión visual y accesibilidad

Se revisaron las capturas de inicio y resultados en escritorio y móvil. La auditoría detectó inicialmente contraste insuficiente en textos secundarios, nombre accesible del logo y regiones desplazables sin foco; se corrigieron y se repitió la comprobación. Se añadieron foco visible, enlace para saltar al contenido, etiquetas, regiones de estado y navegación por teclado.

La herramienta dejó comprobaciones de contraste incompletas en elementos decorativos del logo y la ilustración, y en símbolos informativos. Se inspeccionaron visualmente; no se afirma conformidad WCAG completa. Quedan pendientes pruebas con lectores de pantalla, personas usuarias y navegadores Safari/Firefox.

## Límites de la evidencia

- Las pruebas numéricas del catálogo contrastan su aritmética y regresiones, no la validez normativa de los importes. El catálogo histórico sigue pendiente de revisión documental y territorial.
- No se ejecutaron los cinco casos de extracción de PDF de Enel por faltar el documento de origen. No se descargaron ni publicaron tarifas nuevas.
- No se probó PostgreSQL ni la imagen Docker: no hay motor Docker instalado en este equipo. La CI queda preparada para construirla una vez que se suba la rama.
- No se verificaron dominio, TLS, límites del proveedor, volumen remoto ni recuperación de respaldos en producción. No se publicó la nueva versión.
- No se ejecutaron scrapers de red, suscripciones, mensajes ni envíos de correo.

## Evidencia local

La carpeta `artifacts/`, excluida de Git, contiene capturas anteriores y nuevas, PDF y CSV de ejemplo, `browser-verification.json`, `accessibility.json`, `production-smoke.json`, `auditoria-dependencias.json` y `auditoria-runtime.json`.

Reproducción y despliegue: [README.md](README.md) y [PRODUCCION.md](PRODUCCION.md).
