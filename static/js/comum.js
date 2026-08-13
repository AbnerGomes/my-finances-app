// ============================================================
// comum.js — usado em todas as telas (cabeçalho, rodapé, tema)
// ============================================================

// ============================================================
// Botão de voltar (◄) no cabeçalho, discreto, do lado esquerdo do
// logo — chama o histórico do navegador. Não aparece na tela inicial
// (não faz sentido "voltar" da home) nem quando não há pra onde
// voltar (primeira página aberta pelo app).
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  const logoText = document.querySelector('.logo-text');
  const ehHome = document.body.classList.contains('home-page');
  if (!logoText || ehHome || window.history.length <= 1) return;

  const botaoVoltar = document.createElement('button');
  botaoVoltar.type = 'button';
  botaoVoltar.className = 'botao-voltar';
  botaoVoltar.setAttribute('aria-label', 'Voltar');
  botaoVoltar.innerHTML = '<span class="material-icons">chevron_left</span>';
  botaoVoltar.addEventListener('click', () => history.back());

  logoText.prepend(botaoVoltar);
});

// ============================================================
// Seletor de data único (calendário via Litepicker) usado nos modais
// de cadastrar/editar gasto (extrato.html) e receita (receitas.html).
// Recebe o botão que abre o calendário, o span onde o texto aparece,
// o input hidden que guarda o valor (formato YYYY-MM-DD, o que o
// backend espera) e uma data inicial opcional.
function criarSeletorDeDataUnica(botaoId, textoId, hiddenId, dataInicial) {
  const botao = document.getElementById(botaoId);
  const texto = document.getElementById(textoId);
  const hidden = document.getElementById(hiddenId);
  if (!botao || !texto || !hidden || typeof Litepicker === 'undefined') return null;

  const atualizar = (data) => {
    hidden.value = data.format('YYYY-MM-DD');
    texto.textContent = data.format('DD/MM/YYYY');
  };

  const picker = new Litepicker({
    element: botao,
    singleMode: true,
    numberOfMonths: 1,
    numberOfColumns: 1,
    format: 'DD/MM/YYYY',
    lang: 'pt-BR',
    startDate: dataInicial || new Date(),
    autoApply: true,
    setup: (picker) => {
      picker.on('selected', (data) => atualizar(data));
    }
  });

  if (dataInicial) atualizar(picker.getStartDate());

  return picker;
}

// ============================================================
// Seletor de mês/ano (sem dia) usado no filtro de mês de despesas.html e
// receitas.html — despesa e receita são sempre por mês inteiro (colunas
// mes_ano/data_receita truncada por mês), então não faz sentido um
// calendário de dias (Litepicker) aqui. É um painel próprio que
// reaproveita a mesma casca visual .painel-dropdown do resto do app
// (Ordenar, Categoria), pra manter a cara padrão.
// ============================================================
const NOMES_MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
const NOMES_MESES_ABREV = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

