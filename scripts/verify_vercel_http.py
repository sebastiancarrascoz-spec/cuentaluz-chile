"""Prueba la app publicada usando la autenticación oficial de Vercel CLI.

No imprime ni guarda credenciales, cookies, respuestas completas ni variables
de entorno. Solo registra rutas, estados y resultados ficticios comprobados.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]


def verify(base):
    parsed=urlsplit(base)
    if parsed.scheme!='https' or not re.fullmatch(r'cuentaluz-chile-preview-[a-z0-9]+-sebastiancarrascoz-spec\.vercel\.app',parsed.hostname or '') or parsed.port is not None or parsed.path not in ('','/') or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('El destino debe ser el despliegue de pruebas revisado.')
    cli=ROOT/'.qa/vercel-cli/node_modules/.bin/vercel.cmd'
    folder=ROOT/'artifacts/vercel-http';folder.mkdir(parents=True,exist_ok=True)
    checks=[]
    def request(path,payload=None):
        args=[str(cli),'curl',base.rstrip('/')+path,'--scope','sebastiancarrascoz-spec','--','--silent','--show-error','--include']
        if payload is not None:
            data_file=folder/'entrada-ficticia.json'
            data_file.write_text(json.dumps(payload),encoding='utf-8')
            args+=['--request','POST','--header','Content-Type: application/json','--data-binary','@'+str(data_file)]
        result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=60)
        if result.returncode: raise AssertionError(f'La CLI no completó la comprobación de {path}.')
        blocks=list(re.finditer(rb'^HTTP/\S+\s+(\d+)[^\r\n]*\r?\n(.*?)\r?\n\r?\n',result.stdout,re.M|re.S))
        if not blocks: raise AssertionError(f'No se reconoció la respuesta HTTP de {path}.')
        block=blocks[-1];code=int(block[1]);headers={}
        for line in block[2].splitlines():
            if b':' in line:
                k,v=line.split(b':',1);headers[k.decode().lower()]=v.decode().strip()
        checks.append({'ruta':path,'http':code})
        return code,result.stdout[block.end():],headers
    code,body,_=request('/health/ready')
    assert code==200 and json.loads(body)['almacenamiento']=='sin_persistencia'
    code,body,headers=request('/cuenta')
    assert code==200 and 'Vista previa de pruebas'.encode() in body
    assert headers.get('cache-control')=='no-store'
    assert 'noindex' in headers.get('x-robots-tag','')
    assert 'worker-src' in headers.get('content-security-policy','')
    for path in ('/comparar','/cobertura-validada','/revisar'):
        code,_,headers=request(path)
        assert code==200, {'ruta':path,'http':code}
        if path!='/cobertura-validada':
            assert headers.get('cache-control')=='no-store', {'ruta':path,'cache':headers.get('cache-control')}
    for asset in ('account_workspace.mjs','invoice_metadata.mjs','scenario_store.mjs'):
        code,body,_=request('/static/js/'+asset)
        assert code==200 and hashlib.sha256(body).digest()==hashlib.sha256((ROOT/'static/js'/asset).read_bytes()).digest()
    code,body,headers=request('/static/css/custom.css')
    assert code==200 and 'text/css' in headers.get('content-type','')
    code,body,headers=request('/static/vendor/pdfjs/pdf.worker.min.mjs')
    assert code==200
    assert hashlib.sha256(body).hexdigest()==hashlib.sha256((ROOT/'static/vendor/pdfjs/pdf.worker.min.mjs').read_bytes()).hexdigest()
    code,body,_=request('/api/estimar',{'kwh':250})
    assert code==503
    code,body,headers=request('/api/estimar',{'kwh':250,'fuente':'personalizada','precio_kwh':240,'cargo_fijo':750})
    assert code==200 and json.loads(body)['total']==60750 and headers.get('cache-control')=='no-store'
    additional={k:{'estado':'no_aplica','respaldo':'Caso ficticio'} for k in ('demanda','reactiva','otros_afectos','otros_exentos','ajustes_finales')}
    data={'periodo':{'lectura_anterior':'2026-10-31','lectura_actual':'2026-11-30','kwh':'100',
        'precios':[{'desde':'2026-11-01','hasta':'2026-11-30','electricidad_neta':'100','transporte_neto':'10','servicio_exento':'1','fijo_neto':'500'}],
        'asignacion':'dias','modo_fijo':'ponderado','redondeo':'por_cargo'},'respaldo_precios':'Precios ficticios','adicionales':additional}
    code,body,headers=request('/api/evaluar-cuenta',data)
    assert code==200 and json.loads(body)['total']==13785 and json.loads(body)['tarifa_oficial_validada'] is False
    assert headers.get('cache-control')=='no-store'
    observed={**data,'observado':{'electricidad':10001,'total':13785}}
    code,body,_=request('/api/evaluar-cuenta',observed)
    assert code==200 and json.loads(body)['revision']
    scenarios=[{'nombre':name,'opcion':'BT2','aplicabilidad_declarada':False,
        'respaldo_aplicabilidad':'Caso ficticio, pendiente','cuenta':data} for name in ('Base','Alternativa')]
    code,body,headers=request('/api/comparar-tarifas',{'escenarios':scenarios})
    assert code==200 and json.loads(body)['menor_costo_declarado']==[] and headers.get('cache-control')=='no-store'
    code,body,headers=request('/api/comparar-guardados',{'anterior':data,'actual':data})
    assert code==200 and json.loads(body)['diferencia_total']==0 and headers.get('cache-control')=='no-store'
    code,_,_=request('/docs');assert code==404
    report={'destino':base,'resultado':'ok','comprobaciones':checks,'precios_propios':60750,
        'cuenta_consolidada':13785,'worker_pdfjs_hash':'coincide','proteccion_vercel':'conservada; pruebas con CLI autenticada',
        'alcance':'Verificación HTTP del despliegue Python 3.12 con datos ficticios. No valida tarifas oficiales ni constituye prueba visual de navegador remoto.'}
    (ROOT/'artifacts/vercel-http-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base-url',required=True)
    print(json.dumps(verify(parser.parse_args().base_url),ensure_ascii=False))
