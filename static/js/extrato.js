document.addEventListener("DOMContentLoaded", function () {
        console.log("EXTRATO carregado, tentando renderizar o gráfico...");
});



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

    // Atualiza visualmente o texto no botão
    const pickerInput = document.getElementById('periodo-picker');
    pickerInput.textContent = `${startDate.toLocaleDateString()} até ${endDate.toLocaleDateString()}`;

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
                pickerInput.textContent = `${startDate.format('DD/MM/YYYY')} até ${endDate.format('DD/MM/YYYY')}`;
            });
        }
    });

});


//modal 
document.addEventListener('click', function (event) {
    // Verifica se o evento foi disparado por um botão de edição
    
    if (event.target.classList.contains('btn-left')) {
      event.preventDefault(); // evita comportamento padrão do botão/link

      // Faz a requisição ao backend Flask
      fetch('/verificar_mensalista')
          .then(response => response.json())
          .then(data => {
              if (data.status === 'ok') {
                  // Mostra o modal de cadastro
                  document.getElementById('modal-cadastrar').style.display = 'block';
              } else {
                  // Mostra o modal de mensalista
                  document.getElementById('modal-mensalista').style.display = 'block';
              }
          })
          .catch(error => {
              console.error('Erro na verificação:', error);
          });
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

    const dataFormatada = formatarDataManual(data);
    document.getElementById('editar-data').value = dataFormatada;
    

      document.getElementById('editar-categoria').value = categoria;
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
     if (event.target && event.target.classList.contains('btn-left')) {
  
      const modal = document.getElementById('modal-cadastrar');
      modal.style.display = 'block';
    }
  
    //cadastro ok  
    if (event.target && event.target.classList.contains('botao-salvar')) {
      const modal_ok = document.getElementById('modal-cadastro-ok');
      const modal_cad = document.getElementById('modal-cadastrar');
      modal_cad.style.display = 'none';
      modal_ok.style.display = 'block';
  
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





