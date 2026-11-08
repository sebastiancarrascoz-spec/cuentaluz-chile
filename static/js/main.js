"use strict";
const $ = (id) => document.getElementById(id);
const money = (n) =>
  new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(n);
const form = $("calculator-form");
if (form) {
  const setMode = (mode) => {
    $("modo").value = mode;
    $("panel-kwh").hidden = mode !== "kwh";
    $("panel-aparatos").hidden = mode !== "aparatos";
    $("kwh_directo").required = mode === "kwh";
    $("kwh_directo").disabled = mode !== "kwh";
    document
      .querySelectorAll("[data-mode]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.mode === mode)),
      );
    document.querySelectorAll(".appliance-row").forEach((row) => {
      row.querySelector("[type=number]").disabled =
        mode !== "aparatos" || !row.querySelector("[type=checkbox]").checked;
    });
  };
  document
    .querySelectorAll("[data-mode]")
    .forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  setMode($("modo").value === "aparatos" ? "aparatos" : "kwh");
  document.querySelectorAll("[data-kwh]").forEach((b) =>
    b.addEventListener("click", () => {
      $("kwh_directo").value = b.dataset.kwh;
    }),
  );
  const setPrices = () => {
    const custom = $("fuente").value === "personalizada";
    $("custom-prices").hidden = !custom;
    $("reference-notice").hidden = custom;
    ["precio_kwh", "cargo_fijo"].forEach((id) => {
      $(id).required = custom;
      $(id).disabled = !custom;
    });
  };
  $("fuente").addEventListener("change", setPrices);
  setPrices();
  const appliances = () => {
    let total = 0;
    document.querySelectorAll(".appliance-row").forEach((row) => {
      const check = row.querySelector("[type=checkbox]"),
        hours = row.querySelector("[type=number]");
      hours.disabled = !check.checked || $("modo").value !== "aparatos";
      if (check.checked)
        total +=
          (Number(check.dataset.watts) / 1000) *
          Number(hours.value) *
          Number($("dias").value);
    });
    $("appliance-kwh").textContent =
      new Intl.NumberFormat("es-CL", { maximumFractionDigits: 1 }).format(
        total,
      ) + " kWh";
  };
  form.addEventListener("input", appliances);
  appliances();
  form.addEventListener("submit", () => {
    const b = form.querySelector("[type=submit]");
    b.disabled = true;
    b.textContent = "Preparando tu estimación…";
  });
  window.addEventListener("pageshow", () => {
    const b = form.querySelector("[type=submit]");
    b.disabled = false;
    b.textContent = "Entender mi cuenta ↗";
  });
  $("form-error")?.focus();
}

const search = $("buscar-comuna");
if (search) {
  const normalize = (s) =>
    s
      .toLocaleLowerCase("es")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  search.addEventListener("input", () => {
    let count = 0;
    const q = normalize(search.value.trim());
    document.querySelectorAll(".comuna-tag").forEach((tag) => {
      tag.hidden = !normalize(tag.dataset.nombre).includes(q);
      if (!tag.hidden) count++;
    });
    document.querySelectorAll(".dist-card").forEach((card) => {
      card.hidden = ![...card.querySelectorAll(".comuna-tag")].some(
        (t) => !t.hidden,
      );
    });
    $("search-count").textContent =
      count + " coincidencias en el directorio nacional";
    $("search-empty").hidden = count > 0;
  });
}

const dataElement = $("estimate-data");
if (dataElement) {
  const result = JSON.parse(dataElement.textContent);
  $("print-result").addEventListener("click", () => {
    document.querySelector(".calculation-details").open = true;
    window.print();
  });
  $("export-csv").addEventListener("click", () => {
    const rows = [
      ["CuentaLuz Chile", "Estimación referencial"],
      ["Fecha", result.fecha],
      ["Distribuidora", result.distribuidora],
      ["Base", result.entrada.fuente],
      ["Consumo (kWh)", result.entrada.kwh],
      ["Días", result.entrada.dias],
      [
        "Boleta informada (CLP)",
        result.entrada.boleta_actual ?? "No informada",
      ],
      [
        "Precio personalizado ($/kWh)",
        result.entrada.precio_kwh ?? "No aplica",
      ],
      [
        "Cargo fijo personalizado ($)",
        result.entrada.cargo_fijo ?? "No aplica",
      ],
      [
        "Fuente",
        result.entrada.fuente === "referencia"
          ? result.tarifa.fuente
          : "Precios ingresados por el usuario",
      ],
      [
        "Vigente desde",
        result.entrada.fuente === "referencia"
          ? result.tarifa.vigente_desde
          : "No aplica",
      ],
      [
        "Vigente hasta",
        result.entrada.fuente === "referencia"
          ? result.tarifa.vigente_hasta
          : "No aplica",
      ],
      ["Componente", "Importe final CLP"],
      ...result.componentes.map((c) => [c.nombre, c.valor]),
      ["Total", result.total],
      ["Metodología", result.metodologia],
      [
        "Alcance",
        "No incluye saldos anteriores, subsidios ni otros ajustes particulares.",
      ],
      ["Reducción de consumo (%)", "Nuevo total CLP", "Ahorro CLP"],
      ...result.escenarios.map((e) => [e.reduccion, e.total, e.ahorro]),
    ];
    const csv =
      "\ufeff" +
      rows
        .map((r) =>
          r
            .map((v) => '"' + String(v ?? "").replaceAll('"', '""') + '"')
            .join(";"),
        )
        .join("\r\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8;" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "CuentaLuz-" + result.fecha + ".csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  let timer,
    controller,
    sequence = 0;
  $("saving-slider").addEventListener("input", () => {
    const reduction = Number($("saving-slider").value);
    $("saving-percent").textContent = reduction + " %";
    $("saving-total").textContent = "Calculando…";
    $("saving-error").hidden = true;
    clearTimeout(timer);
    controller?.abort();
    const current = ++sequence;
    timer = setTimeout(async () => {
      controller = new AbortController();
      try {
        const response = await fetch("/api/estimar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...result.entrada,
            kwh: result.entrada.kwh * (1 - reduction / 100),
          }),
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("estimate");
        const next = await response.json();
        if (current !== sequence) return;
        $("saving-total").textContent = money(next.total);
        $("saving-detail").textContent =
          new Intl.NumberFormat("es-CL", { maximumFractionDigits: 1 }).format(
            next.entrada.kwh,
          ) +
          " kWh · ahorro de " +
          money(result.total - next.total);
      } catch (error) {
        if (error.name !== "AbortError" && current === sequence) {
          $("saving-total").textContent = "—";
          $("saving-error").textContent =
            "No pudimos actualizar el escenario. Mueve el control para reintentar.";
          $("saving-error").hidden = false;
        }
      }
    }, 250);
  });
}
