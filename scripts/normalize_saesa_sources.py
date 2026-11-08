"""Extrae candidatos del diseño Pub. PDF del grupo Saesa, sin aprobar tarifas.

Solo usa ZIP/XML estándar: conserva los decimales del XML y el formato de
publicación, evitando convertir precios a float. Originales y detalle quedan
en artifacts; el resumen versionado no habilita cálculo oficial.
"""
import hashlib
import csv
import json
import posixpath
import re
import unicodedata
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
N = {"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
MONTHS = {v:i for i,v in enumerate(("enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"),1)}


def normalized(value):
    return " ".join("".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn").split())


def read_publication(path):
    with ZipFile(path) as z:
        if len(z.infolist()) > 5000 or sum(i.file_size for i in z.infolist()) > 100_000_000:
            raise ValueError("Libro demasiado grande para la extracción documental.")
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        sheet = workbook.find("s:sheets/s:sheet",N)
        if sheet is None or sheet.attrib["name"] not in ("Pub. PDF", "Pub-PDF"):
            raise ValueError("Diseño de publicación no reconocido.")
        rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relation=next(r for r in rels if r.attrib['Id']==rid)
        if relation.attrib.get('TargetMode')=='External':
            raise ValueError("No se admiten hojas externas.")
        target=relation.attrib['Target']
        member=posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/'+target)
        if not member.startswith('xl/worksheets/') or '..' in member.split('/'):
            raise ValueError("Referencia de hoja no admitida.")
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(t.text or '' for t in si.findall('.//s:t',N)) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',N)]
        styles=ET.fromstring(z.read('xl/styles.xml'))
        formats={int(e.attrib['numFmtId']):e.attrib['formatCode'] for e in styles.findall('s:numFmts/s:numFmt',N)}
        style_formats=[formats.get(int(e.attrib.get('numFmtId','0')), 'General') for e in styles.findall('s:cellXfs/s:xf',N)]
        cells={}
        for c in ET.fromstring(z.read(member)).findall('.//s:sheetData/s:row/s:c',N):
            v=c.find('s:v',N); value=v.text if v is not None else None
            kind=c.attrib.get('t')
            if kind=='s' and value is not None: value=shared[int(value)]
            elif kind=='inlineStr': value=''.join(t.text or '' for t in c.findall('.//s:t',N))
            if value is None: continue
            cells[c.attrib['r']]={"valor":value,"numerico":kind in (None,'n'),
                "formato":style_formats[int(c.attrib.get('s','0'))],"formula":c.find('s:f',N) is not None}
        return sheet.attrib['name'], cells


def column_number(label):
    result=0
    for c in label: result=result*26+ord(c)-64
    return result


def column_name(number):
    result=''
    while number:
        number, r=divmod(number-1,26); result=chr(65+r)+result
    return result


def published_price(cell):
    if not cell['numerico']:
        raise ValueError("La celda de precio no contiene un número en caché.")
    raw=Decimal(cell['valor'])
    if not raw.is_finite() or raw < 0:
        raise ValueError("Precio inválido.")
    # Este importador está limitado al diseño que publica tres decimales.
    if cell['formato'] != '#,##0.000':
        raise ValueError("Formato de precio no reconocido; revisión manual necesaria.")
    return format(raw.quantize(Decimal('.001'),rounding=ROUND_HALF_UP),'f')


def extract_document(document, communes, root=ROOT):
    path=(root/document['archivo']).resolve()
    if not path.is_relative_to(root.resolve()): raise ValueError("Original fuera del repositorio documental.")
    if hashlib.sha256(path.read_bytes()).hexdigest()!=document['sha256']:
        raise ValueError("El hash del original no coincide con el índice.")
    sheet,cells=read_publication(path)
    v=lambda ref: cells.get(ref,{}).get('valor','')
    header_row=min(int(re.search(r'\d+$',ref)[0]) for ref,c in cells.items() if normalized(c['valor'])=='comunas')
    net_row=header_row+2
    title=v(f'B{header_row-2}')
    match=re.search(r'(?i)(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre) de (\d{4})',title)
    if not match: raise ValueError("No se reconoce el período de la publicación.")
    month=MONTHS[match[1].lower()]; year=int(match[2])
    period=f'{year:04d}-{month:02d}'
    start=re.search(r'(?i)desde el\s+(\d{1,2}) de\s+(\w+) de (\d{4})',v(f'B{header_row-1}'))
    if not start or MONTHS.get(start[2].lower())!=month or int(start[3])!=year:
        raise ValueError("La fecha de aplicación declarada no coincide con el título.")
    from datetime import date
    since=date(year,month,int(start[1])).isoformat()
    headers=sorted((column_number(re.sub(r'\d+$','',ref)),re.sub(r'\d+$','',ref)) for ref,c in cells.items() if int(re.search(r'\d+$',ref)[0])==net_row and c['valor'].strip()=='$ NETO')
    if not headers: raise ValueError("No se reconocen columnas de precios netos.")
    # Asociaciones por nombre exacto normalizado: sin inferir distribuidora ni sector.
    by_name={}
    for c in communes: by_name.setdefault(normalized(c['nombre']),[]).append(c['cut'])
    rows=[]; issues=[]
    blocks=sorted(column_number(re.sub(r'\d+$','',ref)) for ref,c in cells.items() if int(re.search(r'\d+$',ref)[0])==header_row and normalized(c['valor'])=='comunas')
    for col,letter in headers:
        header=v(letter+str(header_row)).strip()
        if not header: raise ValueError("Columna neta sin encabezado territorial.")
        location=header.rsplit(' - ',1)[0]
        cut_candidates=by_name.get(normalized(location),[])
        cut=cut_candidates[0] if len(cut_candidates)==1 else None
        label_col=column_name(max(b for b in blocks if b<col))
        unit_col=column_name(column_number(label_col)+1)
        section=None
        for row in range(net_row+1,1000):
            label=v(f'{label_col}{row}').strip(); unit=v(f'{unit_col}{row}').strip()
            if normalized(label).startswith(('cargo por servicio publico:', 'precios para valorizacion')): break
            if label.startswith('Tarifa '): section=label; continue
            if not label or not unit or not section: continue
            ref=f'{letter}{row}'; cell=cells.get(ref)
            if cell is None:
                issues.append({"celda":ref,"territorio":header,"motivo":"Sin valor numérico publicado; no se sustituye por cero."}); continue
            try: price=published_price(cell)
            except ValueError as e:
                issues.append({"celda":ref,"territorio":header,"motivo":str(e)}); continue
            etr=re.search(r'factor ETR\s+(\d)',label,re.I)
            tax='exento' if 'exento de iva' in normalized(label) else 'pendiente'
            role='agregado_no_sumar_con_desglose' if normalized(label)=='transporte de electricidad' else 'componente_o_alternativa_por_revisar'
            series='|'.join((document['proveedor'],sheet,header,section,label,unit))
            key=period+'|'+series
            rows.append({"id":hashlib.sha256(key.encode()).hexdigest(),"id_serie":hashlib.sha256(series.encode()).hexdigest(),"empresa":document['proveedor'],
                "periodo_publicacion":period,"vigencia_desde_declarada":since,"vigencia_hasta_confirmada":None,
                "cut":cut,"territorio_original":header,"red_normalizada":None,"opcion_original":section,
                "cargo_original":label,"tramo_etr_detectado":etr[1] if etr else None,"unidad":unit,
                "precio_neto_publicado":price,"valor_xml":cell['valor'],"formato":cell['formato'],
                "celda_con_formula":cell['formula'],"precio_con_iva_publicado_xml":v(column_name(col+1)+str(row)),
                "tratamiento":tax,"rol_fila":role,"hoja":sheet,"celda":ref,
                "fuente":document['url'],"sha256":document['sha256'],"estado":"pendiente"})
    if len({r['id'] for r in rows})!=len(rows): raise ValueError("Candidatos duplicados dentro del documento.")
    return rows,issues


def main():
    catalog=json.loads((ROOT/'config/fuentes_nacionales.json').read_text(encoding='utf-8'))
    communes=json.loads((ROOT/'config/cobertura_nacional.json').read_text(encoding='utf-8'))['comunas']
    docs=[d for d in catalog['documentos'] if d['tipo']=='xlsx' and 'Suministro Regulado' in d['archivo'] and d['proveedor'] in ('saesa','frontel','luzosorno','edelaysen')]
    all_rows=[]; reports=[]
    for d in sorted(docs,key=lambda d:(d['proveedor'],d['archivo'])):
        rows,issues=extract_document(d,communes)
        all_rows.extend(rows)
        reports.append({"empresa":d['proveedor'],"sha256":d['sha256'],"periodo":rows[0]['periodo_publicacion'] if rows else None,
            "candidatos":len(rows),"incidencias":issues})
    target=ROOT/'artifacts/normalizacion'; target.mkdir(parents=True,exist_ok=True)
    payload=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in all_rows).encode('utf-8')
    digest=hashlib.sha256(payload).hexdigest()
    (target/f'saesa-{digest[:16]}.jsonl').write_bytes(payload)
    (target/'informe.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    groups=Counter((r['cut'] or '',r['territorio_original'],r['empresa'],r['periodo_publicacion'],r['opcion_original'],r['sha256']) for r in all_rows)
    assigned={r['cut'] for r in all_rows if r['cut']}
    matrix=target/f'matriz-comunas-{digest[:16]}.csv'
    with matrix.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['CUT','Territorio','Empresa del documento','Período publicado','Sección original','SHA-256 original','Valores candidatos','Estado de cálculo'])
        for fields,count in sorted(groups.items()): writer.writerow([*fields,count,'pendiente'])
        for c in sorted(communes,key=lambda c:c['cut']):
            if c['cut'] not in assigned: writer.writerow([c['cut'],c['nombre'],'','','','',0,'sin valores normalizados en este lote'])
    summary={"estado":"candidatos_sin_aprobar","documentos":len(reports),"candidatos":len(all_rows),"sha256_datos":digest,
        "por_empresa":dict(sorted(Counter(r['empresa'] for r in all_rows).items())),
        "por_periodo":dict(sorted(Counter(r['periodo_publicacion'] for r in all_rows).items())),
        "comunas_cut_distintas":len(assigned),"comunas_sin_valores_en_lote":len(communes)-len(assigned),
        "matriz_archivo":matrix.relative_to(ROOT).as_posix(),
        "territorios_sin_cut":sorted({r['territorio_original'] for r in all_rows if not r['cut']}),
        "secciones_originales":sorted({r['opcion_original'] for r in all_rows}),
        "incidencias":sum(len(r['incidencias']) for r in reports),"perfiles_aprobados":0,
        "alcance":"Extracción del diseño Pub. PDF de suministro regulado; conserva alternativas y agregados. No sumar filas indiscriminadamente. Faltan impuesto de cada componente, red normalizada, condiciones, vigencia final y validación contra PDF y facturas. No habilita cálculo oficial."}
    (ROOT/'config/normalizacion_saesa.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__': main()
