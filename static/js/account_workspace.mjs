import {readRecords,makeRecord,saveRecord,removeRecord,allowedField} from "/static/js/scenario_store.mjs";
const $=(id)=>document.getElementById(id), form=$("account-form"), status=$("escenarios-estado");
const money=(n)=>new Intl.NumberFormat("es-CL",{style:"currency",currency:"CLP",maximumFractionDigits:0}).format(n);
let records=[];
function message(text){status.textContent=text;}
function fail(error){message(error.message==="limite"?"Puedes guardar hasta diez escenarios. Elimina uno antes de guardar otro.":"No se pudo acceder al almacenamiento local. El cálculo sigue disponible; revisa la configuración del navegador.");}
function fill(record){
  for(const control of form.elements)if(control.name?.includes("respaldo"))control.value="";
  for(const [name,value] of Object.entries(record.fields)){
    if(!allowedField(name))continue;
    const control=form.elements.namedItem(name);if(control&&"value"in control)control.value=value;
  }
  message("Datos restaurados. Completa otra vez los respaldos y vuelve a calcular; los textos libres no se guardaron.");
  $("guardar-escenario")?.setAttribute("disabled","");
  form.scrollIntoView({behavior:"smooth",block:"start"});
}
function load(record){
  const current=form.elements.namedItem("datos_demanda");
  if(!record.fields.datos_demanda&&current){sessionStorage.setItem("cuentaluz.restaurar.v1",record.id);window.location.assign("/cuenta");return;}
  if(record.fields.datos_demanda&&record.fields.tipo_demanda&&(!current||current.value!==record.fields.datos_demanda||form.elements.namedItem("tipo_demanda")?.value!==record.fields.tipo_demanda)){
    sessionStorage.setItem("cuentaluz.restaurar.v1",record.id);
    const transfer=document.createElement("form");transfer.method="post";transfer.action="/cuenta/preparar-demanda";
    for(const key of ["tipo_demanda","datos_demanda"]){const input=document.createElement("input");input.type="hidden";input.name=key;input.value=record.fields[key];transfer.append(input);}
    document.body.append(transfer);transfer.submit();return;
  }
  fill(record);
}
function render(){
  records=readRecords(localStorage);$("escenarios-lista").replaceChildren();
  for(const select of [$("comparar-anterior"),$("comparar-actual")])select.replaceChildren(new Option("Selecciona un escenario",""));
  for(const r of records){
    const text=`${r.input.periodo.lectura_actual} · ${r.input.periodo.kwh} kWh · ${money(r.total)}`;
    const li=document.createElement("li"),label=document.createElement("span"),loadButton=document.createElement("button"),remove=document.createElement("button");
    label.textContent=text;loadButton.type=remove.type="button";loadButton.className=remove.className="button secondary";
    loadButton.textContent="Cargar valores";remove.textContent="Eliminar";
    loadButton.addEventListener("click",()=>{try{load(r);}catch(e){fail(e);}});
    remove.addEventListener("click",()=>{try{removeRecord(localStorage,r.id);render();message("Escenario eliminado de este navegador.");}catch(e){fail(e);}});
    li.append(label,loadButton,remove);$("escenarios-lista").append(li);
    $("comparar-anterior").add(new Option(text,r.id));$("comparar-actual").add(new Option(text,r.id));
  }
  $("escenarios-contenido").hidden=false;message(`${records.length} escenarios guardados en este navegador.`);
}
$("ver-escenarios")?.addEventListener("click",()=>{try{render();}catch(e){fail(e);}});
const snapshotElement=$("cuenta-snapshot");
if(snapshotElement){
  const snapshot=JSON.parse(snapshotElement.textContent),fields=Object.fromEntries(new FormData(form));
  const button=$("guardar-escenario");button.disabled=false;
  button.addEventListener("click",()=>{try{saveRecord(localStorage,makeRecord(snapshot,fields,crypto.randomUUID(),new Date().toISOString()));render();message("Escenario guardado por tu elección. PDF, identidad y textos libres de respaldo no se guardaron.");}catch(e){fail(e);}});
  form.addEventListener("input",()=>{button.disabled=true;message("Modificaste los datos. Vuelve a calcular antes de guardar el resultado.");});
  form.addEventListener("change",()=>{button.disabled=true;});
}
try{
  const pending=sessionStorage.getItem("cuentaluz.restaurar.v1");
  if(pending){sessionStorage.removeItem("cuentaluz.restaurar.v1");const r=readRecords(localStorage).find(r=>r.id===pending);if(r)fill(r);}
}catch(e){fail(e);}
$("comparar-guardados")?.addEventListener("click",async()=>{
  const a=records.find(r=>r.id===$("comparar-anterior").value),b=records.find(r=>r.id===$("comparar-actual").value);
  if(!a||!b||a.id===b.id){message("Selecciona dos escenarios distintos.");return;}
  try{
    const response=await fetch("/api/comparar-guardados",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({anterior:a.input,actual:b.input})});
    if(!response.ok)throw new Error("comparacion");
    const result=await response.json(),box=$("comparacion-guardados");box.replaceChildren();
    const title=document.createElement("h3");title.textContent="Comparación recalculada";box.append(title);
    const p=document.createElement("p");p.textContent=`Total anterior: ${money(result.anterior_total)}. Actual: ${money(result.actual_total)}. Diferencia: ${money(result.diferencia_total)}. Consumo diario: ${result.anterior_kwh_dia} → ${result.actual_kwh_dia} kWh/día.`;box.append(p);
    if(result.descomposicion){
      const d=result.descomposicion;for(const [label,value] of [["Efecto del consumo",d.efecto_consumo],["Efecto del precio medio declarado",d.efecto_precio_medio],["Otros cargos, impuestos y redondeos",d.otros_cargos_impuestos_y_redondeos]]){const line=document.createElement("p");line.textContent=`${label}: ${money(value)}`;box.append(line);}
      const method=document.createElement("p");method.textContent=d.metodo;box.append(method);
    }
    const note=document.createElement("p");note.textContent=result.alcance;box.append(note);
  }catch(e){message("No se pudo comparar. Revisa los datos guardados; un registro incompleto o alterado requiere reconstruir el escenario.");}
});
let opened=[];
function preparePrint(){if(document.body.classList.contains("printing-account"))return;document.body.classList.add("printing-account");opened=Array.from($("informe-cuenta")?.querySelectorAll("details")||[]).map(e=>[e,e.open]);for(const [e]of opened)e.open=true;}
function finishPrint(){document.body.classList.remove("printing-account");for(const [e,wasOpen]of opened)e.open=wasOpen;opened=[];}
window.addEventListener("beforeprint",preparePrint);window.addEventListener("afterprint",finishPrint);
$("imprimir-cuenta")?.addEventListener("click",()=>{preparePrint();window.print();});
