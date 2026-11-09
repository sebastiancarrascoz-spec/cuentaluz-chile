import test from 'node:test';import assert from 'node:assert/strict';
import {analizarMetadatos} from '../static/js/invoice_metadata.mjs';
const doc=`ENEL DISTRIBUCIÓN CHILE S.A.\nTarifa: BT1 AREA 1 A (a)\nElectricidad consumida (145kWh) 26.300\nComuna: Macul\nLectura anterior: 23/09/2026\nLectura actual: 21/10/2026\nRUT: 11.111.111-1\nCliente: Persona Privada\nDirección: Calle Privada 123`;
test('Extrae solo datos eléctricos expresos y no deduce red o ETR',()=>{
 const r=analizarMetadatos([{numero:1,texto:doc}],['Macul']);
 assert.equal(r.campos.kwh.valor,145);assert.equal(r.campos.tarifa.valor,'BT1');assert.equal(r.campos.comuna.valor,'Macul');
 assert.equal(r.campos.lectura_anterior.valor,'2026-09-23');assert.equal(r.campos.distribuidora.valor,'ENEL');
 assert.equal(r.campos.red,undefined);assert.equal(r.campos.etr,undefined);
 assert.ok(!JSON.stringify(r).includes('Persona Privada')&&!JSON.stringify(r).includes('11.111'));
});
test('No revela una comuna desconocida ni convierte una dirección en comuna',()=>{
 const r=analizarMetadatos([{numero:1,texto:'Comuna: Calle Privada\nDirección: Macul'}],['Macul']);assert.equal(r.campos.comuna,undefined);
});
test('Conserva contradicciones y fechas imposibles como pendientes',()=>{
 const r=analizarMetadatos([{numero:1,texto:'Consumo total: 145 kWh\nConsumo total: 146 kWh\nLectura anterior: 31/02/2026\nLectura actual: 20/01/2026'}]);
 assert.ok(r.ambiguos.includes('kwh'));assert.equal(r.campos.kwh,undefined);assert.equal(r.campos.lectura_anterior,undefined);
 const backwards=analizarMetadatos([{numero:1,texto:'Lectura anterior: 21/10/2026\nLectura actual: 20/10/2026'}]);assert.ok(backwards.ambiguos.includes('periodo'));
});
test('Red y ETR se aceptan únicamente cuando están expresos',()=>{
 const r=analizarMetadatos([{numero:2,texto:'Tipo de red: BT_AS\nTramo ETR: T2\nEmpresa emisora: FRONTEL\nOpción tarifaria: BT4.3'}]);
 assert.equal(r.campos.red.valor,'BT_AS');assert.equal(r.campos.etr.valor,'T2');assert.equal(r.campos.tarifa.valor,'BT4.3');assert.equal(r.campos.distribuidora.valor,'FRONTEL');
});
test('Consumo cero y miles chilenos sin confundir precios por kWh',()=>{
 assert.equal(analizarMetadatos([{numero:1,texto:'Consumo total: 0 kWh'}]).campos.kwh.valor,0);
 assert.equal(analizarMetadatos([{numero:1,texto:'Consumo del mes: 1.234,5 kWh'}]).campos.kwh.valor,1234.5);
 assert.equal(analizarMetadatos([{numero:1,texto:'Cargo por energía ($/kWh) 136,169'}]).campos.kwh,undefined);
});
