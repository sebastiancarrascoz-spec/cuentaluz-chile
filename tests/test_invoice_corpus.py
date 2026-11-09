import json
from pathlib import Path
from app.services.invoice_service import InvoiceInput, conciliar


def test_real_anonymized_corpus_matches_transcribed_amounts_without_approving_tariffs():
    fixtures=Path(__file__).parent/'fixtures/facturas'
    cases=[json.loads(p.read_text(encoding='utf-8')) for p in sorted(fixtures.glob('*.json'))]
    assert cases
    for case in cases:
        result=conciliar(InvoiceInput(**case['entrada']))
        assert all(result[key]==expected for key,expected in case['esperado'].items()), case['id']
        assert case['validacion_tarifaria']=='pendiente'
