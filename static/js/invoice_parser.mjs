// Solo importes y páginas. El texto completo del documento nunca se devuelve.
const amount = String.raw`\$?\s*((?:\d{1,3}(?:\.\d{3})+|\d{1,12})(?:,\d{1,4})?)`;
const labels = {
  administracion: String.raw`Administraci[oó]n\s+del\s+servicio`,
  electricidad: String.raw`Electricidad\s+consumida(?:\s*\(\s*[\d.,]+\s*kWh\s*\))?`,
  transporte: String.raw`Transporte\s+de\s+electricidad`,
  servicio_publico: String.raw`Cargo\s+por\s+servicio\s+p[uú]blico`,
  neto: String.raw`(?:Total\s+monto\s+neto|Total\s+neto|Neto\s+afecto)`,
  iva: String.raw`(?:Total\s+)?I\.?\s*V\.?\s*A\.?\s*\(\s*19\s*%\s*\)`,
  exentos: String.raw`(?:Monto\s+exento|Total\s+exento)`,
  total_documento: String.raw`(?:Monto\s+total|Total\s+a\s+pagar|Total\s+del\s+documento)`,
};

export function analizarPaginas(pages) {
  if (!Array.isArray(pages) || !pages.length || pages.length > 12) throw new Error("paginas");
  const found = Object.fromEntries(Object.keys(labels).map((key) => [key, []]));
  let length = 0;
  for (const page of pages) {
    if (typeof page.texto !== "string" || !Number.isInteger(page.numero) || page.numero < 1 || page.numero > 12) throw new Error("paginas");
    length += page.texto.length;
    if (length > 200000) throw new Error("texto_largo");
    const text = page.texto.normalize("NFC").replaceAll("\r", "\n").replaceAll("\u00a0", " ");
    for (const [key, label] of Object.entries(labels)) {
      const regex = new RegExp(String.raw`(?:^|\n)[ \t]*${label}[ \t:]*\n?[ \t]*${amount}[ \t]*(?=\n|$)`, "gimu");
      for (const match of text.matchAll(regex)) {
        const value = Number(match[1].replaceAll(".", "").replace(",", "."));
        if (Number.isFinite(value) && value >= 0 && value <= 100000000000) {
          found[key].push({valor: value, pagina: page.numero});
        }
      }
    }
  }
  const fields = {}, ambiguous = [];
  for (const [key, candidates] of Object.entries(found)) {
    if (new Set(candidates.map((c) => c.valor)).size > 1) ambiguous.push(key);
    else if (candidates.length) fields[key] = candidates[0];
  }
  const required = ["administracion", "electricidad", "transporte", "neto", "iva", "exentos", "total_documento"];
  const missing = required.filter((key) => !fields[key]);
  const warnings = [];
  if (missing.length) warnings.push("Faltan importes o encabezados necesarios. Completa la revisión manual.");
  if (ambiguous.length) warnings.push("Hay importes diferentes para un mismo concepto. No se selecciona uno automáticamente.");
  const cents = (key) => Math.round(fields[key].valor * 10000);
  if (!missing.length && !ambiguous.length) {
    if (["neto", "iva", "exentos", "total_documento"].some((key) => !Number.isInteger(fields[key].valor))) {
      warnings.push("Los resúmenes deben estar expresados en pesos enteros para esta importación. Revisa manualmente los decimales y su redondeo.");
    }
    if (cents("administracion") + cents("electricidad") + cents("transporte") !== cents("neto")) {
      warnings.push("El neto no coincide con los cargos reconocidos. Puede haber potencia, descuentos u otros conceptos que debas revisar manualmente.");
    }
    if (Math.floor((Math.floor(fields.neto.valor + 0.5) * 19 + 50) / 100) !== fields.iva.valor) {
      warnings.push("El IVA detectado no coincide con el 19 % del neto. Revisa base y redondeo.");
    }
    if (fields.neto.valor + fields.iva.valor + fields.exentos.valor !== fields.total_documento.valor) {
      warnings.push("Neto, IVA y exentos no reconstruyen el total. Puede haber ajustes o saldos que revisar.");
    }
  }
  return {campos: fields, faltantes: missing, ambiguos: ambiguous, avisos: warnings,
    listo_para_revisar: warnings.length === 0, paginas: pages.length};
}
