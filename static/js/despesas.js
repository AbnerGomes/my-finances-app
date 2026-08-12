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
// criarSeletorDeMes agora vive em comum.js (compartilhado com
// receitas.js, que usa o mesmo componente pro filtro de mês).

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

      if (bloquearSePlanoExpirado(e)) return;

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
    btn.addEventListener("click", (e) => {
      // despesa de outra pessoa (modo Casal) — nem abre o modal de
      // edição; quem barra e avisa é o protegerAcoesDeTerceiros (comum.js)
      if (btn.dataset.proprio === "false") return;

      if (bloquearSePlanoExpirado(e)) return;

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

      // despesa de outra pessoa (modo Casal) — nem abre o modal de
      // confirmação; quem barra e avisa é o protegerAcoesDeTerceiros
      // (comum.js), que também escuta o clique nesse mesmo ícone
      if (btn.dataset.proprio === "false") return;

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

  // ================= REPLICAR PARA O MÊS SEGUINTE =================
  // copia a despesa (descrição/valor/categoria/tipo) pro mês seguinte,
  // sempre como Pendente — pra não precisar digitar de novo uma despesa
  // fixa/recorrente todo mês
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-replicar-despesa");
    if (!btn) return;

    // não deixa o clique borbulhar pro card e fechar o detalhe que
    // acabou de ser usado pra clicar no botão
    e.stopPropagation();

    const id = btn.dataset.id;
    btn.disabled = true;

    fetch("/replicar_despesa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_despesa: id })
    })
      .then(res => res.json().then(corpo => ({ ok: res.ok, corpo })))
      .then(({ ok, corpo }) => {
        showToast(ok ? (corpo.mensagem || "Despesa replicada para o mês seguinte!") : (corpo.erro || "Erro ao replicar despesa"), ok);
      })
      .catch(() => showToast("Erro de conexão", false))
      .finally(() => { btn.disabled = false; });
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