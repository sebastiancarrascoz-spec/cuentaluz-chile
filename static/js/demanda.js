"use strict";
document.getElementById("actualizar-meses").addEventListener("click", () => {
  const value = document.getElementById("mes_facturacion").value;
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) return;
  const [year, month] = value.split("-").map(Number);
  const cards = document.querySelectorAll("#historial-demanda > section");
  cards.forEach((card, index) => {
    const d = new Date(0);
    d.setUTCFullYear(year, month - cards.length + index, 1);
    const m = d.toISOString().slice(0, 7);
    const old = card.querySelector("h3").textContent;
    card.querySelector("h3").textContent = m;
    card.querySelectorAll("input").forEach((input) => {
      const oldId = input.id;
      input.name = input.name.replace(old, m);
      if (oldId) {
        input.id = oldId.replace(old, m);
        card.querySelector(`label[for="${oldId}"]`).htmlFor = input.id;
      }
      if (input.type === "checkbox") input.checked = false;
      else input.value = "";
    });
  });
  const previousPeak = document.getElementById("meses_punta_anterior");
  if (previousPeak) previousPeak.value = "";
  const observed = document.getElementById("cargo_observado_neto");
  if (observed) observed.value = "";
});
