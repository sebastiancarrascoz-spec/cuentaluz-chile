"""Cobertura calculable separada de asociaciones y valores candidatos."""
import calendar
from datetime import date
import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.services.tariff_engine import TariffProfile
ROOT=Path(__file__).resolve().parents[2]


class CoverageQuery(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    cut:str|None=Field(default=None,pattern=r'^\d{5}$')
    empresa:str|None=Field(default=None,max_length=80)
    opcion:str|None=Field(default=None,max_length=12)
    mes:str=Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')

    @model_validator(mode='after')
    def valid_date(self):
        date.fromisoformat(self.mes+'-01');return self


def validation_coverage(q:CoverageQuery):
    communes=json.loads((ROOT/'config/cobertura_nacional.json').read_text(encoding='utf-8'))['comunas']
    index=json.loads((ROOT/'config/indice_validacion.json').read_text(encoding='utf-8'))
    profiles=[TariffProfile.model_validate(p) for p in json.loads((ROOT/'config/perfiles_aprobados.json').read_text(encoding='utf-8'))]
    first=date.fromisoformat(q.mes+'-01');last=date(first.year,first.month,calendar.monthrange(first.year,first.month)[1])
    company=q.empresa.upper() if q.empresa else None
    rows=[]
    for c in communes:
        if q.cut and c['cut']!=q.cut:continue
        entries=[e for e in index['entradas'] if e['cut']==c['cut'] and e['mes']==q.mes and (not company or e['empresa']==company) and (not q.opcion or q.opcion in e['opciones'])]
        approved=[p for p in profiles if p.estado=='aprobado' and p.cut==c['cut'] and p.desde<=first and p.hasta>=last and (not company or p.empresa.upper()==company) and (not q.opcion or p.opcion==q.opcion)]
        if company and company not in [n.upper() for n in c['concesionarias_cne']] and not entries and not approved:continue
        refs=sorted({sha for e in entries for sha in e['fuentes']})
        rows.append({'cut':c['cut'],'comuna':c['nombre'],'region':c['region'],'empresas_asociadas':c['concesionarias_cne'],
            'empresas_con_candidatos':sorted({e['empresa'] for e in entries}),'valores_candidatos':sum(e['valores_candidatos'] for e in entries),
            'opciones_detectadas':sorted({o for e in entries for o in e['opciones']}),'fuentes':[index['fuentes'][sha] for sha in refs],
            'perfiles_aprobados':len(approved),'estado':'perfiles_documentados' if approved else 'candidatos_pendientes' if entries else 'sin_valores_en_lote',
            'condiciones_por_confirmar':[{'empresa':p.empresa,'sector':p.sector,'red':p.red,'opcion':p.opcion,'condicion':p.condicion} for p in approved]})
    return {'consulta':q.model_dump(),'comunas':rows,'selector_comunas':[{'cut':c['cut'],'nombre':c['nombre'],'region':c['region']} for c in sorted(communes,key=lambda c:c['nombre'])],
        'selector_empresas':sorted({name for c in communes for name in c['concesionarias_cne']}|{e['empresa'] for e in index['entradas']}),
        'total':len(rows),'total_perfiles_biblioteca':sum(p.estado=='aprobado' for p in profiles),'comunas_con_perfiles':sum(r['perfiles_aprobados']>0 for r in rows),
        'comunas_con_candidatos':sum(r['valores_candidatos']>0 for r in rows),
        'alcance':'Los candidatos no habilitan cálculo oficial. El filtro de opción confirma presencia de una sección; el conteo incluye todas las secciones del grupo empresa/comuna/mes y no representa cargos calculables de esa opción. Un perfil documentado exige además confirmar sector, red, condiciones y cobertura de todo el período de la cuenta. Sin valores en este lote no significa ausencia de servicio ni de documentos en otras fuentes.'}
