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

    // Atualiza visualmente o texto no botão (o botão em si vira o "anchor"
    // do Litepicker, mas o texto fica num span filho pra não perder o ícone)
    const pickerInput = document.getElementById('periodo-picker');
    const pickerTexto = document.getElementById('periodo-picker-texto');
    pickerTexto.textContent = `${startDate.toLocaleDateString()} até ${endDate.toLocaleDateString()}`;

    // Inicializa o picker
    const picker = new Litepicker({
        element: pickerInput,
        singleMode: false,
        numberOfMonths: 1,
        numberOfColumns: 1,
        format: "DD/MM/YYYY",
        lang: "pt-BR",
        startDate: startDate,
        endDate: endDate,
        autoApply: true,
        setup: (picker) => {
            picker.on('selected', (startDate, endDate) => {
                document.querySelector('input[name="data_inicio"]').value = startDate.format('YYYY-MM-DD');
                document.querySelector('input[name="data_fim"]').value = endDate.format('YYYY-MM-DD');
                pickerTexto.textContent = `${startDate.format('DD/MM/YYYY')} até ${endDate.format('DD/MM/YYYY')}`;
                submeterFiltroExtrato();
            });
        }
    });

    //validacao icone de casal

    // Seletor de data único (calendário bonitinho, mesmo padrão do filtro
    // de período) usado nos modais de cadastrar/editar gasto. Recebe o
    // botão que abre o calendário, o span onde o texto aparece, o input
    // hidden que guarda o valor (formato YYYY-MM-DD, o que o backend
    // espera) e uma data inicial opcional.
    function criarSeletorDeDataUnica(botaoId, textoId, hiddenId, dataInicial) {
        const botao = document.getElementById(botaoId);
        const texto = document.getElementById(textoId);
        const hidden = document.getElementById(hiddenId);
        if (!botao || !texto || !hidden) return null;

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
            startDate: dataInicial || hoje,
            autoApply: true,
            setup: (picker) => {
                picker.on('selected', (data) => atualizar(data));
            }
        });

        if (dataInicial) atualizar(picker.getStartDate());

        return picker;
    }

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
    const ordenarBtn = document.getElementById('ordenar-btn');
    const painelOrdenar = document.getElementById('painelOrdenar');

    if (ordenarBtn && painelOrdenar) {
        ordenarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            painelOrdenar.classList.toggle('show');
        });

        painelOrdenar.querySelectorAll('.ordenar-opcao').forEach((opcao) => {
            opcao.addEventListener('click', () => {
                painelOrdenar.querySelectorAll('.ordenar-opcao').forEach((o) => o.classList.remove('active'));
                opcao.classList.add('active');
                aplicarOrdenacaoGastos(opcao.dataset.ordenar);
                painelOrdenar.classList.remove('show');
            });
        });

        document.addEventListener('click', (e) => {
            if (
                painelOrdenar.classList.contains('show') &&
                !painelOrdenar.contains(e.target) &&
                e.target !== ordenarBtn &&
                !ordenarBtn.contains(e.target)
            ) {
                painelOrdenar.classList.remove('show');
            }
        });
    }
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

    if (!window._gastosOrdemOriginal) {
        window._gastosOrdemOriginal = Array.from(lista.children);
    }

    if (criterio === 'recentes') {
        window._gastosOrdemOriginal.forEach((node) => lista.appendChild(node));
        return;
    }

    window._gastosOrdemOriginal
        .filter((node) => node.classList.contains('data-grupo'))
        .forEach((node) => node.remove());

    const cards = Array.from(lista.querySelectorAll('.gasto-card'));

    const parseDataBr = (str) => {
        const [dia, mes, ano] = (str || '').split('/');
        return new Date(Number(ano), Number(mes) - 1, Number(dia));
    };

    const comparadores = {
        antigos: (a, b) => parseDataBr(a.dataset.data) - parseDataBr(b.dataset.data),
        'maior-valor': (a, b) => parseFloat(b.dataset.valor) - parseFloat(a.dataset.valor),
        'menor-valor': (a, b) => parseFloat(a.dataset.valor) - parseFloat(b.dataset.valor),
        nome: (a, b) => (a.querySelector('.gasto-descricao')?.textContent || '')
            .localeCompare(b.querySelector('.gasto-descricao')?.textContent || '', 'pt-BR'),
    };

    const comparador = comparadores[criterio];
    if (comparador) cards.sort(comparador);

    cards.forEach((card) => lista.appendChild(card));
}


//modal 
document.addEventListener('click', function (event) {
    // Verifica se o evento foi disparado por um botão de edição
    
    
    const btn = event.target.closest('.btn-adicionar');

    if (btn) {
      document.getElementById('modal-cadastrar').style.display = 'block';
      event.preventDefault(); // evita comportamento padrão do botão/link
      
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


//baixar pdf force
document.getElementById("enviapdf").addEventListener("click", function (e) {
  e.preventDefault(); // evita que o link redirecione a página

  const url = this.href; // pega a URL completa já montada no atributo href

  const link = document.createElement("a");
  link.href = url;
  link.download = "extrato.pdf";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
});

//add gasto rapido
function quickAddGasto(descricao, valor, categoria) {

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
  .then(res => res.json())
  .then(() => {
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

