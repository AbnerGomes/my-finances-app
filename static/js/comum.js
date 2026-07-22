// ============================================================
// comum.js — usado em todas as telas (cabeçalho, rodapé, tema)
// ============================================================

function filtrarGastos(isCasal) {
  const url = new URL(window.location.href);
  url.searchParams.set("isCasal", isCasal);
  window.location.href = url.toString();
}

function filtrarDespesas(isCasal) {
  const url = new URL(window.location.href);
  url.searchParams.set("isCasal", isCasal);

  // se o mês selecionado no filtro ainda não estiver na URL (ex.: acabou
  // de carregar a página sem escolher nada), usa o valor atual do input
  const filtroMes = document.getElementById("filtroMes");
  if (filtroMes && filtroMes.value && !url.searchParams.get("mes_ano")) {
    url.searchParams.set("mes_ano", filtroMes.value);
  }

  window.location.href = url.toString();
}

function filtrarReceitas(isCasal) {
  const url = new URL(window.location.href);
  url.searchParams.set("isCasal", isCasal);
  window.location.href = url.toString();
}

// ============================================================
// Persistência do modo Individual/Casal entre as telas
// ============================================================
const MODO_STORAGE_KEY = "isCasalModo";

function getModoSalvo() {
  return localStorage.getItem(MODO_STORAGE_KEY) || "N";
}

function salvarModo(isCasal) {
  localStorage.setItem(MODO_STORAGE_KEY, isCasal);
}

// Se a tela atual já indica (via atributos no <body>) qual isCasal foi
// renderizado pelo servidor e se o usuário tem cônjuge vinculado, garante
// que essa tela reflita o último modo escolhido em qualquer outra tela —
// recarregando com o parâmetro correto quando necessário.
function sincronizarModoNaCarga() {
  const body = document.body;
  const temConjuge = body.dataset.temConjuge === "true";
  const modoRenderizado = body.dataset.isCasal;

  if (modoRenderizado === undefined || !temConjuge) return;

  const modoSalvo = getModoSalvo();
  if (modoSalvo !== modoRenderizado) {
    const url = new URL(window.location.href);
    url.searchParams.set("isCasal", modoSalvo);
    window.location.replace(url.toString());
  }
}

document.addEventListener("DOMContentLoaded", sincronizarModoNaCarga);

function toggleDropdown() {
  const menu = document.getElementById("main-dropdown");
  if (menu) menu.classList.toggle("show");
}

function toggleModeDropdown() {
  const submenu = document.getElementById("mode-dropdown");
  if (submenu) submenu.classList.toggle("show");
}

function toggleThemeDropdown() {
  const dropdown = document.getElementById("theme-dropdown");
  if (dropdown) dropdown.classList.toggle("show");
}

function changeMode(isCasal) {
  salvarModo(isCasal);

  const nomePagina = window.location.pathname.split("/").pop();
  const nomeSemExtensao = nomePagina.split(".")[0];

  if (nomeSemExtensao === "extrato") {
    filtrarGastos(isCasal);
  }
  if (nomeSemExtensao === "despesas") {
    filtrarDespesas(isCasal);
  }
  if (nomeSemExtensao === "receitas") {
    filtrarReceitas(isCasal);
  }

  const userIcon = document.getElementById("user-icon");
  if (userIcon) {
    userIcon.textContent = isCasal === "S" ? "people" : "person";
  }

  const userIcon1 = document.getElementById("user-icon1");
  if (userIcon1) {
    userIcon1.textContent = isCasal === "S" ? "people" : "person";
  }

  document.querySelectorAll(".modo-pill-compacta").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.modo === isCasal);
  });
}

// Fecha os dropdowns ao clicar fora deles
window.onclick = function (event) {
  if (!event.target.closest(".dropdown")) {
    document.getElementById("main-dropdown")?.classList.remove("show");
    document.getElementById("mode-dropdown")?.classList.remove("show");
    document.getElementById("theme-dropdown")?.classList.remove("show");
  }
};

function signOut() {
  window.location.href = `/`;
}

function changeTheme(theme) {
  // Antes isso zerava TODAS as classes do body (document.body.className = "").
  // Agora removemos só as classes "theme-*", preservando qualquer outra
  // classe que a página tenha (ex.: "home-page", usada na nova tela inicial).
  Array.from(document.body.classList)
    .filter((c) => c.startsWith("theme-"))
    .forEach((c) => document.body.classList.remove(c));

  document.body.classList.add(`theme-${theme}`);
  localStorage.setItem("theme", theme);

  if (typeof atualizarTemaGraficos === "function") {
    atualizarTemaGraficos();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const temaSalvo = localStorage.getItem("theme") || "blue";
  changeTheme(temaSalvo);
});

// ============================================================
// Bloqueio visual de ações em gastos/despesas/receitas que não
// pertencem ao usuário logado (aparecem no modo Casal, mas só dá
// pra editar/excluir o que é seu). Os ícones continuam normais —
// só ao passar o mouse ou clicar é que viram um cadeado por um
// instante e mostram um aviso, sem executar a ação de verdade.
// ============================================================
const MENSAGENS_BLOQUEIO = {
  gastos: "Você só pode editar/excluir seus próprios gastos",
  despesas: "Você só pode editar/excluir suas próprias despesas",
  receitas: "Você só pode editar/excluir suas próprias receitas",
};

function protegerAcoesDeTerceiros() {
  document.querySelectorAll('[data-proprio="false"]').forEach((icone) => {
    if (icone.dataset.bloqueioConfigurado) return;
    icone.dataset.bloqueioConfigurado = "1";

    const classesOriginais = icone.className;
    let timeoutTroca = null;

    const bloquear = (e) => {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }

      icone.className = classesOriginais.replace(/fa-(edit|trash)\b/g, "fa-lock");

      const tipo = icone.dataset.tipoBloqueado || "gastos";
      if (typeof showToast === "function") {
        showToast(MENSAGENS_BLOQUEIO[tipo] || MENSAGENS_BLOQUEIO.gastos, false);
      }

      clearTimeout(timeoutTroca);
      timeoutTroca = setTimeout(() => {
        icone.className = classesOriginais;
      }, 1400);
    };

    icone.addEventListener("mouseenter", bloquear);
    icone.addEventListener("click", bloquear);
  });
}

document.addEventListener("DOMContentLoaded", protegerAcoesDeTerceiros);

// ============================================================
// mensagens flash (ex.: "Você só pode editar seus próprios gastos")
// somem sozinhas depois de alguns segundos, em vez de ficarem
// acumulando na sessão do Flask e aparecendo do nada numa tela
// seguinte que nem tem a ver (ex.: o login)
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash-banner").forEach((banner) => {
    setTimeout(() => {
      banner.classList.add("flash-saindo");
      banner.addEventListener("transitionend", () => banner.remove(), { once: true });
    }, 3000);
  });
});