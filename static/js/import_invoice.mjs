import {analizarPaginas} from "/static/js/invoice_parser.mjs";
const $ = (id) => document.getElementById(id);
let proposal = null;
const names = {administracion:"Administración", electricidad:"Electricidad consumida", transporte:"Transporte",
  servicio_publico:"Servicio público", neto:"Neto afecto", iva:"IVA 19 %", exentos:"Total exento", total_documento:"Total del documento"};
const money = (v) => new Intl.NumberFormat("es-CL", {style:"currency", currency:"CLP", maximumFractionDigits:4}).format(v);

function display(result) {
  proposal = result;
  $("pdf-campos").replaceChildren();
  for (const [key, field] of Object.entries(result.campos)) {
    const row = document.createElement("tr"), label = document.createElement("th"), value = document.createElement("td"), page = document.createElement("td");
    label.scope = "row";
    label.textContent = names[key];
    value.textContent = money(field.valor);
    page.textContent = String(field.pagina);
    row.append(label, value, page);
    $("pdf-campos").append(row);
  }
  $("pdf-avisos").replaceChildren();
  const metaNames={distribuidora:"Distribuidora",tarifa:"Opción tarifaria",comuna:"Comuna",kwh:"Consumo (kWh)",lectura_anterior:"Lectura anterior",lectura_actual:"Lectura actual",red:"Red expresamente informada",etr:"Tramo ETR informado"};
  $("pdf-metadatos").replaceChildren();
  for(const [key,field] of Object.entries(result.metadatos.campos)){
    const li=document.createElement("li");li.textContent=`${metaNames[key]}: ${field.valor} · página ${field.pagina}`;$("pdf-metadatos").append(li);
  }
  for(const key of result.metadatos.ambiguos){const li=document.createElement("li");li.textContent=`Dato ambiguo pendiente: ${metaNames[key]||key}.`;$("pdf-metadatos").append(li);}
  for (const message of result.avisos) {
    const item = document.createElement("li");
    item.textContent = message;
    $("pdf-avisos").append(item);
  }
  $("pdf-usar").disabled = !result.listo_para_revisar;
  $("pdf-propuesta").hidden = false;
  $("pdf-estado").textContent = result.listo_para_revisar
    ? "Lectura terminada. Comprueba los importes y sus páginas antes de usarlos."
    : "La lectura requiere revisión manual. Los campos del conciliador no se han modificado.";
}

$("pdf-archivo").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  proposal = null;
  $("pdf-propuesta").hidden = true;
  $("pdf-usar").disabled = true;
  $("pdf-archivo").disabled = true;
  $("pdf-estado").textContent = "Leyendo el PDF en este equipo…";
  let worker, pdfWorker, document, loading, timeout, cancelled = false;
  try {
    if (file.size > 6 * 1024 * 1024 || file.size === 0) throw new Error("tamano");
    const bytes = new Uint8Array(await file.arrayBuffer());
    if (new TextDecoder().decode(bytes.subarray(0, 5)) !== "%PDF-") throw new Error("formato");
    const run = async () => {
      const pdfjs = await import("/static/vendor/pdfjs/pdf.min.mjs");
      if (cancelled) throw new Error("tiempo");
      worker = new Worker("/static/vendor/pdfjs/pdf.worker.min.mjs", {type:"module"});
      pdfWorker = new pdfjs.PDFWorker({port:worker});
      loading = pdfjs.getDocument({data:bytes, worker:pdfWorker, isEvalSupported:false,
        enableXfa:false, useWasm:false, useWorkerFetch:false, disableFontFace:true, disableWorkerRendering:true,
        stopAtErrors:true, verbosity:0});
      // No se solicitan contraseñas, acciones, vínculos ni adjuntos del PDF.
      loading.onPassword = () => { loading.destroy().catch(() => {}); };
      document = await loading.promise;
      if (document.numPages > 12) throw new Error("paginas");
      const pages = [];
      let length = 0;
      for (let i = 1; i <= document.numPages; i++) {
        if (cancelled) throw new Error("tiempo");
        const page = await document.getPage(i);
        const content = await page.getTextContent();
        let text = "", lastY;
        for (const item of content.items) {
          if (typeof item.str !== "string") continue;
          const y = item.transform?.[5];
          if (lastY !== undefined && Math.abs(y - lastY) > 2) text += "\n";
          text += item.str + (item.hasEOL ? "\n" : " ");
          lastY = y;
        }
        length += text.length;
        if (length > 200000) throw new Error("texto_largo");
        pages.push({numero:i, texto:text});
        page.cleanup();
      }
      if (length < 30) throw new Error("sin_texto");
      return analizarPaginas(pages,JSON.parse($("comunas-lector").textContent));
    };
    const deadline = new Promise((_, reject) => { timeout = setTimeout(() => {
      cancelled = true;
      worker?.terminate();
      reject(new Error("tiempo"));
    }, 12000); });
    display(await Promise.race([run(), deadline]));
  } catch (error) {
    const messages = {tamano:"Elige un PDF de hasta 6 MB.", formato:"El archivo no tiene una cabecera PDF válida.",
      paginas:"La lectura admite hasta 12 páginas.", texto_largo:"El documento contiene demasiado texto para esta lectura.",
      sin_texto:"El PDF parece una imagen o no contiene texto legible. Usa la revisión manual; el OCR no está habilitado.",
      tiempo:"La lectura superó el tiempo máximo. Usa la revisión manual."};
    $("pdf-estado").textContent = messages[error.message] || "No se pudo leer este PDF. Puede estar protegido, dañado o usar un formato no compatible. Usa la revisión manual.";
  } finally {
    clearTimeout(timeout);
    loading?.destroy().catch(() => {});
    pdfWorker?.destroy();
    worker?.terminate();
    $("pdf-archivo").value = "";
    $("pdf-archivo").disabled = false;
  }
});

$("pdf-usar").addEventListener("click", () => {
  if (!proposal?.listo_para_revisar) return;
  for (const key of ["administracion", "electricidad", "transporte", "exentos", "total_documento"]) {
    $(key).value = String(proposal.campos[key].valor);
  }
  // Se reemplaza el escenario completo después de la confirmación explícita.
  $("potencia").value = "0";
  $("otros").value = "0";
  $("ajustes_finales").value = "0";
  for(const key of ["kwh","lectura_anterior","lectura_actual"]){const target=$("dato_"+key);if(target)target.value=proposal.metadatos.campos[key]?.valor??"";}
  $("pdf-estado").textContent = "Importes copiados al formulario. Revísalos y pulsa «Comprobar el total» cuando estén correctos.";
  $("electricidad").focus();
});

$("continuar-escenario").addEventListener("click",()=>{
  const form=document.createElement("form");form.method="post";form.action="/cuenta/desde-revision";
  for(const [name,id] of [["electricidad","electricidad"],["transporte","transporte"],["administracion","administracion"],["exentos","exentos"],["total","total_documento"],["kwh","dato_kwh"],["lectura_anterior","dato_lectura_anterior"],["lectura_actual","dato_lectura_actual"]]){
    const value=$(id).value;if(!value)continue;
    if(!name.startsWith("lectura")&&name!=="kwh"&&!/^\d+$/.test(value)){ $("pdf-estado").textContent="El contraste por cargo requiere pesos enteros. Revisa los importes sin redondearlos para forzar un resultado.";return; }
    const input=document.createElement("input");input.type="hidden";input.name=name;input.value=value;form.append(input);
  }
  document.body.append(form);form.submit();
});