// aoSelecionar (opcional) só dispara quando o usuário efetivamente
// escolhe um mês — não no preenchimento inicial do texto/valor, senão
// o filtro de mês recarregaria a página sozinho assim que a tela abrisse.
function criarSeletorDeMes(botaoId, textoId, hiddenId, valorInicial, aoSelecionar) {
  const botao = document.getElementById(botaoId);
  const texto = document.getElementById(textoId);
  const hidden = document.getElementById(hiddenId);
  if (!botao || !texto || !hidden) return null;

  const painel = document.createElement('div');
  painel.className = 'painel-dropdown painel-mes';
  botao.insertAdjacentElement('afterend', painel);

  const hoje = new Date();
  let ano = hoje.getFullYear();
  let mes = hoje.getMonth() + 1; // 1-12
  if (valorInicial) {
    const [a, m] = valorInicial.split('-');
    if (a && m) {
      ano = Number(a);
      mes = Number(m);
    }
  }

  const definirValor = (novoAno, novoMes) => {
    ano = novoAno;
    mes = novoMes;
    hidden.value = `${ano}-${String(mes).padStart(2, '0')}`;
    texto.textContent = `${NOMES_MESES[mes - 1]} ${ano}`;
  };

  const renderizar = (anoExibido) => {
    painel.innerHTML = '';

    const header = document.createElement('div');
    header.className = 'mes-picker-header';

    const btnAnterior = document.createElement('button');
    btnAnterior.type = 'button';
    btnAnterior.className = 'mes-picker-nav';
    btnAnterior.setAttribute('aria-label', 'Ano anterior');
    btnAnterior.innerHTML = '<span class="material-icons">chevron_left</span>';
    btnAnterior.addEventListener('click', (e) => {
      e.stopPropagation();
      renderizar(anoExibido - 1);
    });

    const spanAno = document.createElement('span');
    spanAno.className = 'mes-picker-ano';
    spanAno.textContent = anoExibido;

    const btnProximo = document.createElement('button');
    btnProximo.type = 'button';
    btnProximo.className = 'mes-picker-nav';
    btnProximo.setAttribute('aria-label', 'Próximo ano');
    btnProximo.innerHTML = '<span class="material-icons">chevron_right</span>';
    btnProximo.addEventListener('click', (e) => {
      e.stopPropagation();
      renderizar(anoExibido + 1);
    });

    header.append(btnAnterior, spanAno, btnProximo);

    const grid = document.createElement('div');
    grid.className = 'mes-picker-grid';

    NOMES_MESES_ABREV.forEach((nome, i) => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'mes-picker-item';
      if (anoExibido === ano && i + 1 === mes) item.classList.add('active');
      item.textContent = nome;
      item.addEventListener('click', () => {
        definirValor(anoExibido, i + 1);
        painel.classList.remove('show');
        if (aoSelecionar) aoSelecionar({ ano: anoExibido, mes: i + 1 });
      });
      grid.appendChild(item);
    });

    painel.append(header, grid);
  };

  const posicionar = () => {
    const r = botao.getBoundingClientRect();
    const largura = Math.max(r.width, 220);
    let esquerda = r.left;
    const maxEsquerda = window.innerWidth - largura - 8;
    if (esquerda > maxEsquerda) esquerda = Math.max(8, maxEsquerda);
    painel.style.width = `${largura}px`;
    painel.style.left = `${esquerda}px`;

    const alturaPainel = Math.min(painel.scrollHeight || 240, 300);
    const espacoAbaixo = window.innerHeight - r.bottom;
    if (espacoAbaixo < alturaPainel + 16 && r.top > espacoAbaixo) {
      painel.style.top = 'auto';
      painel.style.bottom = `${window.innerHeight - r.top + 8}px`;
    } else {
      painel.style.bottom = 'auto';
      painel.style.top = `${r.bottom + 8}px`;
    }
  };

  botao.addEventListener('click', (e) => {
    e.stopPropagation();
    const vaiAbrir = !painel.classList.contains('show');
    if (vaiAbrir) {
      renderizar(ano);
      posicionar();
    }
    painel.classList.toggle('show');
  });

  document.addEventListener('click', (e) => {
    if (
      painel.classList.contains('show') &&
      !painel.contains(e.target) &&
      e.target !== botao &&
      !botao.contains(e.target)
    ) {
      painel.classList.remove('show');
    }
  });

  // só fecha se quem rolou foi a página, não o próprio painel (mesmo
  // cuidado do configurarDropdown acima)
  window.addEventListener('scroll', (e) => {
    if (painel.contains(e.target)) return;
    painel.classList.remove('show');
  }, true);
  window.addEventListener('resize', () => {
    if (painel.classList.contains('show')) posicionar();
  });

  definirValor(ano, mes);

  return { getValor: () => hidden.value };
}

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
  window.location.href = `/logout`;
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

// ============================================================
// Teste grátis expirado sem plano pago: cadastro/edição de gasto,
// despesa e receita ficam bloqueados (consultar/listar/excluir
// continuam liberados — ver bloqueado_para_cadastro() no routes.py).
// A tela já sabe disso de cara via data-bloqueado-cadastro no <body>
// (extrato.html/despesas.html/receitas.html), então o aviso aparece
// no clique do "+"/editar, ANTES de abrir qualquer modal — em vez de
// deixar preencher tudo pra só rejeitar depois do "Salvar".
// ============================================================
const MENSAGEM_BLOQUEIO_PLANO = "Seu período de teste terminou. Assine um plano para continuar cadastrando.";

function bloquearSePlanoExpirado(e) {
  if (document.body.dataset.bloqueadoCadastro !== "true") return false;

  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }

  if (typeof showToast === "function") {
    showToast(MENSAGEM_BLOQUEIO_PLANO, false);
  }

  return true;
}

