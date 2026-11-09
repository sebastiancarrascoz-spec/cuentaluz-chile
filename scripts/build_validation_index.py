"""Resumen público por CUT/empresa/mes de candidatos; no aprueba perfiles."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def detected_options(section):
    label=section.upper()
    options={re.sub(r'\s+','',v) for v in re.findall(r'\b(?:TRBT|TRAT|BT|AT)\s*[1-6]?(?:\.[1-3])?',label)}
    compact=re.sub(r'\s+','',label)
    for prefix in ('BT','AT'):
        if prefix+'4.1,4.2,4.3' in compact:options.update(prefix+'4.'+str(i) for i in (1,2,3))
    return options


def main():
    summary=json.loads((ROOT/'config/normalizacion_saesa.json').read_text(encoding='utf-8'))
    raw=(ROOT/f"artifacts/normalizacion/saesa-{summary['sha256_datos'][:16]}.jsonl").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=summary['sha256_datos']:raise ValueError('Hash de normalización distinto.')
    groups={};sources={}
    for line in raw.decode('utf-8').splitlines():
        r=json.loads(line)
        if not r['cut']:continue
        key=(r['cut'],r['empresa'].upper(),r['periodo_publicacion'])
        g=groups.setdefault(key,{'cut':key[0],'empresa':key[1],'mes':key[2],'valores_candidatos':0,'opciones':set(),'fuentes':set()})
        g['valores_candidatos']+=1;g['fuentes'].add(r['sha256'])
        g['opciones'].update(detected_options(r['opcion_original']))
        sources[r['sha256']]={'sha256':r['sha256'],'url':r['fuente'],'empresa':key[1],'mes':key[2]}
    entries=[{**g,'opciones':sorted(g['opciones']),'fuentes':sorted(g['fuentes'])} for _,g in sorted(groups.items())]
    out={'estado':'candidatos_sin_aprobar','sha256_normalizacion':summary['sha256_datos'],'entradas':entries,'fuentes':sources,
        'alcance':'Detección de secciones del primer lote, sin verificar reglas, red, elegibilidad ni impuestos. La presencia de una opción no acredita un perfil completo.'}
    (ROOT/'config/indice_validacion.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'grupos':len(entries),'comunas':len({r['cut'] for r in entries}),'perfiles_aprobados':0}))


if __name__=='__main__':main()
