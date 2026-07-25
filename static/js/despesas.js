function showToast(msg, success = true) {
  const toast = document.getElementById("toast");

  toast.textContent = msg;
  toast.style.background = success ? "#16a34a" : "#dc2626";

  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

let idParaExcluir = null;

// ================= STATUS =================
function atualizarStatus(selectElement) {
  const card = selectElement.closest('.despesa-card');
  const idDespesa = card.dataset.id;
  const novoStatus = selectElement.value;

  // 🔥 remove classes antigas
  card.classList.remove("status-pago", "status-parcial", "status-pendente");

  // 🔥 adiciona nova
  if (novoStatus === "Pago") {
    card.classList.add("status-pago");
  } else if (novoStatus === "Parcial") {
    card.classList.add("status-parcial");
  } else {
    card.classList.add("status-pendente");
  }

  // backend
  fetch('/atualizar_status', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      id_despesa: idDespesa,
      novo_status: novoStatus
    })
  });
}

// ================= FILTRO =================
function filtrarPorMes() {
  const filtroMes = document.getElementById("filtroMes").value;
  const modoAtual = (typeof getModoSalvo === 'function') ? getModoSalvo() : 'N';

  if (filtroMes) {
    window.location.href = `/despesas?mes_ano=${filtroMes}&isCasal=${modoAtual}`;
  } else {
    showToast("Selecione um mês", false);
  }
}

// ================= MODAIS =================
function abrirModal(id) {
    document.getElementById(id).style.display = "block"; 
}

function fecharModal(id) {
  document.getElementById(id).style.display = "none";
}

// ================= REPLICAR DESPESA FIXA =================
// o checkbox "replicar para os demais meses do ano" só faz sentido pra
// despesas do tipo Fixa (valor que não muda mês a mês)
function atualizarOpcaoReplicar() {
  const wrapper = document.getElementById("replicar-ano-wrapper");
  if (!wrapper) return;

  const fixaMarcada = document.querySelector('input[name="tipo_despesa"][value="Fixa"]:checked');

  if (fixaMarcada) {
    wrapper.style.display = "block";
  } else {
    wrapper.style.display = "none";
    const checkbox = document.getElementById("replicar-ano");
    if (checkbox) checkbox.checked = false;
  }
}

// ================= SELETOR DE MÊS =================
// Despesa é sempre por mês inteiro (coluna mes_ano), então o seletor
// aqui é só mês/ano — sem dia — pra não sugerir uma precisão que não
// existe. É um painel próprio (não usa o Litepicker, que é um calendário
// de dias) mas reaproveita a mesma casca visual .painel-dropdown do
// resto do app (Ordenar, Categoria), pra manter a cara padrão.
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

  window.addEventListener('scroll', () => painel.classList.remove('show'), true);
  window.addEventListener('resize', () => {
    if (painel.classList.contains('show')) posicionar();
  });

  definirValor(ano, mes);

  return { getValor: () => hidden.value };
}

