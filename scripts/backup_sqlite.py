"""Respaldo consistente SQLite y restauración aislada; nunca reemplaza la app."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid


def readonly(path):
    return sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=10)


def inspect(path):
    with readonly(path) as db:
        if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
            raise ValueError('El respaldo no supera integrity_check.')
        tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        counts={name:db.execute('SELECT COUNT(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in tables}
        schema=db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
    return {"tablas_y_filas":counts,"sha256_esquema":hashlib.sha256(json.dumps(schema,ensure_ascii=False).encode()).hexdigest()}


def backup_and_verify(database,output):
    database=Path(database).resolve(); output=Path(output).resolve()
    if not database.is_file(): raise ValueError('No existe la base SQLite de origen.')
    output.mkdir(parents=True,exist_ok=True)
    tag=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    backup=output/f'cuentaluz-{tag}.sqlite3'
    restored=output/f'restauracion-prueba-{tag}.sqlite3'
    # El nombre es exclusivo y el origen se abre en modo de solo lectura.
    with backup.open('xb'): pass
    with readonly(database) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    expected=inspect(backup)
    with restored.open('xb'): pass
    with readonly(backup) as source, sqlite3.connect(restored) as target:
        source.backup(target)
    actual=inspect(restored)
    if actual!=expected: raise ValueError('La restauración aislada difiere del respaldo.')
    sha=hashlib.sha256(backup.read_bytes()).hexdigest()
    manifest={"fecha_utc":datetime.now(timezone.utc).isoformat(),"archivo":backup.name,"sha256":sha,
        "bytes":backup.stat().st_size,**expected,"integridad":"ok","restauracion_aislada":"ok",
        "archivo_restauracion":restored.name,"alcance":"Respaldo local consistente y restauración aislada. No acredita copia remota, recuperación del hosting ni PostgreSQL. Puede contener datos privados heredados: no publicar."}
    with backup.with_suffix('.manifest.json').open('x',encoding='utf-8') as f: json.dump(manifest,f,ensure_ascii=False,indent=2)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); print(json.dumps(backup_and_verify(args.database,args.output),ensure_ascii=False))


if __name__=='__main__': main()
