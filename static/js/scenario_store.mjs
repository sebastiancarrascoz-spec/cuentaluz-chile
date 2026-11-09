export const STORE_KEY = "cuentaluz.escenarios.v1";
const sourceKeys = new Set(["respaldo", "respaldo_precios", "respaldo_aplicabilidad"]);
export function redactSources(value) {
  if (Array.isArray(value)) return value.map(redactSources);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([k,v]) => [k, sourceKeys.has(k) ? "Respaldo no conservado; verificar antes de usar." : redactSources(v)]));
  return value;
}
export function allowedField(name) {
  return /^(?:lectura_anterior|lectura_actual|cambio|kwh|modo_fijo|fijo_neto_periodo|redondeo|total_documento|tipo_demanda|datos_demanda|precio_punta_neto|precio_suministrada_o_contratada_neto|(?:electricidad_neta|transporte_neto|servicio_exento|fijo_neto)_[12]|(?:demanda|reactiva|otros_afectos|otros_exentos|ajustes_finales)_(?:estado|importe)|obs_(?:electricidad|transporte|administracion|demanda|reactiva|otros_afectos|exentos|ajustes_finales|neto_afecto|iva|total))$/.test(name);
}
export function readRecords(storage) {
  const raw=storage.getItem(STORE_KEY);
  if (!raw) return [];
  if (raw.length>250000) throw new Error("almacenamiento_invalido");
  const rows=JSON.parse(raw);
  if (!Array.isArray(rows)||rows.length>10) throw new Error("almacenamiento_invalido");
  for(const r of rows) {
    if(r.version!==1||typeof r.id!=="string"||!r.input?.periodo||!r.fields||typeof r.total!=="number"||!Number.isSafeInteger(r.total))throw new Error("almacenamiento_invalido");
    for(const [k,v] of Object.entries(r.fields))if(!allowedField(k)||typeof v!=="string"||v.length>20000)throw new Error("almacenamiento_invalido");
  }
  return rows;
}
export function makeRecord(snapshot, fields, id, created) {
  const safeFields=Object.fromEntries(Object.entries(fields).filter(([k,v])=>allowedField(k)&&typeof v==="string"));
  return {version:1,id,created,input:redactSources(snapshot.entrada),fields:safeFields,total:snapshot.resultado.total};
}
export function saveRecord(storage, record) {
  const rows=readRecords(storage);
  if(rows.length>=10)throw new Error("limite");
  const next=JSON.stringify([...rows,record]);
  if(next.length>250000)throw new Error("limite");
  storage.setItem(STORE_KEY,next);
}
export function removeRecord(storage,id) { storage.setItem(STORE_KEY,JSON.stringify(readRecords(storage).filter(r=>r.id!==id))); }