// ================= EVENTOS =================
document.addEventListener('DOMContentLoaded', () => {

  criarSeletorDeMes('cadastrar-data-btn', 'cadastrar-data-texto', 'cadastrar-data', document.getElementById('cadastrar-data')?.value);

  // filtro de mês do topo — mesmo calendário, filtra assim que um mês é escolhido
  criarSeletorDeMes('filtroMesBtn', 'filtroMesTexto', 'filtroMes', document.getElementById('filtroMes')?.value, () => filtrarPorMes());

  // 👉 BOTÃO ADICIONAR (AGORA CORRETO)
  const btnAdd = document.getElementById("addDespesaBtn");

  if (btnAdd) {
    btnAdd.addEventListener("click", (e) => {
      e.stopPropagation();

      // fetch('/valida_mensalista')
      //   .then(res => res.json())
      //   .then(dados => {
      //     if (dados.status === 'ok') {
      //       abrirModal("modal-cadastrar");
      //     } else {
      //       abrirModal("modal-mensalista");
      //     }
      //   });
      // por enquanto sempre abrir
      document.getElementById("form-cadastrar")?.reset();
      const primeiraCategoria = document.getElementById('cadastrar-categoria-painel')?.querySelector('.ordenar-opcao')?.dataset.categoria;
      if (primeiraCategoria) definirCategoriaSelecionada('cadastrar', primeiraCategoria);
      atualizarOpcaoReplicar();
      abrirModal("modal-cadastrar");
    });
  }

  // 👉 FECHAR MODAIS
  document.querySelectorAll(".close").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      btn.closest(".modal").style.display = "none";
    });
  });

  // 👉 EDITAR
  document.querySelectorAll(".edit-icon").forEach(btn => {
    btn.addEventListener("click", () => {
      definirCategoriaSelecionada('editar', btn.dataset.categoria);
      document.getElementById('editar-descricao').value = btn.dataset.descricao;
      document.getElementById('editar-valor').value = btn.dataset.valor;
      document.getElementById('editar-id').value = btn.dataset.id;

      abrirModal("modal-editar");
    });
  });

  // 👉 DELETE (SEM BUG)
  document.querySelectorAll(".delete-despesa").forEach(btn => {

    btn.addEventListener("click", () => {

      const id = btn.dataset.id;
      console.log(id)
      // const modal = document.getElementById("modal-confirmar-exclusao");
      const confirmarBtn = document.getElementById("confirmar-exclusao");

      abrirModal("modal-confirmar-exclusao");

      // limpa eventos antigos
      confirmarBtn.replaceWith(confirmarBtn.cloneNode(true));
      const novoBtn = document.getElementById("confirmar-exclusao");

      novoBtn.addEventListener("click", (e) => {
        e.preventDefault(); // 🔥 evita submit fantasma
      
        fetch("/deletar_despesa", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ id })
        })
        .then(() => {
          const card = btn.closest(".despesa-card");
      
          card.style.transition = "0.3s";
          card.style.transform = "translateX(-100%)";
          card.style.opacity = "0";
      
          setTimeout(() => card.remove(), 300);
      
          fecharModal("modal-confirmar-exclusao");
        })
        .catch(() => {
          showToast("Erro ao deletar despesa", false);
        });
      });

    });

  });

  // clique no card detalhes
  document.querySelectorAll(".despesa-card").forEach(card => {

    card.addEventListener("click", (e) => {
  
      // evita conflito com botões
      if (e.target.closest(".acoes") || e.target.tagName === "SELECT") return;
  
      const detalhe = card.querySelector(".despesa-detalhe");
      const jaAberto = card.classList.contains("aberto");
  
      // fecha todos
      document.querySelectorAll(".despesa-card").forEach(c => {
        c.classList.remove("aberto");
  
        const det = c.querySelector(".despesa-detalhe");
        if (det) det.style.height = "0px";
      });
  
      // abre se não estava aberto
      if (!jaAberto) {
        card.classList.add("aberto");

        // ⚡ AQUI entra o teu código
        detalhe.style.height = detalhe.scrollHeight + "px";
      }

    });

  });

  // ================= ORDENAR =================
  configurarDropdown('ordenar-despesas-btn', 'painelOrdenarDespesas', (opcao) => {
    aplicarOrdenacaoDespesas(opcao.dataset.ordenar);
  });

  // ================= FILTRO DE CATEGORIA (client-side — as despesas
  // do mês já estão todas carregadas na tela, sem precisar ir ao
  // backend de novo) =================
  configurarDropdown('categoria-despesas-btn', 'painelCategoriaDespesas', (opcao) => {
    categoriaDespesaAtiva = opcao.dataset.categoria;
    const texto = document.getElementById('categoria-despesas-texto');
    if (texto) texto.textContent = categoriaDespesaAtiva === 'Todas' ? 'Categoria' : categoriaDespesaAtiva;
    aplicarFiltroCategoriaDespesas();
  });

});

let categoriaDespesaAtiva = 'Todas';

// Filtra os .despesa-card já carregados na tela pela categoria
// escolhida no dropdown.
function aplicarFiltroCategoriaDespesas() {
  const cards = document.querySelectorAll('.despesa-card');
  let algumVisivel = false;

  cards.forEach((card) => {
    const categoria = card.dataset.categoria || '';
    const visivel = categoriaDespesaAtiva === 'Todas' || categoria === categoriaDespesaAtiva;
    card.style.display = visivel ? '' : 'none';
    if (visivel) algumVisivel = true;
  });

  const lista = document.querySelector('.lista-despesas');
  let vazio = document.getElementById('categoriaDespesaVazia');

  if (!algumVisivel && lista) {
    if (!vazio) {
      vazio = document.createElement('div');
      vazio.id = 'categoriaDespesaVazia';
      vazio.className = 'busca-vazia';
      lista.appendChild(vazio);
    }
    vazio.textContent = 'Nenhuma despesa nessa categoria';
  } else if (vazio) {
    vazio.remove();
  }
}

// Reordena os .despesa-card já carregados na tela (sem ir ao backend).
function aplicarOrdenacaoDespesas(criterio) {
  const lista = document.querySelector('.lista-despesas');
  if (!lista) return;

  if (!window._despesasOrdemOriginal) {
    window._despesasOrdemOriginal = Array.from(lista.querySelectorAll('.despesa-card'));
  }

  if (criterio === 'padrao') {
    window._despesasOrdemOriginal.forEach((card) => lista.appendChild(card));
    return;
  }

  const cards = Array.from(lista.querySelectorAll('.despesa-card'));

  const comparadores = {
    'maior-valor': (a, b) => parseFloat(b.dataset.valor) - parseFloat(a.dataset.valor),
    'menor-valor': (a, b) => parseFloat(a.dataset.valor) - parseFloat(b.dataset.valor),
    categoria: (a, b) => (a.dataset.categoria || '').localeCompare(b.dataset.categoria || '', 'pt-BR'),
    nome: (a, b) => (a.querySelector('.despesa-descricao')?.textContent.trim() || '')
      .localeCompare(b.querySelector('.despesa-descricao')?.textContent.trim() || '', 'pt-BR'),
  };

  const comparador = comparadores[criterio];
  if (comparador) cards.sort(comparador);

  cards.forEach((card) => lista.appendChild(card));
}

function filtrarPendentesAntigos(el) {

  // aplica classe de clique
  el.classList.add("clicando");

  setTimeout(() => {
    window.location.href = "/despesas?pendentes_antigos=S";
  }, 150); // tempo da animação
}