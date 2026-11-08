# Operación del candidato

El proceso de producción se probó localmente con SQLite y en un contenedor de CI de GitHub. Hosting, dominio, certificado y PostgreSQL requieren comprobación en el destino. Las pruebas técnicas no acreditan exactitud tarifaria. Consultar `PLAN_PRODUCCION.md` antes de lanzar. Sebastián decidió seguir mejorando antes de publicar y aún no tiene hosting/dominio.

## Respaldo y recuperación

```powershell
python scripts/backup_sqlite.py --database data/cuentaluz.db --output artifacts/backups
```

El comando abre el origen en modo de solo lectura y usa la API de respaldo consistente, compatible con WAL activo. Crea nombres exclusivos, manifiesto SHA-256 y una restauración aislada; comprueba `integrity_check`, esquema y conteos. No reemplaza la base en uso. Las pruebas incluyen transacciones confirmadas en WAL y dos respaldos que conservan versiones distintas.

Verificado el 8 de noviembre: base activa de 28.672 bytes, tablas `sec_cache` y `subscribers` vacías; integridad y restauración aislada correctas. Respaldo en `artifacts/backups/cuentaluz-20261108T163038Z-6b81b113.sqlite3`, hash `dce0df29fd3bfce314ed15b7920164013d1601f91995e837572f41a1d31e1ea0`. Copia local únicamente.

La imagen incluye `ops/backup_sqlite.py` y `ops/monitor_health.py`. Tras construir y arrancar el contenedor:

```powershell
docker compose exec web python ops/backup_sqlite.py --database data/cuentaluz.db --output data/backups
```

Confirmar el nombre del servicio en Compose y permisos del volumen. En este repositorio el servicio se denomina `web`. Antes de un cambio, copiar el respaldo y su manifiesto a almacenamiento remoto controlado, comprobar su hash y ensayar la restauración en un entorno separado. Todavía no hay destino remoto ni retención programada. No subir bases ni manifiestos operativos a Git.

Para recuperar en producción: detener escrituras, conservar una copia de la base y del candidato actuales, verificar hash/integridad del respaldo, probarlo en un entorno aislado con la misma versión, y recién entonces sustituir la base en una ventana de mantenimiento. Volver a comprobar salud, datos y formularios antes de abrir tráfico. No usar SQLite para restaurar una base PostgreSQL.

## Disponibilidad y verificación

```powershell
python scripts/monitor_health.py --base-url http://127.0.0.1:8018 --output artifacts/health-monitor.json
```

La sonda comprueba `/health/live` y `/health/ready`, devuelve código 1 ante un fallo y acepta HTTPS para destinos remotos. No sigue redirecciones ni usa credenciales. No envía facturas. La ejecución local pasó; no hay aún monitor remoto, alarmas ni responsable configurados. Programar esta sonda y sus alertas solo después de acordar el destino y responsable operativo.

`verify_runtime.py --base-url ...` verifica además bloqueo del catálogo, precios propios, cuenta consolidada, límite de cuerpo, hosts y documentación API cerrada. Requiere un proceso iniciado en modo producción. `verify_production.py` arranca y cierra un proceso local aislado para esas comprobaciones.

## Lanzamiento

CI ejecuta construcción, arranque HTTP, prueba de respaldo/restauración con el usuario del contenedor, reinicio y repetición de controles. La primera ejecución remota aprobada es https://github.com/sebastiancarrascoz-spec/cuentaluz-chile/actions/runs/42510260109 para `34822ea545a695b0e6e12c47a06ba9458a26efbb`. No reemplaza la prueba de persistencia del volumen de hosting ni la recuperación desde almacenamiento remoto. Cada modificación posterior debe conservar su propia evidencia y corregir fallos antes de promover el candidato.

Después se necesitan hosting y dominio concretos, presupuesto si hay servicios pagados, HTTPS, volumen persistente, copia remota, retención, alertas y contacto público. El piloto con precios propios debe describirse como escenario declarado. Para activar tarifas oficiales falta cerrar los controles documentales y numéricos de los perfiles; no se habilitan cambiando una fecha o una bandera sin evidencia.
