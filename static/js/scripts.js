var donutChart = null; // Variável global inicializada

var barChart =null;


function filtrarGastosBtn(periodo){
    let name = document.getElementById('current-username').textContent;

    let isCasal = name == 'Casal' ? 'S' : 'N'

    filtrarGastos(periodo,isCasal)

}



// Função para buscar e atualizar os dados do gráfico
function filtrarGastos(periodo,isCasal) {
    var ctx = document.getElementById('donutChart').getContext('2d');

    $.getJSON(`/filtrarGastos/${periodo}/${isCasal}`, function(dados) {

            
            const mensagem = document.getElementById("mensagem");

            const total = document.getElementById("total");

            if (dados.length === 0 || dados === null || dados === undefined ) {

                //MENSAGEM
                const modal_mensagem = document.getElementById('modal-mensagem');
                modal_mensagem.style.display = 'block';


                mensagem.innerHTML = "Nenhum gasto encontrado para esse período.";
                //mensagem.style.display = "block"; // Exibe a mensagem
                // atualizarGrafico([], []); // Limpa o gráfico    
                total.style.display = "none"
            }
            else {
                console.log(periodo)
                console.log(dados)
                console.log('cai aqui')
                total.style.display = "block";
                mensagem.style.display = "none";
                let categorias = dados.map(item => item.categoria);
                let valores = dados.map(item => item.valor);
                
                donutChart.data.labels = categorias;
                donutChart.data.datasets[0].data = valores;
                donutChart.update();
                //drawDonutChart(dados);

                    // Calcula e mostra o total
                let totalGasto = valores.reduce((acc, val) => acc + parseFloat(val || 0), 0);
                let totalFormatado = totalGasto.toLocaleString('pt-BR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
                document.getElementById("valor-total").innerText = totalFormatado;
                document.getElementById("valor-total").style.color = '#003f5c';
            }    
            });
}

function filtrarGastosMensais(isCasal) {
    var ctx = document.getElementById('barChart').getContext('2d');

    $.getJSON(`/filtrarGastosMensais/${isCasal}`, function(dados) {

            
            //const mensagem = document.getElementById("mensagem");

            //const total = document.getElementById("total");

            if (dados.length === 0 || dados === null || dados === undefined ) {

                //MENSAGEM
                //const modal_mensagem = document.getElementById('modal-mensagem');
                //modal_mensagem.style.display = 'block';


                //mensagem.innerHTML = "Nenhum gasto encontrado para esse período.";
                //mensagem.style.display = "block"; // Exibe a mensagem
                // atualizarGrafico([], []); // Limpa o gráfico    
                //total.style.display = "none"
            }
            else {
                console.log('BAR CHART')

                let mes_ano = dados.map(item => item.mes_ano);
                let valores = dados.map(item => item.valor);
                
                barChart.data.labels = mes_ano;
                barChart.data.datasets[0].data = valores;
                barChart.update();

            }    
            });
}




 document.addEventListener("DOMContentLoaded", function () {
    //document.getElementById('total').style.display='none'
    

    let name = document.getElementById('current-username').textContent;
    let texto = document.getElementById('current-username').innerHTML;
    console.log(name);
    console.log(texto);

    if (name == 'analidiacadribeiro28') {    
        const modal_mo = document.getElementById('modal-mo');
        modal_mo.style.display = 'block';  
    }


filtrarGastos('mesatual','N');
filtrarGastosMensais('N');

   console.log("JavaScript carregado, tentando renderizar o gráfico...");
    
    var ctx = document.getElementById('donutChart');
    
    if (!ctx) {
        console.error("Erro: Elemento 'donutChart' não encontrado!");
        return;
    }

     // Verifica se o gráfico já existe e destrói antes de recriar
     if (donutChart) {
        donutChart.destroy();
        }

    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Alimentação', 'Entretenimento','Mobilidade','Saúde','Moradia','Outros','Dívidas','Educação'],
            datasets: [{
                data: [0, 0,0,0,0,0,0],
                backgroundColor: ['#B0E0E6', '#bc89f0','#eb2d2d', '#E0FFFF','#8FBC8F','#f7f568','#f78b8b','#f0054b']
            }]
        }, options: {
            plugins: {
              legend: {
                //position: 'rigth', // Posiciona a legenda ao lado direito do gráfico
                labels: {
                  color: 'black', // Muda a cor do texto das labels da legenda
                  font: {
                    size: 10
                    , weight: 'bold'
                  },                  
                  padding: 10, // Espaçamento entre as legendas
                  boxWidth: 10, // Largura das caixas de cor ao lado de cada label
                }
              }
            }
          }
    });

    //grafico de barras

    var ctxBar = document.getElementById('barChart').getContext('2d');

