document.addEventListener('DOMContentLoaded', function () {
    // Pega as datas do formulário
    const dataInicioStr = document.getElementById('data_inicio')?.value;
    const dataFimStr = document.getElementById('data_fim')?.value;

    // Se vierem vazias, usa primeiro dia do mês até hoje
    const hoje = new Date();
    const primeiroDiaMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1);

    // Converte para datas no fuso local (sem subtrair 1 dia)
    const parseDate = (str) => {
        if (!str) return null;
        const parts = str.split('-'); // "YYYY-MM-DD"
        return new Date(parts[0], parts[1] - 1, parts[2]); // mês começa em 0
    };

    const startDate = parseDate(dataInicioStr) || primeiroDiaMes;
    const endDate = parseDate(dataFimStr) || hoje;

    // Atualiza visualmente o texto no botão "Período" (abre o bottom
    // sheet — ver mais abaixo). Formato curto (sem ano, "01/07 a 24/07")
    // pra caber no espaço da pílula ao lado de "Ordenar"/"Categoria" — o
    // intervalo completo (com ano) fica disponível no title, pra quem
    // passar o mouse/segurar o dedo.
    const pad2 = (n) => String(n).padStart(2, '0');
    const curtoDate = (d) => `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}`;
    const formatarISO = (d) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;

    const pickerInput = document.getElementById('periodo-picker');
    const pickerTexto = document.getElementById('periodo-picker-texto');
    pickerTexto.textContent = `${curtoDate(startDate)} a ${curtoDate(endDate)}`;
    pickerInput.title = `${startDate.toLocaleDateString()} até ${endDate.toLocaleDateString()}`;

    // ================= BOTTOM SHEET "PERÍODO" =================
    // Substitui o antigo calendário de intervalo (Litepicker range) por
    // um sheet com atalhos (7/15/30/90 dias) + intervalo personalizado,
    // no mesmo padrão visual de apps de banco.
    const sheetPeriodo = document.getElementById('sheet-periodo');

    const abrirSheetPeriodo = () => sheetPeriodo?.classList.add('show');
    const fecharSheetPeriodo = () => sheetPeriodo?.classList.remove('show');

    if (pickerInput && sheetPeriodo) {
        pickerInput.addEventListener('click', abrirSheetPeriodo);

        // fecha ao clicar no fundo escuro (fora do conteúdo do sheet)
        sheetPeriodo.addEventListener('click', (e) => {
            if (e.target === sheetPeriodo) fecharSheetPeriodo();
        });
    }

    const aplicarPeriodo = (dataInicio, dataFim, textoBotao) => {
        document.getElementById('data_inicio').value = formatarISO(dataInicio);
        document.getElementById('data_fim').value = formatarISO(dataFim);
        pickerTexto.textContent = textoBotao;
        pickerInput.title = `${dataInicio.toLocaleDateString()} até ${dataFim.toLocaleDateString()}`;
        fecharSheetPeriodo();
        submeterFiltroExtrato();
    };

    // atalhos "7 Dias" / "15 Dias" / "30 Dias" / "90 Dias" — aplica na hora
    document.querySelectorAll('.periodo-rapido-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const dias = Number(btn.dataset.dias);
            const fim = new Date();
            const inicio = new Date();
            inicio.setDate(inicio.getDate() - (dias - 1));
            aplicarPeriodo(inicio, fim, `${curtoDate(inicio)} a ${curtoDate(fim)}`);
        });
    });

    // intervalo personalizado — mesmo seletor de data único usado no
    // resto do app (criarSeletorDeDataUnica, em comum.js)
    const pickerDataInicial = criarSeletorDeDataUnica(
        'periodo-data-inicial-btn', 'periodo-data-inicial-texto', 'periodo-data-inicial', startDate
    );
    const pickerDataFinal = criarSeletorDeDataUnica(
        'periodo-data-final-btn', 'periodo-data-final-texto', 'periodo-data-final', endDate
    );

    const DOIS_ANOS_EM_MS = 2 * 365 * 24 * 60 * 60 * 1000;

    const btnFiltrarPeriodo = document.getElementById('btn-filtrar-periodo');
    if (btnFiltrarPeriodo) {
        btnFiltrarPeriodo.addEventListener('click', () => {
            const iniStr = document.getElementById('periodo-data-inicial').value;
            const fimStr = document.getElementById('periodo-data-final').value;

            if (!iniStr || !fimStr) {
                showToast('Selecione a data inicial e a data final', false);
                return;
            }

            const inicio = parseDate(iniStr);
            const fim = parseDate(fimStr);

            if (inicio > fim) {
                showToast('A data inicial não pode ser depois da data final', false);
                return;
            }

            if (fim - inicio > DOIS_ANOS_EM_MS) {
                showToast('Você só pode consultar períodos de até 2 anos', false);
                return;
            }

            aplicarPeriodo(inicio, fim, `${curtoDate(inicio)} a ${curtoDate(fim)}`);
        });
    }

    const btnLimparPeriodo = document.getElementById('btn-limpar-periodo');
    if (btnLimparPeriodo) {
        btnLimparPeriodo.addEventListener('click', () => {
            // limpa os dois campos — o backend já cai de volta no padrão
            // (primeiro dia do mês até hoje) quando vêm vazios
            document.getElementById('data_inicio').value = '';
            document.getElementById('data_fim').value = '';
            fecharSheetPeriodo();
            submeterFiltroExtrato();
        });
    }

    //validacao icone de casal

    // criarSeletorDeDataUnica agora vive em comum.js (compartilhado com receitas.js)
    const pickerCadastrar = criarSeletorDeDataUnica('cadastrar-data-btn', 'cadastrar-data-texto', 'cadastrar-data', hoje);
    const pickerEditar = criarSeletorDeDataUnica('editar-data-btn', 'editar-data-texto', 'editar-data');

    // deixa os dois pickers acessíveis fora deste bloco (usados ao abrir o
    // modal de edição, pra sincronizar com a data do gasto clicado)
    window._pickerEditarGasto = pickerEditar;

    // painel flutuante de "ações rápidas" — abre no clique do botão de
    // raio, fecha no X, clicando fora dele, ou clicando no raio de novo
    const btnAcoesRapidas = document.getElementById('btnAcoesRapidas');
    const painelAcoesRapidas = document.getElementById('painelAcoesRapidas');
    const fecharAcoesRapidas = document.getElementById('fecharAcoesRapidas');

    if (btnAcoesRapidas && painelAcoesRapidas) {
        btnAcoesRapidas.addEventListener('click', function (e) {
            e.stopPropagation();
            painelAcoesRapidas.classList.toggle('show');
        });

        if (fecharAcoesRapidas) {
            fecharAcoesRapidas.addEventListener('click', function () {
                painelAcoesRapidas.classList.remove('show');
            });
        }

        document.addEventListener('click', function (e) {
            if (
                painelAcoesRapidas.classList.contains('show') &&
                !painelAcoesRapidas.contains(e.target) &&
                e.target !== btnAcoesRapidas &&
                !btnAcoesRapidas.contains(e.target)
            ) {
                painelAcoesRapidas.classList.remove('show');
            }
        });
    }

    // ================= BUSCA POR NOME =================
    // filtra os cards já carregados na tela pelo texto digitado, sem
    // recarregar a página (igual a apps bancários: busca instantânea)
    const campoBusca = document.getElementById('buscaDescricao');
    if (campoBusca) {
        campoBusca.addEventListener('input', (e) => filtrarGastosPorTexto(e.target.value));
    }

    // ================= ORDENAR =================
    configurarDropdown('ordenar-btn', 'painelOrdenar', (opcao) => {
        aplicarOrdenacaoGastos(opcao.dataset.ordenar);
    });

    // ================= FILTRO DE CATEGORIA =================
    configurarDropdown('categoria-filtro-btn', 'categoria-filtro-painel', (opcao) => {
        const hidden = document.getElementById('categoria-filtro-hidden');
        if (hidden) hidden.value = opcao.dataset.categoria;
        const texto = document.getElementById('categoria-filtro-texto');
        if (texto) texto.textContent = opcao.dataset.categoria === 'Todas' ? 'Categoria' : opcao.dataset.categoria;
        submeterFiltroExtrato();
    });
});

