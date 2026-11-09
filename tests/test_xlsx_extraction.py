from hashlib import sha256
from zipfile import ZipFile
from scripts.normalize_saesa_sources import extract_document
import pytest


def test_xml_extractor_keeps_zero_and_mixed_aggregate_and_blocks_missing_price(tmp_path):
    path=tmp_path/'fuente.xlsx'
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    def text(ref,value): return f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'
    def number(ref,value): return f'<c r="{ref}" s="1"><v>{value}</v></c>'
    with ZipFile(path,'w') as z:
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Pub. PDF" sheetId="1" r:id="r1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/styles.xml',f'<styleSheet xmlns="{ns}"><numFmts><numFmt numFmtId="165" formatCode="#,##0.000"/></numFmts><cellXfs><xf numFmtId="0"/><xf numFmtId="165"/></cellXfs></styleSheet>')
        cells=[text('B4','Tarifas de Suministro Eléctrico - noviembre de 2026'),text('B5','desde el 01 de noviembre de 2026'),
            text('B6','Comunas'),text('D6','Comuna ficticia - Aéreo'),text('D8','$ NETO'),text('B9','Tarifa BT2 y BT3'),
            text('B10','Cargo fijo'),text('C10','$/mes'),number('D10','0'),
            text('B11','Transporte de Electricidad'),text('C11','$/kWh'),number('D11','27.804000000000002'),
            text('B12','Cargo sin valor'),text('C12','$/kWh'),text('B13','Precios para valorización de inyecciones'),
            text('B14','Inyección'),text('C14','$/kWh'),number('D14','999')]
        z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{ns}"><sheetData><row>'+''.join(cells)+'</row></sheetData></worksheet>')
    source={'archivo':'fuente.xlsx','sha256':sha256(path.read_bytes()).hexdigest(),'url':'https://example.test/fuente.xlsx','proveedor':'Ficticia'}
    rows,issues=extract_document(source,[{'nombre':'Comuna ficticia','cut':'99999'}],tmp_path)
    assert len(rows)==2 and len(issues)==1 and issues[0]['celda']=='D12'
    assert rows[0]['precio_neto_publicado']=='0.000'
    assert rows[1]['precio_neto_publicado']=='27.804' and rows[1]['valor_xml']=='27.804000000000002'
    assert rows[1]['rol_fila']=='agregado_no_sumar_con_desglose'
    assert all(r['opcion_original']=='Tarifa BT2 y BT3' and r['estado']=='pendiente' and r['tratamiento']=='pendiente' for r in rows)
    assert all(r['cut']=='99999' and r['vigencia_hasta_confirmada'] is None for r in rows)
    with path.open('ab') as f:f.write(b'changed')
    with pytest.raises(ValueError,match='hash'):extract_document(source,[],tmp_path)
