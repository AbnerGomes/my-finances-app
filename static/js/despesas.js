let idParaExcluir = null;

function atualizarStatus(selectElement) {
    const novoStatus = selectElement.value;
    const linha = selectElement.closest('tr');
    const idDespesa = linha.getAttribute('data-id');
  
    const spanStatus = linha.querySelector('.status-indicator');
    const textoStatus = linha.querySelector('.status-text');
  
    // Atualiza a cor da bolinha
    spanStatus.className = 'status-indicator'; // remove classes antigas
    spanStatus.classList.add(novoStatus.replaceAll(' ', '-')); // adiciona a nova classe
  
    // Atualiza o texto
    //textoStatus.textContent = novoStatus;
  
    // Envia para o backend
    fetch('/despesas', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        id_despesa: idDespesa,
        novo_status: novoStatus
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro ao atualizar status');
      }
      return response.json();
    })
    .then(data => {
      console.log('Status atualizado:', data);
    })
    .catch(error => {
      alert('Erro ao atualizar status: ' + error.message);
    });
  }
  


  function filtrarPorMes() {
    const filtroMes = document.getElementById("filtroMes").value;
    
    if (filtroMes) {
        const dataInicio = filtroMes;
        window.location.href = `/despesas?mes_ano='${dataInicio}`;
        document.getElementById("filtroMes").value = filtroMes;
    } else {
        alert("Selecione um mês para filtrar.");
    }
}

function limparFiltro() {
    window.location.href = "/despesas";
    document.getElementById("filtroMes").value = "2025-04"
}


document.addEventListener('DOMContentLoaded', () => {
    aplicarCoresIniciais();
  });
  
  function aplicarCoresIniciais() {
    document.querySelectorAll('tr').forEach(row => {
      const statusText = row.querySelector('td:nth-child(4)')?.innerText?.trim();
      const indicador = row.querySelector('.status-indicator');
  
      if (statusText && indicador) {
        indicador.classList.remove('Pago', 'Pendente', 'Parcial'); // limpa
        if (statusText === 'Pago') {
          indicador.classList.add('Pago');
        } else if (statusText === 'Pendente') {
          indicador.classList.add('Pendente');
        } else if (statusText === 'Parcial') {
          indicador.classList.add('Parcial');
        }
      }
    });
  }


//modal 
document.addEventListener('click', function (event) {
  // Verifica se o evento foi disparado por um botão de edição
  
  if (event.target.classList.contains('btn-left')) {
    event.preventDefault(); // evita comportamento padrão do botão/link

    //workaround
//     $.getJSON(`/valida_mensalista`, function(dados) {

//       console.log('STATUS')
// console.log(dados)
//       if (dados.status === 'ok') {
//         document.getElementById('modal-cadastrar').style.display = 'block';
//       }
//       else{
//         document.getElementById('modal-mensalista').style.display = 'block';
//       }

//   });
fetch('/valida_mensalista')
      .then(response => response.json())  // Converte a resposta para JSON
      .then(dados => {
        console.log('STATUS recebido:', dados); // Verificando o que está vindo no JS

        if (dados.status === 'ok') {
          document.getElementById('modal-cadastrar').style.display = 'block';
        } else {
          document.getElementById('modal-mensalista').style.display = 'block';
        }
      })
      .catch(error => {
        console.error('Erro na requisição:', error);
      });  

}
else
{
  
  //ok mensalista
  if (event.target && event.target.classList.contains('btn-ok')) {
    const modal_mensalista = document.getElementById('modal-mensalista');
    modal_mensalista.style.display = 'none';

 }

  // Verifica se o evento foi disparado por um botão de edição
  if (event.target && event.target.classList.contains('edit-icon')) {
    const categoria = event.target.getAttribute('data-categoria');
    const descricao = event.target.getAttribute('data-descricao');
    const valor = event.target.getAttribute('data-valor');
    
    const id = event.target.getAttribute('data-id');

  

    document.getElementById('editar-categoria').value = categoria;
    document.getElementById('editar-descricao').value = descricao;
    document.getElementById('editar-valor').value = valor;

    document.getElementById('editar-id').value = id;

    const modal = document.getElementById('modal-editar');
    modal.style.display = 'flex';
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
 


  //deletar
   // Clique no ícone de deletar

   if (event.target && event.target.classList.contains('fa-trash')) {
      const modal = document.getElementById('modal-confirmar-exclusao');
      // const fecharModal = document.getElementById('fechar-modal-excluir');
      // const confirmarBtn = document.getElementById('confirmar-exclusao');

      let idSelecionado = null;

      // Abre o modal ao clicar na lixeira
      
      idSelecionado = event.target.getAttribute('data-id');
      modal.style.display = 'block';
              
      //setar no campo id hidden o id para delecao
      document.getElementById('id-despesa-excluir').value = idSelecionado;

   }

   //cadastro ok  
  if (event.target && event.target.classList.contains('botao-deletar')) {
    const modal_delete = document.getElementById('modal-confirmar-exclusao');
    //const modal_ok = document.getElementById('modal-cadastro-ok');
    modal_delete.style.display = 'none';

    //modal_ok.style.display = 'block';
    //modal_ok.innerHTML = 'Despesa deletada com sucesso ! Recarregando...'

 }


  } 
});