// Filtra os .gasto-card pelo texto digitado (nome/descrição do gasto).
// Funciona independente da ordenação atual (agrupado por data ou não) —
// opera direto em cima de cada card e, se os cabeçalhos "📅 data" ainda
// estiverem no DOM (ordenação padrão "Mais recentes"), some com os que
// ficarem sem nenhum gasto visível embaixo.
function filtrarGastosPorTexto(termo) {
    const termoNorm = termo.trim().toLowerCase();
    const cards = document.querySelectorAll('.gasto-card');

    cards.forEach((card) => {
        const nome = card.querySelector('.gasto-descricao')?.textContent.toLowerCase() || '';
        const visivel = !termoNorm || nome.includes(termoNorm);
        card.style.display = visivel ? '' : 'none';
    });

    document.querySelectorAll('.data-grupo').forEach((grupo) => {
        let algumVisivel = false;
        let el = grupo.nextElementSibling;
        while (el && el.classList.contains('gasto-card')) {
            if (el.style.display !== 'none') algumVisivel = true;
            el = el.nextElementSibling;
        }
        grupo.style.display = algumVisivel ? '' : 'none';
    });

    const lista = document.querySelector('.lista-gastos');
    let vazio = document.getElementById('buscaVazia');
    const algumCardVisivel = Array.from(cards).some((c) => c.style.display !== 'none');

    if (!algumCardVisivel && termoNorm && lista) {
        if (!vazio) {
            vazio = document.createElement('div');
            vazio.id = 'buscaVazia';
            vazio.className = 'busca-vazia';
            lista.appendChild(vazio);
        }
        vazio.textContent = `Nenhum gasto encontrado para "${termo.trim()}"`;
    } else if (vazio) {
        vazio.remove();
    }
}

