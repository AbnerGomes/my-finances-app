

// Função para buscar e atualizar os dados do gráfico
function filtrarGastos(isCasal) {
  // $.getJSON(`/filtrarGastos/${periodo}/${isCasal}`, function(dados) {  
              window.location.href = `/extrato?isCasal=${isCasal}`;
}


function filtrarDespesas(isCasal) {
  // $.getJSON(`/filtrarGastos/${periodo}/${isCasal}`, function(dados) {  
              window.location.href = `/despesas?isCasal=${isCasal}`;
}


function toggleDropdown() {
    const menu = document.getElementById('dropdown-menu');
    menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
  }

//   function changeUser(name) {
//     document.getElementById('current-username').textContent = name;
//     document.getElementById('dropdown-menu').style.display = 'none';

//     let isCasal = name == 'Casal' ? 'S' : 'N'

    

//     // if (isCasal == 'S') {
//     //     document.getElementById('user-icon').textContent = 'people';
//     //     document.getElementById('current-username').textContent = 'Casal';
//     // }
//     // else{
//     //     document.getElementById('user-icon').textContent = 'person';
//     //     document.getElementById('current-username').textContent = name;
//     // }



//   // Fecha dropdown se clicar fora
//   document.addEventListener('click', function (event) {
//     const dropdown = document.querySelector('.dropdown');
//     if (!dropdown.contains(event.target)) {
//       document.getElementById('dropdown-menu').style.display = 'none';
//     }
//   });


// };


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


function changeMode(isCasal) {
  //document.getElementById('current-username').textContent = name;
  //document.getElementById('dropdown-menu').style.display = 'none';

  //let isCasal = name == 'Casal' ? 'S' : 'N'

  
    const nomePagina = window.location.pathname.split("/").pop();
    const nomeSemExtensao = nomePagina.split(".")[0];   
    if(nomeSemExtensao == 'extrato'){
      filtrarGastos(isCasal)
    }
    if(nomeSemExtensao == 'despesas'){
      filtrarDespesas(isCasal)
    }


  //carrega os dados do casal

  //filtrarGastos('mesatual',isCasal)
  //filtrarGastosMensais(isCasal)

  if (isCasal == 'S') {
      document.getElementById('user-icon').textContent = 'people';
  }
  else{
      document.getElementById('user-icon').textContent = 'person';
  }

}

  function toggleDropdown() {
    const menu = document.getElementById("main-dropdown");
    menu.style.display = menu.style.display === "block" ? "none" : "block";
  }

  function toggleModeDropdown() {
    const submenu = document.getElementById("mode-dropdown");
    submenu.style.display = submenu.style.display === "block" ? "none" : "block";
  }

  window.onclick = function(event) {
    if (!event.target.closest(".dropdown")) {
      document.getElementById("main-dropdown").style.display = "none";
      document.getElementById("mode-dropdown").style.display = "none";
    }
  };

function signOut(){
  window.location.href = `/`;
}
