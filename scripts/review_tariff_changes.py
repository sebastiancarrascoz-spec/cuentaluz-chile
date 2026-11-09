"""Compara dos publicaciones normalizadas sin modificar el catálogo web."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def compare(rows, previous, current):
    if previous >= current: raise ValueError("El período nuevo debe ser posterior al anterior.")
    indexes={p:{} for p in (previous,current)}
    for r in rows:
        p=r['periodo_publicacion']
        if p not in indexes: continue
        key=r['id_serie']
        if key in indexes[p]: raise ValueError("Hay candidatos duplicados; la comparación queda en cuarentena.")
        if r['estado']!='pendiente': raise ValueError("Este flujo solo acepta candidatos pendientes.")
        indexes[p][key]=r
    old,new=indexes[previous],indexes[current]
    if not old or not new: raise ValueError("Ambos períodos deben contener candidatos.")
    changes=[]
    for key in sorted(set(old)|set(new)):
        a,b=old.get(key),new.get(key)
        kind='agregado' if a is None else 'retirado' if b is None else 'precio_modificado' if a['precio_neto_publicado']!=b['precio_neto_publicado'] else 'sin_cambio_de_precio'
        row=b or a
        changes.append({"id_serie":key,"tipo":kind,"empresa":row['empresa'],"territorio":row['territorio_original'],
            "opcion":row['opcion_original'],"cargo":row['cargo_original'],"unidad":row['unidad'],
            "anterior":{k:a[k] for k in ('precio_neto_publicado','sha256','hoja','celda')} if a else None,
            "nuevo":{k:b[k] for k in ('precio_neto_publicado','sha256','hoja','celda')} if b else None})
    return {"estado":"cuarentena_revision_obligatoria","anterior":previous,"nuevo":current,
        "resumen":dict(sorted(Counter(r['tipo'] for r in changes).items())),"cambios":changes,
        "publicacion_automatica":False,
        "requisitos_salida":["Cotejar precios y notas con PDF original", "Confirmar red, sector, condiciones e impuestos",
            "Revisar vigencias y fórmulas", "Contrastar casos independientes por componente", "Revisar diferencias mediante cambio de código"]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('datos',type=Path); parser.add_argument('--anterior',required=True)
    parser.add_argument('--nuevo',required=True); parser.add_argument('--salida',type=Path,required=True)
    args=parser.parse_args()
    if args.salida.resolve()==args.datos.resolve(): raise ValueError("No se puede sobrescribir el original.")
    raw=args.datos.read_bytes()
    report=compare([json.loads(l) for l in raw.decode('utf-8').splitlines() if l],args.anterior,args.nuevo)
    report['sha256_entrada']=hashlib.sha256(raw).hexdigest()
    args.salida.parent.mkdir(parents=True,exist_ok=True)
    with args.salida.open('x',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='cambios'},ensure_ascii=False))


if __name__=='__main__': main()