// Reordena os .gasto-card já carregados na tela (sem ir ao backend).
// "Mais recentes" restaura a ordem original vinda do servidor (agrupada
// por data, que já é do mais recente pro mais antigo); as demais opções
// removem os cabeçalhos de data (não fazem sentido fora da ordem
// cronológica) e reordenam os cards pelo critério escolhido.
function aplicarOrdenacaoGastos(criterio) {
    const lista = document.querySelector('.lista-gastos');
    if (!lista) return;

    // sempre parte dos cards atuais (não de uma cópia congelada), pra
    // funcionar certo mesmo depois de excluir um gasto
    const cards = Array.from(lista.querySelectorAll('.gasto-card'));

    const parseDataBr = (str) => {
        const [dia, mes, ano] = (str || '').split('/');
        return new Date(Number(ano), Number(mes) - 1, Number(dia));
    };

    const comparadores = {
        // o sort é estável (garantido pela spec desde ES2019), então
        // comparar só a data aqui mantém a ordem original dentro de um
        // mesmo dia — que já vem do backend ordenada como "recentes"
        recentes: (a, b) => parseDataBr(b.dataset.data) - parseDataBr(a.dataset.data),
        antigos: (a, b) => parseDataBr(a.dataset.data) - parseDataBr(b.dataset.data),
        'maior-valor': (a, b) => parseFloat(b.dataset.valor) - parseFloat(a.dataset.valor),
        'menor-valor': (a, b) => parseFloat(a.dataset.valor) - parseFloat(b.dataset.valor),
        categoria: (a, b) => (a.querySelector('.gasto-categoria')?.dataset.categoria || '')
            .localeCompare(b.querySelector('.gasto-categoria')?.dataset.categoria || '', 'pt-BR'),
        nome: (a, b) => (a.querySelector('.gasto-descricao')?.textContent.trim() || '')
            .localeCompare(b.querySelector('.gasto-descricao')?.textContent.trim() || '', 'pt-BR'),
    };

    const comparador = comparadores[criterio];
    if (comparador) cards.sort(comparador);

    // remove os cabeçalhos "📅 data" atuais e recria um toda vez que a
    // data mudar na nova ordem — assim a data nunca some, só passa a
    // acompanhar a ordenação escolhida em vez de ficar presa à ordem
    // cronológica original
    lista.querySelectorAll('.data-grupo').forEach((cabecalho) => cabecalho.remove());

    let dataAnterior = null;
    cards.forEach((card) => {
        const dataCard = card.dataset.data || '';
        if (dataCard !== dataAnterior) {
            const cabecalho = document.createElement('div');
            cabecalho.className = 'data-grupo';
            cabecalho.textContent = `📅 ${dataCard}`;
            lista.appendChild(cabecalho);
            dataAnterior = dataCard;
        }
        lista.appendChild(card);
    });
}


