# CuentaLuz Chile: respaldo nacional y precisión

Revisión del 7 de noviembre de 2026. Alcance solicitado: todas las comunas y opciones tarifarias, incluidas comerciales e industriales. **La recopilación avanzó; la cobertura tarifaria nacional completa todavía no está acreditada.** No hay perfiles nacionales aprobados para producción.

Avance BT3/AT3 del 8 de noviembre: [DEMANDA_BT3_AT3.md](DEMANDA_BT3_AT3.md) documenta la revisión del cargo de demanda neto, su memoria en máximos mensuales y su mínimo histórico monetario. Se conserva el punto pendiente de la ventana del mínimo y se evita devolver un cargo único cuando esa diferencia cambia el resultado sin confirmación declarada. Son evaluaciones con precio e históricos propios; siguen sin aprobarse perfiles nacionales.

Actualización del 8 de noviembre: [PRECISION_TEMPORAL.md](PRECISION_TEMPORAL.md) documenta el contraste septiembre/octubre y el nuevo escenario `/periodos`. Ponderar el fijo y redondear sobre el subtotal produce el total del caso de prueba, pero queda una diferencia de un peso en la electricidad redondeada. No se promovió una política de redondeo ni una tarifa por esa coincidencia. Se mantienen 362 originales PDF/Excel únicos y cero perfiles nacionales aprobados; las descargas directas de Enel de septiembre y noviembre quedaron registradas como fallidas.

Actualización posterior: `/revisar` permite seleccionar una factura PDF para leerla dentro del navegador, sin enviar el archivo ni su texto completo al servidor. Se proponen importes y páginas y se exige confirmación antes de reemplazar los campos manuales. La lectura probada con el documento existente reconstruye 35.123 al confirmar los importes; no valida sus precios ni amplía la cobertura documental nacional. Los límites son 6 MB, 12 páginas, texto seleccionable y 12 segundos. Sin OCR y con reconocimiento parcial de formatos. Ante ambigüedades, cargos faltantes o diferencias de conciliación, se mantiene la revisión manual. Esta actualización sustituye la limitación anterior de ausencia de lectura PDF; sigue sin existir carga del archivo al servidor.

## Qué está respaldado

Se verificaron por SHA-256 **362 documentos únicos: 338 PDF, 23 XLSX y un XLS**. Incluyen pliegos de suministro, peajes, servicios asociados, inyección, documentos regulatorios y la nómina territorial. Este número no equivale a 362 tarifas ni a 362 pliegos vigentes. Los ZIP contenedores y las páginas de índices no se cuentan como documentos adicionales.

Los originales públicos están en `artifacts/fuentes_nacionales/`. Cada descarga conserva URL, fecha de consulta UTC, estado HTTP, tamaño y hash en `manifest.json`. Los miembros de ZIP conservan también el hash y URL del contenedor en `miembros_zip.json`. `indice_documental.csv` permite revisar las fuentes sin depender de la interfaz. El código y el catálogo de metadatos están versionados; los originales descargados se conservan localmente fuera de Git.

| Fuente o proveedor del archivo | Documentos únicos |
|---|---:|
| CEC | 18 |
| Chilquinta | 1 |
| CNE | 31 |
| Codiner | 2 |
| Coelcha | 65 |
| Coopelan | 30 |
| Cooprel | 10 |
| Copelec | 38 |
| CRELL | 22 |
| EDECSA | 1 |
| Edelaysen | 6 |
| EEPA | 1 |
| EMELCA | 1 |
| Enel Colina | 33 |
| Frontel | 10 |
| Grupo Saesa: otros archivos y sistemas aislados | 37 |
| Litoral | 1 |
| Luz Osorno | 10 |
| Mataquito | 2 |
| Saesa | 10 |
| SEC | 7 |
| SUBDERE | 1 |
| Tiltil | 25 |

Las cantidades agrupan por proveedor del archivo y deduplican por contenido. No demuestran cobertura de todos sus meses, localidades u opciones. Se recopilaron documentos disponibles de 2026, con prioridad en septiembre, octubre y noviembre. Chilquinta y Litoral corresponden al pliego de octubre; EMELCA es una publicación legal de marzo, Mataquito de enero y EDECSA corresponde solo a peajes. Los documentos regulatorios de años anteriores se preservan cuando son antecedentes del período investigado. No se declara un histórico nacional completo.

## Cobertura territorial real

