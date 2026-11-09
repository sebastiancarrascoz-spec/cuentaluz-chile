import test from "node:test";
import assert from "node:assert/strict";
import {analizarPaginas} from "../static/js/invoice_parser.mjs";

const page = `Administración del servicio 614
Electricidad Consumida (145kWh) 26.300
Cargo por Servicio Público 124
Transporte de electricidad 2.497
Total Monto Neto 29.411
Total I.V.A. (19%) 5.588
Monto Exento 124
Monto Total 35.123`;

test("Reconoce importes netos y no suma dos veces el servicio público", () => {
  const r = analizarPaginas([{numero:1,texto:page}]);
  assert.equal(r.campos.total_documento.valor,35123);
  assert.equal(r.campos.exentos.valor,124);
  assert.equal(r.campos.electricidad.valor,26300);
  assert.equal(r.listo_para_revisar,true);
});
test("Acepta valores en renglón siguiente y mantiene su página", () => {
  const r = analizarPaginas([{numero:2,texto:page.replaceAll(" 614","\n614")}]);
  assert.equal(r.campos.administracion.pagina,2);
  assert.equal(r.listo_para_revisar,true);
});
test("No escoge entre dos importes contradictorios", () => {
  const r = analizarPaginas([{numero:1,texto:page}, {numero:2,texto:"Monto Total 40.000"}]);
  assert.deepEqual(r.ambiguos,["total_documento"]);
  assert.equal(r.listo_para_revisar,false);
});
test("Un encabezado repetido con el mismo importe no duplica el cargo", () => {
  const r = analizarPaginas([{numero:1,texto:page}, {numero:2,texto:"Monto Total 35.123"}]);
  assert.equal(r.listo_para_revisar,true);
  assert.equal(r.campos.total_documento.valor,35123);
});
test("No completa cargos faltantes ni equilibra mediante otros cargos", () => {
  const r = analizarPaginas([{numero:1,texto:page.replace("26.300","20.000")}]);
  assert.equal(r.listo_para_revisar,false);
  assert.ok(r.avisos.some((s)=>s.includes("neto no coincide")));
});
test("No interpreta importes finales sin neto e IVA desglosados", () => {
  const r = analizarPaginas([{numero:1,texto:page.replace("Total Monto Neto 29.411","").replace("Total I.V.A. (19%) 5.588","")}]);
  assert.equal(r.listo_para_revisar,false);
  assert.ok(r.faltantes.includes("neto"));
});
test("Un cero explícito se conserva y un encabezado vacío no se vuelve cero", () => {
  const r = analizarPaginas([{numero:1,texto:"Monto Exento 0\nMonto Total"}]);
  assert.equal(r.campos.exentos.valor,0);
  assert.ok(r.faltantes.includes("total_documento"));
});
test("No devuelve datos personales ni ejecuta texto del documento", () => {
  const r = analizarPaginas([{numero:1,texto:page+"\nCLIENTE PRIVADO\n<script>alert(1)</script>"}]);
  assert.ok(!JSON.stringify(r).includes("CLIENTE PRIVADO"));
  assert.ok(!JSON.stringify(r).includes("script"));
});
test("Rechaza texto excesivo y documentos demasiado largos", () => {
  assert.throws(()=>analizarPaginas([{numero:1,texto:"x".repeat(200001)}]));
  assert.throws(()=>analizarPaginas(Array(13).fill({numero:1,texto:page})));
});
test("No importa resúmenes decimales que puedan cambiar al redondear en el conciliador", () => {
  const text = page.replace("614","0").replace("26.300","0,5").replace("2.497","0")
    .replace("29.411","0,5").replace("5.588","0").replaceAll("124","0,5").replace("35.123","1");
  assert.equal(analizarPaginas([{numero:1,texto:text}]).listo_para_revisar,false);
});