//modal 
document.addEventListener('click', function (event) {
    // Verifica se o evento foi disparado por um botão de edição
    
    
    const btn = event.target.closest('.btn-adicionar');

    if (btn) {
      event.preventDefault(); // evita comportamento padrão do botão/link

      if (bloquearSePlanoExpirado(event)) return;

      document.getElementById('modal-cadastrar').style.display = 'block';
      
      //comentado temporariamente para testes  
      // fetch('/valida_mensalista')
      // .then(response => response.json())  // Converte a resposta para JSON
      // .then(dados => {

      //   if (dados.status === 'ok') {
      //      document.getElementById('modal-cadastrar').style.display = 'block';
      //   } else {
      //     document.getElementById('modal-mensalista').style.display = 'block';
      //   }
      // })
      // .catch(error => {
      //   console.error('Erro na requisição:', error);
      // }); 
    }
    else
    {
    
    //ok mensalista
    if (event.target && event.target.classList.contains('btn-ok')) {
      const modal_mensalista = document.getElementById('modal-mensalista');
      modal_mensalista.style.display = 'none';
  
   }
    //editar

    if (event.target && event.target.classList.contains('edit-icon')) {
      // gasto de outra pessoa (modo Casal) — nem abre o modal de
      // edição; quem barra e avisa é o protegerAcoesDeTerceiros (comum.js)
      if (event.target.getAttribute('data-proprio') === 'false') return;

      if (bloquearSePlanoExpirado(event)) return;

      const data = event.target.getAttribute('data-data');
      const categoria = event.target.getAttribute('data-categoria');
      const descricao = event.target.getAttribute('data-descricao');
      const valor = event.target.getAttribute('data-valor');
      
      const id = event.target.getAttribute('data-id');

    const dataFormatada = formatarDataManual(data); // YYYY-MM-DD
    document.getElementById('editar-data').value = dataFormatada;

    const editarDataTexto = document.getElementById('editar-data-texto');
    if (editarDataTexto) editarDataTexto.textContent = data; // já vem DD/MM/YYYY

    if (window._pickerEditarGasto && dataFormatada) {
      const [ano, mes, dia] = dataFormatada.split('-');
      window._pickerEditarGasto.setDate(new Date(ano, mes - 1, dia));
    }


      definirCategoriaSelecionada('editar', categoria);
      document.getElementById('editar-descricao').value = descricao;
      document.getElementById('editar-valor').value = valor;
  
      document.getElementById('editar-id').value = id;

      const modal = document.getElementById('modal-editar');
      modal.style.display = 'block';
    }
  

    //deletar
     if (event.target && event.target.classList.contains('fa-trash')) {
        // gasto de outra pessoa (modo Casal) — nem abre o modal de
        // confirmação; quem barra e avisa é o protegerAcoesDeTerceiros
        // (comum.js), que também escuta o clique nesse mesmo ícone
        if (event.target.getAttribute('data-proprio') === 'false') return;

        const modal = document.getElementById('modal-confirmar-exclusao');
        const fecharModal = document.getElementById('fechar-modal-excluir');
        const confirmarBtn = document.getElementById('confirmar-exclusao');

        let idSelecionado = null;

        // Abre o modal ao clicar na lixeira

        idSelecionado = event.target.getAttribute('data-id');
        modal.style.display = 'block';
                
        //setar no campo id hidden o id para delecao
        document.getElementById('id-gasto-excluir').value = idSelecionado;

     }

     //cadastrar 
     if (event.target && event.target.classList.contains('btn-adicionar')) {
  
      const modal = document.getElementById('modal-cadastrar');
      modal.style.display = 'block';
    }
  

    // Fechar o modal quando clicar no botão de fechar ou fora do modal
    const fecharModal = document.getElementById('fechar-modal');
    const fecharModalok = document.getElementById('fechar-modal-cadastro');

    if (event.target === fecharModal) {
      const modal = document.getElementById('modal-editar');
      modal.style.display = 'none';
    }

    if (event.target === fecharModalok) {
      const modal = document.getElementById('modal-cadastrar');
      modal.style.display = 'none';
    }

    const modal = document.getElementById('modal-editar');
    const modal_cad = document.getElementById('modal-editar');
    if (event.target === modal || event.target === modal_cad) {
      modal.style.display = 'none';
    }

    // modal de confirmação de exclusão — fecha no X ou clicando fora dele
    // (antes só existia o botão "OK", sem jeito de desistir da exclusão)
    const modalExcluir = document.getElementById('modal-confirmar-exclusao');
    const fecharModalExcluir = document.getElementById('fechar-modal-excluir');
    if (modalExcluir && (event.target === fecharModalExcluir || event.target === modalExcluir)) {
      modalExcluir.style.display = 'none';
    }
  }

  });
  

  function formatarDataManual(dataBr) {
    const partes = dataBr.split('/');
    if (partes.length === 3) {
      const [dia, mes, ano] = partes;
      return `${ano}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}`;
    }
    return '';
  }
  
  //modal delecao

  let idParaExcluir = null;