La nómina de [SUBDERE](https://www.subdere.gov.cl/sites/default/files/documentos/CUT_2018_v04.xls) contiene 346 comunas y 16 regiones. La [tabla 31 del informe CNE PNP julio de 2026](https://www.cne.cl/wp-content/uploads/2026/06/2026.06-ITD-PNP-julio-2026.pdf), páginas 104 a 142, permitió extraer 3.215 filas con dos factores ETR y asociar 330 comunas. Hay 117 comunas con varias denominaciones de empresas. Las denominaciones regulatorias pueden incluir nombres históricos; no se presentan como 33 empresas independientes actualmente activas.

La extracción no incorpora la sección suplementaria de una sola columna de factores al final de la tabla. No debe utilizarse como una extracción íntegra y validada de todos los factores para cálculo. No se encontraron códigos CUT ajenos a la nómina en las filas extraídas. Falta cotejo independiente de las celdas antes de utilizar sus valores en el motor.

Quedan sin asociación en esta extracción: Camiña, Ollagüe, San Pedro de Atacama, María Elena, Juan Fernández, Isla de Pascua, Guaitecas, O'Higgins, Tortel, Laguna Blanca, Río Verde, San Gregorio, Antártica, Primavera, Timaukel y General Lagos. Se requieren fuentes específicas de concesiones, sistemas aislados y prestadores. No significa ausencia de suministro.

`config/cobertura_nacional.json` y `cobertura_346_comunas.csv` contienen el CUT, región, provincia, asociaciones y fuentes. Todos los estados de cálculo permanecen pendientes. La página `/comunas` usa este directorio, sustituyendo el mapa legado de cuatro distribuidoras. No permite identificar una concesionaria por dirección.

## Brechas documentales que siguen abiertas

- **Enel Distribución:** el PDF oficial de octubre puede consultarse mediante la herramienta web, pero su descarga local entrega control de acceso. No se cuenta como original respaldado. Falta el original verificable y el pliego de septiembre para revisar el período que cruza ambos meses. Enel Colina tiene documentos separados y no sustituye a Enel Distribución.
- **CGE:** el portal y el PDF identificado de octubre respondieron HTTP 403. No se importaron precios de terceros. Las denominaciones históricas relacionadas de la tabla CNE necesitan conciliación documental antes de asignar un pliego común.
- **Edelmag y SASIPA:** no se logró el respaldo local del contenido tarifario consultado; sus portales responden con restricciones. Requieren documentos originales y modelos propios de sus sistemas.
- **Luzlinares y Luzparral:** no se obtuvo un pliego de suministro validable desde los portales consultados. En Luzparral hubo un error de certificado TLS; no se desactivó la verificación. El índice de Luzlinares entregó una aplicación con control de acceso y sin enlaces documentales utilizables en la respuesta.
- **Socoepa:** el índice mostraba un PDF de peajes; el filtro de noviembre no entregó enlaces de pliegos utilizables. Falta respaldo del suministro del período.
- **Coopersol, DESA, Luz Andes, EEC y otras denominaciones sin correspondencia directa en el catálogo:** resolver nombre legal, sucesión o marca y su fuente aplicable. No se asigna el precio de otra empresa por similitud de nombre.
- **EMELCA, Mataquito, EDECSA y restantes empresas con archivos parciales:** completar suministro, períodos y opciones faltantes. Tener un documento de servicios o peajes no resuelve el suministro.

Los fallos de descarga quedan registrados. El planificador evita repetir automáticamente respuestas 403 y 404; un enlace fallido necesita revisión antes de reintentarse.

## Qué se comprobó con la factura de prueba

Caso anonimizado de 145 kWh: el catálogo heredado devuelve $30.250 frente a $35.123 del documento, una subestimación de $4.873 (13,9 %). La reconstrucción de los importes declarados es:

| Concepto | Importe neto o exento |
|---|---:|
| Electricidad consumida, afecto | $26.300 |
| Transporte, afecto | $2.497 |
| Administración, afecto | $614 |
| Neto afecto | $29.411 |
| IVA 19 %, redondeado al peso | $5.588 |
| Servicio público, exento | $124 |
| Total | **$35.123** |

El [pliego Enel de octubre de 2026](https://www.enel.cl/content/dam/enel-cl/es/personas/informacion-de-utilidad/tarifas-y-reglamentos/tarifas/tarifas-reguladas/2026/Enel%20Distribuci%C3%B3n%20Chile%20SA._Tarifas%20Suministro%20El%C3%A9ctrico%208T_%20VAD%205T%20Octubre%20de%202026.pdf), página 1, distingue energía, compras de potencia y componente de distribución. El catálogo histórico no incluye un componente separado de distribución y sus precios de energía, transporte y fijo difieren del documento. El escenario diagnóstico para Macul, BT_AA y ETR T1 incluye esa distribución y arroja $35.124: queda una diferencia de $1 en administración. No se altera el precio para forzar coincidencia.

Este escenario **no valida la factura**: el período real cruza septiembre y octubre; falta resolver la aplicación temporal, confirmar la red, el sector y el tramo ETR por promedio del año anterior. No se deduce T1 de los 145 kWh del mes. El candidato está deshabilitado para uso ordinario y no es una tarifa vigente de noviembre.

La función pública `/revisar` y `/api/conciliar` comprueban la aritmética con importes transcritos, Decimal e IVA sobre el neto afecto. No acreditan legalidad de cargos ni precios. No hay carga de PDF ni almacenamiento de datos identificatorios. El documento privado no se copia al repositorio ni al paquete de fuentes públicas.

## Motor para todas las opciones

Actualización posterior: `/demanda` revisa cantidades BT4.2, BT4.3, AT4.2 y AT4.3 con 12 meses consecutivos y calendario de punta declarado. `demand_service.py` aplica las relaciones de los numerales 4.7 a 4.10 del Decreto 5T/2024: lectura actual de punta cuando corresponde, promedio de dos máximos del período anterior fuera de punta y promedio de dos máximos suministrados en 12 meses para 4.3. En 4.2 conserva la potencia contratada. Identifica los meses utilizados y no incluye precios. Rechaza históricos incompletos, duplicados y lecturas incoherentes. El calendario y su aplicabilidad al suministro necesitan comprobación documental; no se transforma un calendario declarado en uno aprobado. Este avance sustituye la limitación anterior de ausencia de derivación histórica únicamente para estas cuatro opciones y estos supuestos. Persisten las demás limitaciones del motor descritas a continuación.

`tariff_engine.py` incorpora componentes netos, cantidades separadas para energía y demanda, unidades, tratamiento tributario, página o celda, contexto del suministro y límites de aplicación. Rechaza períodos que crucen vigencias, perfiles de otra comuna, red, opción, sector o condición y cantidades facturables ausentes. La aprobación exige hash del original, revisión de reglas, casos contrastados y límites explícitos para todas las cantidades. El acceso interno de diagnóstico no se expone como parámetro HTTP.

Es una base de cálculo por componentes; todavía no deriva las potencias facturables de sus históricos ni implementa automáticamente todas las reglas de BT/AT/TRBT/TRAT, invierno, FET, ETR, prorrateos, reactiva, reliquidaciones, generación distribuida o sistemas aislados. Los precios publicados con IVA requieren normalización expresa: el motor nuevo admite precios netos, no adivina esa base. Los contratos de clientes libres requieren además su contrato particular.

El modelo BT1 heredado continúa disponible solo como referencia explícita en desarrollo. Su fórmula FET y demás reglas no se consideran validadas. El modo producción mantiene bloqueado ese catálogo sin aprobación. La interfaz inicia con precios propios; no ofrece un precio antiguo por defecto.

## Reproducir el respaldo

Instalar las herramientas con `requirements-sources.txt`, fuera de la imagen de producción. Los archivos `config/fuentes_*.json`, excepto el catálogo consolidado `fuentes_nacionales.json`, son solicitudes documentales conocidas, no datos tarifarios aprobados.

1. Descargar una lista seleccionada: `.venv\Scripts\python.exe scripts/source_repository.py config/fuentes_iniciales.json`.
2. Planificar enlaces publicados: `.venv\Scripts\python.exe scripts/plan_source_downloads.py` y revisar `artifacts/fuentes_nacionales/descargas_planificadas.json` antes de descargar.
3. Extraer ZIP y registrar hashes: `.venv\Scripts\python.exe scripts/index_archives.py`.
4. Construir el directorio: `.venv\Scripts\python.exe scripts/build_national_inventory.py`.
5. Verificar hashes e indexar documentos: `.venv\Scripts\python.exe scripts/build_source_catalog.py`.
6. Reproducir el diagnóstico: `.venv\Scripts\python.exe scripts/diagnose_invoice_case.py`.

No se debe sustituir automáticamente `config/tarifas.json`. El siguiente control necesario es la validación por perfil y período con casos independientes de cada familia tarifaria. La app todavía no debe anunciarse como calculadora nacional exacta.
