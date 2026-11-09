"""Prueba HTTP de un candidato ya iniciado, local o en HTTPS."""
import argparse
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener
from monitor_health import NoRedirect, probe


def verify(base):
    for attempt in range(30):
        health=probe(base)
        if health['ok']: break
        time.sleep(.2)
    else: raise AssertionError('El candidato no inició correctamente.')
    opener=build_opener(NoRedirect)
    def request(path,data=None,headers=None,raw=None):
        body=json.dumps(data).encode() if data is not None else raw
        req=Request(base.rstrip('/')+path,data=body,headers={**({'Content-Type':'application/json'} if body else {}),**(headers or {})})
        try:response=opener.open(req,timeout=5)
        except HTTPError as error:response=error
        with response: return response.status,response.read(100000).decode(),dict(response.headers.items())
    assert request('/docs')[0]==404
    assert request('/openapi.json')[0]==404
    assert request('/',headers={'Host':'invalid.example'})[0]==400
    assert request('/api/estimar',{'kwh':250})[0]==503
    code,body,headers=request('/api/estimar',{'kwh':250,'fuente':'personalizada','precio_kwh':240,'cargo_fijo':750})
    assert code==200 and json.loads(body)['total']==60750
    assert next(v for k,v in headers.items() if k.lower()=='cache-control')=='no-store'
    declared={k:{'estado':'no_aplica','respaldo':'Excluido en este caso ficticio'} for k in ('demanda','reactiva','otros_afectos','otros_exentos','ajustes_finales')}
    cuenta={'periodo':{'lectura_anterior':'2026-10-31','lectura_actual':'2026-11-30','kwh':'100',
        'precios':[{'desde':'2026-11-01','hasta':'2026-11-30','electricidad_neta':'100','transporte_neto':'10','servicio_exento':'1','fijo_neto':'500'}],
        'asignacion':'dias','modo_fijo':'ponderado','redondeo':'por_cargo'},'respaldo_precios':'Precios ficticios','adicionales':declared}
    code,body,headers=request('/api/evaluar-cuenta',cuenta)
    assert code==200 and json.loads(body)['total']==13785 and json.loads(body)['tarifa_oficial_validada'] is False
    assert next(v for k,v in headers.items() if k.lower()=='cache-control')=='no-store'
    assert request('/api/evaluar-cuenta',raw=b'x'*32769)[0]==413
    assert request('/cuenta')[0]==200 and request('/fuentes')[0]==200
    return {'estado':'ok','catalogo_pendiente_bloqueado':True,'cuenta_consolidada':13785,
        'limite_cuerpo':413,'host_invalido':400,'documentacion_api':404,
        'alcance':'Prueba técnica del proceso iniciado. No valida dominio, certificado ni tarifas oficiales.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--base-url',required=True)
    args=parser.parse_args(); print(json.dumps(verify(args.base_url),ensure_ascii=False))