//////validacao mensalista
document.addEventListener('click', function (event) {
  // Verifica se o botão "Adicionar Gasto" foi clicado
  
});


// Envia o formulário de filtro programaticamente (troca de período ou de
// categoria) — usa requestSubmit() em vez de submit() porque submit()
// NÃO dispara o evento 'submit' do form, e é nesse evento aqui embaixo
// que o filtro de período/categoria aprende se a visão é Individual ou
// Casal (isCasal); só form.submit() faria a página recarregar perdendo
// esse parâmetro.
function submeterFiltroExtrato() {
    const form = document.getElementById('filtro-form');
    if (!form) return;
    if (form.requestSubmit) {
        form.requestSubmit();
    } else {
        form.submit();
    }
}

const form = document.getElementById('filtro-form');
form.addEventListener('submit', function(e) {
  const usuario = document.getElementById('current-username').textContent;

  // Cria input escondido
  const inputHidden = document.createElement('input');
  inputHidden.type = 'hidden';
  inputHidden.name = 'isCasal';
  inputHidden.value = usuario == 'Casal' ? 'S' : 'N';

  // Adiciona ao form
  form.appendChild(inputHidden);
});


//add gasto rapido
function quickAddGasto(descricao, valor, categoria) {

  if (bloquearSePlanoExpirado()) return;

  fetch('/cadastrar_gasto_rapido', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      gasto: descricao,
      valor: valor,
      categoria: categoria
    })
  })
  .then(res => res.json().then(corpo => ({ ok: res.ok, corpo })))
  .then(({ ok, corpo }) => {
    // antes disparava "Gasto adicionado" mesmo quando o backend recusava
    // (ex.: teste grátis encerrado) — precisa checar se realmente deu certo
    if (!ok) {
      showToast(corpo.erro || "Erro ao adicionar", false);
      return;
    }

    showToast("Gasto adicionado 🚀");

    // opcional: recarregar lista
    setTimeout(() => {
      location.reload();
    }, 500);
  })
  .catch(() => {
    showToast("Erro ao adicionar", false);
  });
}

// ================= TOAST =================
function showToast(msg, success = true) {
  const toast = document.getElementById("toast");

  toast.textContent = msg;
  toast.style.background = success ? "#0abfa7" : "#ef4444";

  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

