"""Sonda técnica sin datos de clientes; devuelve código 1 ante fallos."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, Request


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


def probe(base):
    url=urlsplit(base)
    if url.username or url.password or url.query or url.fragment or url.path not in ('','/'):
        raise ValueError('Usa únicamente el origen público, sin credenciales, ruta ni consulta.')
    if url.scheme!='https' and not (url.scheme=='http' and url.hostname in ('localhost','127.0.0.1','::1')):
        raise ValueError('Usa HTTPS; HTTP solo se admite para pruebas locales.')
    opener=build_opener(NoRedirect)
    checks=[]
    for path in ('/health/live','/health/ready'):
        try:
            with opener.open(Request(base.rstrip('/')+path,headers={'Accept':'application/json'}),timeout=5) as response:
                payload=json.loads(response.read(4097))
                ok=response.status==200 and isinstance(payload,dict) and payload.get('status')=='ok'
                checks.append({'ruta':path,'ok':ok,'http':response.status})
        except (HTTPError,URLError,TimeoutError,ValueError,OSError):
            checks.append({'ruta':path,'ok':False})
    return {'fecha_utc':datetime.now(timezone.utc).isoformat(),'ok':all(c['ok'] for c in checks),'comprobaciones':checks,
        'alcance':'Disponibilidad técnica; no certifica precios ni exactitud tarifaria.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',required=True); parser.add_argument('--output',type=Path)
    args=parser.parse_args(); result=probe(args.base_url)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(0 if result['ok'] else 1)


if __name__=='__main__': main()
