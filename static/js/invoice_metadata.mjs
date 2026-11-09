// Solo datos eléctricos permitidos; nunca dirección, RUT, cliente o texto completo.
const number=String.raw`((?:\d{1,3}(?:\.\d{3})+|\d{1,10})(?:,\d{1,4})?)`;
const dateToken=String.raw`(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})`;
function isoDate(raw){
  const a=raw.split(/[/-]/).map(Number),[y,m,d]=a[0]>999?a:[a[2],a[1],a[0]];
  if(y<2000||y>2099)return null;
  const day=new Date(Date.UTC(y,m-1,d));
  return day.getUTCFullYear()===y&&day.getUTCMonth()===m-1&&day.getUTCDate()===d?`${y}-${String(m).padStart(2,"0")}-${String(d).padStart(2,"0")}`:null;
}
export function analizarMetadatos(pages,comunas=[]){
  if(!Array.isArray(pages)||!pages.length||pages.length>12)throw new Error("paginas");
  const names=new Map(comunas.filter(v=>typeof v==="string").map(v=>[v.normalize("NFD").replace(/\p{M}/gu,"").toLowerCase(),v]));
  const found={};let length=0;
  const add=(key,value,page)=>{if(value!==null&&value!==undefined)(found[key]??=[]).push({valor:value,pagina:page});};
  for(const p of pages){
    if(typeof p.texto!=="string"||!Number.isInteger(p.numero)||p.numero<1||p.numero>12)throw new Error("paginas");
    length+=p.texto.length;if(length>200000)throw new Error("texto_largo");
    const text=p.texto.normalize("NFC").replaceAll("\r", "\n").replaceAll("\u00a0"," ");
    for(const m of text.matchAll(new RegExp(String.raw`(?:^|\n)[ \t]*(?:Consumo\s+(?:total|del\s+mes)|Energ[ií]a\s+consumida)[ \t]*(?:\(kWh\))?[ \t:]*\n?[ \t]*${number}[ \t]*(?:kWh)?[ \t]*(?=\n|$)`,"gimu")))add("kwh",Number(m[1].replaceAll(".","").replace(",",".")),p.numero);
    for(const m of text.matchAll(new RegExp(String.raw`Electricidad\s+consumida\s*\(\s*${number}\s*kWh\s*\)`,"gimu")))add("kwh",Number(m[1].replaceAll(".","").replace(",",".")),p.numero);
    for(const m of text.matchAll(/(?:^|\n)[ \t]*(?:Opci[oó]n\s+tarifaria|Tarifa)[ \t:]+((?:TRBT|TRAT|BT|AT)\s*[1-6]?(?:\.[1-3])?)(?=[ \t(\n]|$)/gimu))add("tarifa",m[1].replaceAll(" ","").toUpperCase(),p.numero);
    for(const [key,label]of [["lectura_anterior","(?:Fecha\\s+de\\s+)?[Ll]ectura\\s+anterior"],["lectura_actual","(?:Fecha\\s+de\\s+)?[Ll]ectura\\s+actual"]]){
      for(const m of text.matchAll(new RegExp(String.raw`(?:^|\n)[ \t]*${label}[ \t:]*\n?[ \t]*${dateToken}[ \t]*(?=\n|$)`,"gimu")))add(key,isoDate(m[1]),p.numero);
    }
    for(const m of text.matchAll(/(?:^|\n)[ \t]*(?:Tipo\s+de\s+red|Red)[ \t:]+(BT_(?:AA|SA|AS|SS))[ \t]*(?=\n|$)/gimu))add("red",m[1].toUpperCase(),p.numero);
    for(const m of text.matchAll(/(?:^|\n)[ \t]*(?:Tramo\s+ETR|ETR)[ \t:]+(T[1-6])[ \t]*(?=\n|$)/gimu))add("etr",m[1].toUpperCase(),p.numero);
    for(const m of text.matchAll(/(?:^|\n)[ \t]*Comuna[ \t:]+([\p{L} .'-]{2,65})[ \t]*(?=\n|$)/gmu)){
      const key=m[1].trim().normalize("NFD").replace(/\p{M}/gu,"").toLowerCase();if(names.has(key))add("comuna",names.get(key),p.numero);
    }
    for(const [id,pattern] of [["ENEL",/^[ \t]*(?:Empresa\s+emisora\s*:\s*)?ENEL\s+DISTRIBUCI[OÓ]N\s+CHILE(?:\s+S\.?A\.?)?[ \t]*$/gimu],["CGE",/^[ \t]*Empresa\s+emisora\s*:\s*CGE(?:\s+DISTRIBUCI[OÓ]N)?[ \t]*$/gimu],["FRONTEL",/^[ \t]*Empresa\s+emisora\s*:\s*FRONTEL[ \t]*$/gimu],["SAESA",/^[ \t]*Empresa\s+emisora\s*:\s*SAESA[ \t]*$/gimu],["CHILQUINTA",/^[ \t]*Empresa\s+emisora\s*:\s*CHILQUINTA[ \t]*$/gimu]])if(pattern.test(text))add("distribuidora",id,p.numero);
  }
  const fields={},ambiguous=[];
  for(const [key,values] of Object.entries(found)){
    const valid=values.filter(v=>key!=="kwh"||(Number.isFinite(v.valor)&&v.valor>=0&&v.valor<=1e9));
    if(new Set(valid.map(v=>v.valor)).size>1)ambiguous.push(key);else if(valid.length)fields[key]=valid[0];
  }
  if(fields.lectura_anterior&&fields.lectura_actual&&fields.lectura_anterior.valor>=fields.lectura_actual.valor){ambiguous.push("periodo");delete fields.lectura_anterior;delete fields.lectura_actual;}
  return {campos:fields,ambiguos:ambiguous,alcance:"Datos expresamente reconocidos para confirmar. No se deduce red ni ETR de AREA 1 A, dirección, consumo actual o coincidencia del total. La ausencia de un campo no impide revisar importes manualmente."};
}
