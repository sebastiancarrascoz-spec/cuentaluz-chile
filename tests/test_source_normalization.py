from copy import deepcopy
from decimal import Decimal
import pytest
from scripts.normalize_saesa_sources import published_price, column_name, column_number, normalized
from scripts.review_tariff_changes import compare


def test_preserves_published_decimals_instead_of_binary_float():
    c={"valor":"27.804000000000002","numerico":True,"formato":"#,##0.000"}
    assert published_price(c)=='27.804'
    assert c['valor']=='27.804000000000002'
    c['valor']='0.855'; assert published_price(c)=='0.855'
    c['valor']='0'; assert published_price(c)=='0.000'
    c['formato']='General'
    with pytest.raises(ValueError): published_price(c)


@pytest.mark.parametrize('value',['-1','NaN','Infinity'])
def test_invalid_xml_number_never_becomes_price(value):
    with pytest.raises(ValueError): published_price({"valor":value,"numerico":True,"formato":"#,##0.000"})


def test_columns_and_exact_territory_matching():
    for n in (1,26,27,120,16384): assert column_number(column_name(n))==n
    assert normalized('  LA   UNIÓN ')==normalized('La Unión')
    assert normalized('S. Juan De La Costa')!=normalized('San Juan de la Costa')


def row(period,price='1.000',key='serie'):
    return {"periodo_publicacion":period,"id_serie":key,"precio_neto_publicado":price,
        "estado":"pendiente","empresa":"Ficticia","territorio_original":"Comuna ficticia",
        "opcion_original":"Tarifa ficticia","cargo_original":"Energía","unidad":"$/kWh",
        "sha256":"0"*64,"hoja":"Pub. PDF","celda":"D19"}


def test_diff_separates_changed_removed_added_and_never_publishes():
    rows=[row('2026-10'),row('2026-11','2.000'),row('2026-10',key='retirada'),row('2026-11',key='nueva')]
    before=deepcopy(rows)
    r=compare(rows,'2026-10','2026-11')
    assert r['resumen']=={'agregado':1,'precio_modificado':1,'retirado':1}
    assert not r['publicacion_automatica'] and rows==before


def test_duplicates_and_absent_period_keep_data_in_quarantine():
    with pytest.raises(ValueError): compare([row('2026-10'),row('2026-10'),row('2026-11')],'2026-10','2026-11')
    with pytest.raises(ValueError): compare([row('2026-10')],'2026-10','2026-11')
    with pytest.raises(ValueError): compare([],'2026-11','2026-10')