// ============================================================
// Confirmação genérica ("quer marcar essa despesa como paga?", "quer
// lançar um gasto pra essa despesa paga?") — cria o modal na hora, com
// estilo próprio (ver .confirmacao-generica-* em comum.css), em vez do
// confirm() nativo do navegador. Usada em extrato.js/despesas.js.
// ============================================================
function mostrarConfirmacao(mensagem, aoConfirmar, opcoes = {}) {
  const existente = document.getElementById("modal-confirmacao-generica");
  if (existente) existente.remove();

  const overlay = document.createElement("div");
  overlay.id = "modal-confirmacao-generica";
  overlay.className = "confirmacao-generica-overlay";
  overlay.innerHTML = `
    <div class="confirmacao-generica-card">
      <p class="confirmacao-generica-texto"></p>
      <div class="confirmacao-generica-botoes">
        <button type="button" class="confirmacao-generica-nao"></button>
        <button type="button" class="confirmacao-generica-sim"></button>
      </div>
    </div>
  `;

  // texto via textContent (não innerHTML) — mensagem pode conter nome
  // de gasto/despesa digitado pelo usuário, evita qualquer risco de XSS
  overlay.querySelector(".confirmacao-generica-texto").textContent = mensagem;
  overlay.querySelector(".confirmacao-generica-nao").textContent = opcoes.textoCancelar || "Não";
  overlay.querySelector(".confirmacao-generica-sim").textContent = opcoes.textoConfirmar || "Sim";

  document.body.appendChild(overlay);

  const fechar = () => overlay.remove();

  const cancelar = () => {
    fechar();
    if (typeof opcoes.aoCancelar === "function") opcoes.aoCancelar();
  };

  overlay.querySelector(".confirmacao-generica-nao").addEventListener("click", cancelar);
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) cancelar();
  });
  overlay.querySelector(".confirmacao-generica-sim").addEventListener("click", () => {
    fechar();
    aoConfirmar();
  });
}

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

// ============================================================
// Liga um botão-pílula a um painel flutuante de opções (usado no
// "Ordenar" e no filtro de "Categoria" de despesas.html e extrato.html):
// abre/fecha ao clicar no botão, fecha ao clicar fora, marca a opção
// escolhida como ativa (classe "active") e dispara o callback com o
// botão de opção clicado.
// ============================================================
function configurarDropdown(botaoId, painelId, aoEscolher) {
  const botao = document.getElementById(botaoId);
  const painel = document.getElementById(painelId);
  if (!botao || !painel) return;

  // O painel é position:fixed e a posição é calculada aqui (em vez de
  // position:absolute ancorado no botão) por dois motivos: 1) evita
  // ficar atrás de elementos com position:fixed (rodapé, cabeçalho),
  // já que um painel "solto" na página empilha na ordem de quem
  // apareceu por último, não pelo z-index; 2) um elemento absoluto que
  // "vaza" pra baixo do fim da página aumenta a altura rolável do
  // documento, e isso já causou o rodapé/ícone do topo se deslocarem
  // (o scroll surgindo empurra o layout) — fixed nunca entra nessa conta.
  const posicionar = () => {
    const r = botao.getBoundingClientRect();
    const largura = Math.max(r.width, 168);
    let esquerda = r.left;
    const maxEsquerda = window.innerWidth - largura - 8;
    if (esquerda > maxEsquerda) esquerda = Math.max(8, maxEsquerda);

    painel.style.width = `${largura}px`;
    painel.style.left = `${esquerda}px`;

    const alturaPainel = Math.min(painel.scrollHeight || 260, 260);
    const espacoAbaixo = window.innerHeight - r.bottom;

    if (espacoAbaixo < alturaPainel + 16 && r.top > espacoAbaixo) {
      painel.style.top = 'auto';
      painel.style.bottom = `${window.innerHeight - r.top + 8}px`;
    } else {
      painel.style.bottom = 'auto';
      painel.style.top = `${r.bottom + 8}px`;
    }
  };

  botao.addEventListener('click', (e) => {
    e.stopPropagation();
    const vaiAbrir = !painel.classList.contains('show');
    if (vaiAbrir) posicionar();
    painel.classList.toggle('show');
  });

  painel.querySelectorAll('.ordenar-opcao').forEach((opcao) => {
    opcao.addEventListener('click', () => {
      painel.querySelectorAll('.ordenar-opcao').forEach((o) => o.classList.remove('active'));
      opcao.classList.add('active');
      aoEscolher(opcao);
      painel.classList.remove('show');
    });
  });

  document.addEventListener('click', (e) => {
    if (
      painel.classList.contains('show') &&
      !painel.contains(e.target) &&
      e.target !== botao &&
      !botao.contains(e.target)
    ) {
      painel.classList.remove('show');
    }
  });

  // fecha em vez de ficar desalinhado — como agora é fixed, rolar a
  // página move o botão mas não o painel. Só quando quem rolou foi a
  // PÁGINA, porém: 'scroll' é capturado aqui em fase de captura (então
  // pega qualquer scroll da árvore, inclusive o interno do próprio
  // painel), e sem esse filtro, arrastar a lista de categorias pra ver
  // as opções de baixo fechava o painel imediatamente no meio do gesto.
  window.addEventListener('scroll', (e) => {
    if (painel.contains(e.target)) return;
    painel.classList.remove('show');
  }, true);
  window.addEventListener('resize', () => {
    if (painel.classList.contains('show')) posicionar();
  });
}

