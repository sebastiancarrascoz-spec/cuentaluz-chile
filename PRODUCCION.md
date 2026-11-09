# CuentaLuz Chile — Preparación de producción

Fecha: 7 de noviembre de 2026. Rama local: `mejora/produccion-v2`.

## Actualización nacional

9 de noviembre: Sebastián autorizó alojar un proyecto separado de pruebas en Vercel, incluido su primer despliegue técnico Production exigido por la plataforma. La [versión de pruebas](https://cuentaluz-chile-preview-eep78iloq-sebastiancarrascoz-spec.vercel.app) está `READY` en Python 3.12, protegida con Vercel Authentication, sin persistencia local ni promoción de dominios. Pasaron salud, assets y cálculos HTTP ficticios. Esto no lanza una calculadora nacional validada. Ver [VERCEL.md](VERCEL.md); las referencias previas a ausencia de hosting corresponden al estado anterior.

8 de noviembre, avance ordenado: leer [PLAN_PRODUCCION.md](PLAN_PRODUCCION.md), [CUENTA_CONSOLIDADA.md](CUENTA_CONSOLIDADA.md), [NORMALIZACION_NACIONAL.md](NORMALIZACION_NACIONAL.md) y [OPERACION.md](OPERACION.md). La cuenta consolidada ya integra demanda e impuestos con datos declarados; 63.120 celdas de precio de cuatro empresas están normalizadas como candidatos. El corpus tiene una factura real anonimizada. Se comprobó respaldo/restauración SQLite y pasaron las pruebas de arranque/reinicio del contenedor en CI remota. No hay todavía perfiles oficiales aprobados ni despliegue público comprobado.

BT3/AT3: `/demanda-3` añade una revisión del cargo neto de demanda con precio e históricos declarados. Mantiene separadas la demanda base en kW y el mínimo monetario. Si la ventana histórica altera el resultado y no está confirmada, muestra las alternativas sin devolver un cargo único. El resultado no incluye IVA ni otros cargos de la cuenta. No activa un perfil oficial: la ventana y la aplicabilidad siguen pendientes de cotejo. Ver [DEMANDA_BT3_AT3.md](DEMANDA_BT3_AT3.md).

8 de noviembre: `/periodos` añade escenarios de precios propios con cambio de vigencia, reparto por días, fijo declarado o ponderado como supuesto y comparación de redondeos. La API permite además consumos medidos por intervalo. No activa precios oficiales ni un perfil aprobado. El caso de prueba y sus limitaciones se documentan en [PRECISION_TEMPORAL.md](PRECISION_TEMPORAL.md). Las nuevas rutas conservan `Cache-Control: no-store` y no almacenan el formulario.

La revisión `/revisar` admite lectura local de PDFs mediante PDF.js 6.5.438. La biblioteca y su worker están incluidos en `static/vendor/pdfjs/`, con licencia y manifiesto de integridad. No necesita Node ni nuevas dependencias Python en producción: Node se usa para las pruebas del parser y la preparación de assets. El archivo y texto completo permanecen en el navegador; el usuario confirma los importes antes de enviarlos al conciliador. No hay endpoint de carga. El lector no usa CDN, OCR ni servicios externos, y no acredita precios oficiales. Los límites y compatibilidad parcial se muestran en pantalla. Al desplegar, conservar `worker-src 'self'`, la misma versión de biblioteca/worker y los archivos estáticos.

El alcance solicitado incluye todas las tarifas comerciales e industriales. El estado y las brechas actuales están en [RESPALDOS_NACIONALES.md](RESPALDOS_NACIONALES.md). Hay 362 documentos públicos únicos y un directorio de las 346 comunas; no hay modelos nacionales aprobados. La revisión aritmética de facturas está disponible en `/revisar`; no valida precios. El motor nuevo por componentes tiene controles de suministro, cantidades facturables, evidencia y vigencia, pero las reglas de cada opción todavía deben integrarse y contrastarse.

La interfaz inicia con precios propios también en desarrollo. El catálogo histórico subestima el caso real revisado y no se ofrece por defecto. No se publica como tarifa actual el candidato Enel de octubre: su escenario difiere en un peso de la factura y faltan condiciones y revisión del período que cruza dos meses.

Las herramientas de respaldo utilizan `requirements-sources.txt` y quedan fuera de la imagen de producción. Los metadatos nacionales están dentro de `config/` y son necesarios para `/comunas` y `/fuentes`; los originales permanecen fuera de Git. El build no necesita descargar fuentes ni acceder a servicios externos.

## Estado real de esta entrega

La interfaz y el cálculo con precios propios están implementados. El catálogo histórico se conserva para exploración en desarrollo. No se ha publicado una web, configurado un dominio ni acreditado una revisión tarifaria vigente. El equipo local no dispone de Docker; GitHub CI sí construyó y ejecutó el contenedor, comprobó respaldo/restauración y reinicio. Ver el resultado remoto en `PLAN_PRODUCCION.md`. Sebastián prefiere seguir mejorando antes de elegir hosting y publicar.

El estado técnico `/health/ready` comprueba base de datos y disponibilidad del motor; no certifica vigencia ni exactitud tarifaria. Devuelve además el estado del catálogo.

## Dos alcances de lanzamiento

1. **Piloto con precios propios:** disponible al iniciar con `APP_ENV=production`. El usuario debe introducir el precio variable final por kWh y el cargo fijo final, ambos con impuestos. El catálogo sin aprobación devuelve 503. El producto debe anunciarse como simulador de escenarios, con sus exclusiones visibles.
2. **Calculadora con tarifas oficiales:** pendiente de validar pliegos, comunas, tipo de red, condiciones del suministro, equidad tarifaria, cargos y tramos aplicables. No basta con cambiar la fecha de actualización. Se requieren casos reales de boletas anonimizadas y reconciliación de los importes. BT2 y solar quedan fuera del lanzamiento inicial.

## Despliegue preparado

Se mantiene FastAPI/Jinja2, con CSS y JavaScript locales. La web no requiere Node en producción. Python 3.11 es el objetivo del contenedor.

- `requirements.txt`: dependencias directas probadas; `requirements.lock`: árbol de producción con versiones fijadas. Herramientas de revisión en `requirements-dev.txt`.
- `Dockerfile`: usuario sin privilegios, comprobación de salud, límite de concurrencia y ejecución sin recarga de desarrollo. No copia credenciales, scrapers, herramientas de desarrollo ni artefactos de prueba.
- `compose.yaml`: puerto solo en loopback, volumen para SQLite y capacidades Linux retiradas. Necesita proxy TLS delante para acceso público.
- `railway.toml`: construcción con Dockerfile y salud en `/health/ready`. Configurar las variables antes del despliegue.
- `.github/workflows/ci.yml`: pruebas, auditoría, construcción/arranque Docker, respaldo/restauración y reinicio. Primera ejecución remota aprobada; evidencia en `PLAN_PRODUCCION.md`. Se ejecuta para PR y cambios en `master` para evitar duplicar tareas en la rama de revisión.

Variables mínimas públicas:

```dotenv
APP_ENV=production
ALLOWED_HOSTS=tu-dominio.cl,tuservicio.up.railway.app,localhost,127.0.0.1
PORT=8000
```

Usar los dominios reales, sin protocolo ni ruta. La aplicación rechaza producción con `ALLOWED_HOSTS` ausente o con comodín. En Railway el puerto lo inyecta la plataforma. No copiar los dominios ilustrativos a producción.

Para un servidor con Docker:

```powershell
Copy-Item .env.example .env
# Editar .env con APP_ENV=production y los hosts reales.
docker compose up --build -d
```

Para Railway: conectar la rama revisada del repositorio, definir `APP_ENV` y `ALLOWED_HOSTS`, usar un volumen para `/app/data` o `DATABASE_URL` de PostgreSQL, y verificar el arranque por el dominio definitivo. La conexión con Railway y el hosting actual no se verificaron en esta entrega. No reemplazar el servicio anterior sin respaldo y prueba del candidato.

## Verificación antes de abrir acceso público

- Construir y ejecutar el contenedor en el entorno de destino. Confirmar permisos del volumen y funcionamiento con PostgreSQL si se elige ese motor; solo SQLite se probó localmente.
- Verificar TLS, certificado, dominio, recuperación de un respaldo y reinicio sin perder la base de datos.
- Configurar límites de solicitudes y conexiones en el proxy/plataforma, retención de registros técnicos y alertas de salud. El límite del cuerpo de la app es 32 KiB y el servidor preparado limita la concurrencia; no sustituyen una protección de tráfico en el borde.
- Recorrer formulario, precios propios, errores, slider, CSV, impresión y enlaces desde el dominio público. Confirmar que el catálogo no aprobado queda bloqueado.
- Definir responsable y contacto público, política de conservación del proveedor, términos del servicio y tratamiento de consultas. Esta versión no solicita datos identificatorios ni expone newsletter/GPS.
- Decidir si el piloto se publica solo con precios propios o si se completa antes la revisión tarifaria. No hay validación del motor legado contra boletas actuales.

## Flujo de tarifas

Los dos comandos históricos `python updater.py` y `python -m services.updater` ahora preparan `data/revision/tarifas_candidatas.json`. El proceso web no arranca el programador de tareas. Los candidatos no reemplazan `config/tarifas.json`, no se marcan como verificados y no envían correos.

Una revisión debe registrar por suministro: URL y archivo fuente, fecha de descarga, hash SHA-256, página y fila del pliego, inicio y término de aplicación, tipo de red y tarifa, unidades, impuestos, condiciones y casos contrastados. Solo después corresponde integrar el catálogo mediante una revisión de código.

El motor reconoce `revision_documental.estado=aprobada` junto con un intervalo de vigencia que cubra el día del cálculo. Este campo es un mecanismo de control, no una certificación externa. No debe activarse sin evidencia documentada. El modelo actual usa una tarifa por empresa y no resuelve las variaciones territoriales; ese diseño debe ampliarse antes de presentar una cobertura nacional exacta.

## Propuestas de evolución, por orden

| Prioridad | Mejora | Criterio de aceptación |
|---|---|---|
| 1 | Catálogo versionado por suministro, comuna y condiciones | Reconciliación contra pliegos y boletas anonimizadas; fuente y vigencia visibles en cada resultado |
| 2 | Lectura asistida de boleta PDF | Confirmación humana de campos, eliminación del archivo tras procesarlo y evaluación de privacidad antes de habilitar cargas |
| 3 | Comparación entre períodos y presupuesto mensual | Normalización por días y separación del cambio de precio respecto del cambio de consumo |
| 4 | Evaluación de otras tarifas | Modelo de potencia contratada/leída, clasificación y reglas aplicables, sin demandas supuestas |
| 5 | Solar con perfil horario | Generación geográfica, autoconsumo, inyección, tarifas de valorización y costos sustentados |
| 6 | Seguimiento voluntario y avisos | Consentimiento, eliminación de datos, baja y política de conservación antes de captar información |

Las primeras tres mejoras acercan el producto al uso frecuente. Publicidad, afiliados y newsletter deben evaluarse después de validar la utilidad y exactitud del núcleo.

## Fuentes primarias consultadas

- Enel, conceptos tarifarios: https://www.enel.cl/es/clientes/tarifas-y-regulacion/conceptos-tarifas.html . BT2 se define como potencia contratada; el modelo anterior la trataba como demanda máxima en punta. Se retiró de la experiencia pública.
- Enel, publicaciones tarifarias: https://www.enel.cl/es/clientes/tarifas-y-regulacion/tarifas.html . Existe publicación de noviembre de 2026, posterior al catálogo recuperado; en esta entrega no se extrajeron ni aprobaron sus importes.
- FastAPI, despliegue en contenedores: https://fastapi.tiangolo.com/deployment/docker/ . Construcción propia y transferencia de señales al proceso del servidor.

No se incorporaron datos ni autorizaciones de Inergy, ARBA o del empleador al producto.
