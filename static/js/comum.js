
// Função para buscar e atualizar os dados do gráfico
function filtrarGastos(isCasal) {
    // $.getJSON(`/filtrarGastos/${periodo}/${isCasal}`, function(dados) {  

    //         if (dados.length === 0 || dados === null || dados === undefined ) {

    //             console.log('ok')
    //         }    
    //         else{
                //window.location.href = `/extrato/${isCasal}`;
                window.location.href = `/extrato?isCasal=${isCasal}`;

            // }
            // });

            // Envia para o backend
// fetch('/extrato', {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json'
//     },
//     body: JSON.stringify({ isCasal: isCasal })
//   });

//   .then(response => {
//     if (!response.ok) {
//       throw new Error('Erro ao atualizar extrato');
//     }
//     return response.text(); // <<< aqui, não .json()
//   })
//   .then(html => {
//     document.body.innerHTML = html; // ou insere num <div> específico
//   })
//   .catch(error => {
//     alert('Erro ao atualizar extrato: ' + error.message);
//   });
    

}



function toggleDropdown() {
    const menu = document.getElementById('dropdown-menu');
    menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
  }

  function changeUser(name) {
    document.getElementById('current-username').textContent = name;
    document.getElementById('dropdown-menu').style.display = 'none';

    let isCasal = name == 'Casal' ? 'S' : 'N'

    

    // if (isCasal == 'S') {
    //     document.getElementById('user-icon').textContent = 'people';
    //     document.getElementById('current-username').textContent = 'Casal';
    // }
    // else{
    //     document.getElementById('user-icon').textContent = 'person';
    //     document.getElementById('current-username').textContent = name;
    // }

    filtrarGastos(isCasal)

  // Fecha dropdown se clicar fora
  document.addEventListener('click', function (event) {
    const dropdown = document.querySelector('.dropdown');
    if (!dropdown.contains(event.target)) {
      document.getElementById('dropdown-menu').style.display = 'none';
    }
  });


};


//   //tentando mudar no DOMCONTENTLOAD
//   document.addEventListener('DOMContentLoaded', function () {

//     //tentatuva de mudar o icone
//     let name = document.getElementById('current-username').textContent;

//     let isCasal = name == 'Casal' ? 'S' : 'N'

//     if (isCasal == 'S') {
//         document.getElementById('user-icon').textContent = 'people';
//         document.getElementById('current-username').textContent = 'Casal';
//     }
//     else{
//         document.getElementById('user-icon').textContent = 'person';
//         document.getElementById('current-username').textContent = name;
//     }

//   });