// ============================================================
// Seletor de categoria com opção de criar categoria própria (usado nos
// modais de cadastrar/editar despesa e gasto). É um botão-pílula +
// painel flutuante (mesmo componente do "Ordenar", pro estilo das
// opções ficar igual em vez de usar a lista feia/nativa do <select>).
// Quem realmente vai no <form> é o campo hidden #<prefixo>-categoria —
// a coluna "categoria" no banco é texto livre, então uma categoria nova
// digitada pelo usuário já funciona sem precisar de nenhuma tabela nova.
// ============================================================
const CATEGORIA_NOVA_VALOR = "__nova__";

function configurarSeletorCategoria(prefixo) {
  const hidden = document.getElementById(`${prefixo}-categoria`);
  const textoBtn = document.getElementById(`${prefixo}-categoria-texto`);
  const wrapper = document.getElementById(`${prefixo}-nova-categoria-wrapper`);
  const input = document.getElementById(`${prefixo}-nova-categoria`);
  const painel = document.getElementById(`${prefixo}-categoria-painel`);
  if (!hidden || !painel) return;

  configurarDropdown(`${prefixo}-categoria-btn`, `${prefixo}-categoria-painel`, (opcao) => {
    const categoria = opcao.dataset.categoria;
    if (categoria === CATEGORIA_NOVA_VALOR) {
      if (wrapper) wrapper.style.display = "flex";
      if (textoBtn) textoBtn.textContent = "+ Criar nova categoria";
      hidden.value = input ? input.value.trim() : "";
      if (input) input.focus();
    } else {
      if (wrapper) wrapper.style.display = "none";
      if (textoBtn) textoBtn.textContent = categoria;
      hidden.value = categoria;
    }
  });

  if (input) {
    input.addEventListener("input", () => {
      hidden.value = input.value.trim();
    });
  }

  // estado inicial: primeira categoria da lista
  const primeiraOpcao = painel.querySelector(".ordenar-opcao");
  if (primeiraOpcao) {
    primeiraOpcao.classList.add("active");
    hidden.value = primeiraOpcao.dataset.categoria;
    if (textoBtn) textoBtn.textContent = primeiraOpcao.dataset.categoria;
  }
}

// Chamado ao abrir o modal de edição, com a categoria já cadastrada do
// item clicado. Se essa categoria não estiver entre as opções do painel
// (ex.: categoria própria criada há pouco), cai no modo "nova categoria"
// com o texto já preenchido, em vez de simplesmente não selecionar nada.
function definirCategoriaSelecionada(prefixo, categoria) {
  const hidden = document.getElementById(`${prefixo}-categoria`);
  const textoBtn = document.getElementById(`${prefixo}-categoria-texto`);
  const wrapper = document.getElementById(`${prefixo}-nova-categoria-wrapper`);
  const input = document.getElementById(`${prefixo}-nova-categoria`);
  const painel = document.getElementById(`${prefixo}-categoria-painel`);
  if (!hidden) return;

  hidden.value = categoria || "";
  painel?.querySelectorAll(".ordenar-opcao").forEach((o) => o.classList.remove("active"));

  const opcaoExiste = painel
    ? Array.from(painel.querySelectorAll(".ordenar-opcao")).find((o) => o.dataset.categoria === categoria)
    : null;

  if (opcaoExiste) {
    opcaoExiste.classList.add("active");
    if (textoBtn) textoBtn.textContent = categoria;
    if (wrapper) wrapper.style.display = "none";
  } else {
    if (textoBtn) textoBtn.textContent = categoria || "+ Criar nova categoria";
    if (wrapper) wrapper.style.display = "flex";
    if (input) input.value = categoria || "";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  ["cadastrar", "editar"].forEach(configurarSeletorCategoria);
});

document.addEventListener("DOMContentLoaded", () => {
  // o servidor só manda a dica pra tela quando o usuário ainda não
  // marcou "não mostrar mais" (tutoriais_vistos no banco — antes era
  // localStorage, que não persistia de forma confiável dentro do
  // WebView do app Android e a dica voltava a aparecer toda hora) —
  // então se o elemento existe no HTML, é pra mostrar
  document.querySelectorAll(".tutorial-dica[data-tutorial]").forEach((dica) => {
    dica.classList.add("mostrar");

    const fechar = dica.querySelector(".tutorial-dica-fechar");
    const naoMostrar = dica.querySelector(".tutorial-dica-nao-mostrar");

    if (fechar) {
      fechar.addEventListener("click", () => {
        // só grava "não mostrar mais" se a pessoa marcou a caixinha —
        // fechar sem marcar só esconde por agora, e a dica volta a
        // aparecer da próxima vez que abrir essa tela
        if (naoMostrar && naoMostrar.checked) {
          fetch("/tutorial/marcar_visto", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tutorial: dica.dataset.tutorial }),
          }).catch(() => {});
        }
        dica.classList.remove("mostrar");
      });
    }
  });
});