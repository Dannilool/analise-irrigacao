/* ==========================================================================
   Dashboard de Irrigação — interações
   ========================================================================== */
(() => {
  "use strict";

  const form = document.getElementById("prediction-form");
  const input = document.getElementById("horas");
  const range = document.getElementById("horas-range");
  const quickButtons = Array.from(document.querySelectorAll("[data-hours]"));
  const resultAngle = document.getElementById("result-angle");
  const resultArea = document.getElementById("result-area");
  const resultHours = document.getElementById("result-hours");
  const resultStatus = document.getElementById("result-status");
  const resultStatusText = document.getElementById("result-status-text");
  const resultTime = document.getElementById("result-time");
  const toast = document.getElementById("toast");

  const numero = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  let ultimaRequisicao = 0;
  let timerRange = null;
  let timerToast = null;

  function mostrarToast(mensagem) {
    if (!toast) return;
    toast.textContent = mensagem;
    toast.classList.add("is-visible");
    window.clearTimeout(timerToast);
    timerToast = window.setTimeout(() => {
      toast.classList.remove("is-visible");
    }, 2200);
  }

  function pintarRange() {
    if (!range) return;
    const min = Number(range.min);
    const max = Number(range.max);
    const valor = Math.min(Math.max(Number(range.value), min), max);
    const percentual = ((valor - min) / (max - min)) * 100;
    range.style.background = `linear-gradient(to right, var(--teal-600) 0%, var(--teal-600) ${percentual}%, #dce7e4 ${percentual}%, #dce7e4 100%)`;
  }

  function marcarRapido(horas) {
    quickButtons.forEach((botao) => {
      botao.classList.toggle("is-active", Number(botao.dataset.hours) === Number(horas));
    });
  }

  function definirStatus(estado, texto) {
    if (!resultStatus || !resultStatusText) return;
    resultStatus.classList.remove("is-error", "is-loading");
    if (estado === "error") resultStatus.classList.add("is-error");
    if (estado === "loading") resultStatus.classList.add("is-loading");
    resultStatusText.textContent = texto;
  }

  function atualizarResultado(dados) {
    if (!dados) return;
    if (resultAngle) resultAngle.textContent = numero.format(Number(dados.area_angulo_prevista));
    if (resultArea) resultArea.textContent = numero.format(Number(dados.area_total_estimada));
    if (resultHours) resultHours.textContent = `${numero.format(Number(dados.horas))} h`;
    if (resultTime) resultTime.textContent = "agora";
    definirStatus("ok", "Previsão calculada pela API · modelo carregado");
  }

  async function prever(horas) {
    const requisicao = ++ultimaRequisicao;
    definirStatus("loading", "Consultando o modelo...");

    try {
      const resposta = await fetch("/api/prever", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ horas: Number(horas) }),
      });

      if (!resposta.ok) {
        let detalhe = `Erro ${resposta.status}`;
        try {
          const corpo = await resposta.json();
          if (typeof corpo.detail === "string") detalhe = corpo.detail;
          if (Array.isArray(corpo.detail) && corpo.detail[0]?.msg) detalhe = corpo.detail[0].msg;
        } catch (_) {
          /* mantém a mensagem padrão */
        }
        throw new Error(detalhe);
      }

      const dados = await resposta.json();
      if (requisicao !== ultimaRequisicao) return;
      atualizarResultado(dados);
    } catch (erro) {
      if (requisicao !== ultimaRequisicao) return;
      definirStatus("error", "Não foi possível calcular. Verifique a API e tente novamente.");
      mostrarToast(erro instanceof Error ? erro.message : "Falha na previsão.");
    }
  }

  function sincronizarEntrada(origem) {
    const horas = Number(input?.value ?? 15);

    if (Number.isFinite(horas) && range) {
      if (horas >= Number(range.min) && horas <= Number(range.max)) {
        range.value = String(horas);
      } else if (origem === "input" && horas > Number(range.max)) {
        range.value = range.max;
      }
      pintarRange();
    }

    marcarRapido(horas);
  }

  form?.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const horas = Number(input?.value);

    if (!Number.isFinite(horas) || horas < 0 || horas > 1000) {
      mostrarToast("Informe um valor entre 0 e 1.000 horas.");
      input?.focus();
      return;
    }

    sincronizarEntrada("submit");
    prever(horas);
  });

  range?.addEventListener("input", () => {
    const horas = Number(range.value);
    if (input) input.value = String(horas);
    pintarRange();
    marcarRapido(horas);
    window.clearTimeout(timerRange);
    timerRange = window.setTimeout(() => prever(horas), 140);
  });

  input?.addEventListener("input", () => {
    sincronizarEntrada("input");
  });

  quickButtons.forEach((botao) => {
    botao.addEventListener("click", () => {
      const horas = Number(botao.dataset.hours);
      if (input) input.value = String(horas);
      sincronizarEntrada("quick");
      prever(horas);
    });
  });

  // Copiar equação
  const copyButton = document.getElementById("copy-equation");
  copyButton?.addEventListener("click", async () => {
    const equacao = copyButton.dataset.equation || "";
    try {
      await navigator.clipboard.writeText(equacao);
      mostrarToast("Equação copiada.");
    } catch (_) {
      mostrarToast("Não foi possível copiar automaticamente.");
    }
  });

  // Lightbox das figuras
  const lightbox = document.getElementById("lightbox");
  const lightboxImage = document.getElementById("lightbox-image");
  const lightboxTitle = document.getElementById("lightbox-title");
  const lightboxClose = document.getElementById("lightbox-close");
  const figureButtons = Array.from(document.querySelectorAll(".figure-button"));
  let elementoAnterior = null;

  function abrirLightbox(botao) {
    if (!lightbox || !lightboxImage || !lightboxTitle) return;
    elementoAnterior = botao;
    lightboxImage.src = botao.dataset.src || "";
    lightboxImage.alt = botao.dataset.title || "Figura ampliada";
    lightboxTitle.textContent = botao.dataset.title || "";
    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
    lightboxClose?.focus();
  }

  function fecharLightbox() {
    if (!lightbox || lightbox.hidden) return;
    lightbox.hidden = true;
    lightboxImage.src = "";
    document.body.style.overflow = "";
    elementoAnterior?.focus();
  }

  figureButtons.forEach((botao) => {
    botao.addEventListener("click", () => abrirLightbox(botao));
  });

  lightboxClose?.addEventListener("click", fecharLightbox);
  lightbox?.addEventListener("click", (evento) => {
    if (evento.target === lightbox) fecharLightbox();
  });

  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") fecharLightbox();
  });

  // Ano do rodapé
  const ano = document.getElementById("ano");
  if (ano) ano.textContent = String(new Date().getFullYear());

  // Estado inicial
  sincronizarEntrada("inicial");
})();