// Gráfico de Barras (Bar Chart)
barChart = new Chart(ctxBar, {
  type: 'bar',
  data: {
      labels: ['Jan/2025', 'Fev/2025', 'Mar/2025', 'Abr/2025', 'Mai/2025', 'Jun/2025', 'Jul/2025'],
      datasets: [{
          label: 'Gastos Mensais (R$)',
          data: [100, 5000, 1500, 10000, 1800, 600, 20],
          backgroundColor: ['#0abfa7','#0abfa7','#0abfa7','#0abfa7','#0abfa7','#0abfa7','#0abfa7'], // Cores suaves
          borderColor: '#F1F1F1', // Borda suave
          borderWidth: 1
      }]
  },
  options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'x', // Eixo X para o gráfico de barras
      plugins: {
          legend: {
              position: 'top',
              labels: {
                  color: '#2E3B55', // Cor da legenda suave
                  font: {
                      size: 12,
                      weight: 'normal'
                  }
              }
          }
      },
      scales: {
          x: {
              beginAtZero: true,
              title: {
                  display: true,
                  text: 'Mes/Ano',
                  color: '#2E3B55',
                  font: {
                      size: 10,
                      weight: 'bold'
                  }
              },
              ticks: {
                  color: '#2E3B55',
                  font: {
                      size: 10
                  }
              },
              grid: {
                display: false 
              }
          },
          y: {
              beginAtZero: true,
              title: {
                  display: false,
                  text: 'Valor Gasto (R$)',
                  color: '#2ECC71',
                  font: {
                      size: 12,
                      weight: 'bold'
                  }
              },
              ticks: {
                  color: '#2E3B55',
                  font: {
                      size: 10
                  }
              },
              grid: {
                display: false 
              }
          }
      },
      layout: {
          padding: {
              top: 20,
          }
      }
  }
});

 });

window.onload = function () {
    console.log("window.onload foi chamado!");
    console.log(document.getElementById("donutChart").getContext('2d'));
};

// data atual ja carregada no cadastro de gasto
document.addEventListener("DOMContentLoaded", function() {
    let hoje = new Date().toISOString().split('T')[0];
    let campoData = document.getElementById("data");
    if (campoData) {
        campoData.value = hoje;
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.period-button');
console.log('okokokokok')
    buttons.forEach(button => {
      button.addEventListener('click', function () {
        // Remove a classe "active" de todos
        buttons.forEach(btn => btn.classList.remove('active'));
        
        // Adiciona ao clicado
        this.classList.add('active');
      });
    });

    //tentatuva de mudar o icone
    let name = document.getElementById('current-username').textContent;

    let isCasal = name == 'Casal' ? 'S' : 'N'

    if (isCasal == 'S') {
        document.getElementById('user-icon').textContent = 'people';
    }
    else{
        document.getElementById('user-icon').textContent = 'person';
    }

  });

  document.addEventListener("click", function (e) {
    // Verifica se clicou num botão com a classe "period-button"
    if (e.target.classList.contains("period-button")) {
      // Remove 'active' de todos
      document.querySelectorAll(".period-button").forEach(btn => {
        btn.classList.remove("active");
      });

      // Adiciona 'active' no botão clicado
      e.target.classList.add("active");
    }

    if (e.target && e.target.classList.contains('botao-salvar')) {
      const modal_mensagem = document.getElementById('modal-mensagem');
      modal_mensagem.style.display = 'none';  

      const modal_mo = document.getElementById('modal-mo');
      modal_mo.style.display = 'none'; 
   } 

  });

  function toggleDropdown() {
    const menu = document.getElementById('dropdown-menu');
    menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
  }

  function changeUser(name) {
    document.getElementById('current-username').textContent = name;
    document.getElementById('dropdown-menu').style.display = 'none';

    let isCasal = name == 'Casal' ? 'S' : 'N'

    

    //carrega os dados do casal
    filtrarGastos('mesatual',isCasal)
    filtrarGastosMensais(isCasal)

    if (isCasal == 'S') {
        document.getElementById('user-icon').textContent = 'people';
    }
    else{
        document.getElementById('user-icon').textContent = 'person';
    }

  }

  // Fecha dropdown se clicar fora
  document.addEventListener('click', function (event) {
    const dropdown = document.querySelector('.dropdown');
    if (!dropdown.contains(event.target)) {
      document.getElementById('dropdown-menu').style.display = 'none';
    }
  });

