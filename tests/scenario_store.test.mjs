import test from 'node:test';import assert from 'node:assert/strict';
import {makeRecord,readRecords,saveRecord,removeRecord,STORE_KEY} from '../static/js/scenario_store.mjs';
const storage=()=>{const m=new Map();return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,v)};};
const snapshot={entrada:{respaldo_precios:'Texto privado',periodo:{kwh:'100',lectura_actual:'2026-11-30'},adicionales:{demanda:{respaldo:'Otro privado'}}},resultado:{total:13785}};
test('Guardar requiere una acción y elimina textos libres y campos desconocidos',()=>{
 const s=storage();assert.deepEqual(readRecords(s),[]);
 const r=makeRecord(snapshot,{kwh:'100',respaldo_precios:'Texto privado',demanda_respaldo:'Otro privado',direccion:'Calle privada',obs_total:'13785'},'1','2026-11-09');
 assert.ok(!JSON.stringify(r).includes('Texto privado')&&!JSON.stringify(r).includes('Calle privada')&&!JSON.stringify(r).includes('Otro privado'));
 assert.deepEqual(Object.keys(r.fields),['kwh','obs_total']);assert.deepEqual(readRecords(s),[]);
 saveRecord(s,r);assert.equal(readRecords(s).length,1);removeRecord(s,'1');assert.deepEqual(readRecords(s),[]);
});
test('Límite de diez no elimina registros anteriores por su cuenta',()=>{
 const s=storage();for(let i=0;i<10;i++)saveRecord(s,makeRecord(snapshot,{kwh:'100'},String(i),'2026-11-09'));
 assert.throws(()=>saveRecord(s,makeRecord(snapshot,{},'11','2026-11-09')),/limite/);assert.equal(readRecords(s).length,10);
});
test('Almacenamiento alterado o excesivo se rechaza sin ejecutarlo',()=>{
 const s=storage();s.setItem(STORE_KEY,'{invalid');assert.throws(()=>readRecords(s));
 s.setItem(STORE_KEY,JSON.stringify([{version:1,id:'x',input:{periodo:{}},fields:{respaldo_precios:'no permitido'},total:1}]));assert.throws(()=>readRecords(s));
 s.setItem(STORE_KEY,'x'.repeat(250001));assert.throws(()=>readRecords(s));
});
