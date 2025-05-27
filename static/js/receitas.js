let receitasChart = null;

function criarGrafico(labels, values) {
  const canvas = document.getElementById('receitasChart');
  const ctx = canvas.getContext('2d');

  const backgroundColors = [
    'rgba(26, 188, 156, 1)',
    'rgba(255, 206, 86, 0.7)',
    'rgba(199, 65, 25, 0.7)',
    'rgba(176, 224, 230, 1)'
  ];

  if (receitasChart) {
    receitasChart.destroy();
  }

  receitasChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: backgroundColors.slice(0, labels.length),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            boxWidth: 20,
            padding: 15
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const value = context.parsed;
              return `${context.label}: R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            }
          }
        }
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById('receitasChart');
  const labels = JSON.parse(canvas.dataset.labels);
  const values = JSON.parse(canvas.dataset.values);

  criarGrafico(labels, values);

  const modal = document.getElementById("modal");
  const addBtn = document.getElementById("addReceitaBtn-REMOVIDO");
  const form = document.getElementById("formReceita");

  addBtn.addEventListener("click", () => {
    modal.style.display = "flex";
  });

  window.fecharModal = function () {
    modal.style.display = "none";
  };

  window.onclick = function (event) {
    if (event.target === modal) {
      modal.style.display = "none";
    }
  };

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = new FormData(form);
    const data = {
      receita: formData.get("receita"),
      valor: formData.get("valor"),
      mes: formData.get("mes")
    };

    const mesSelecionado = data.mes;

      //em testes de prod
    // try {
    //   const response = await fetch("/salvar_receita", {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify(data)
    //   });

    //   if (response.ok) {
    //     const dadosAtualizados = await fetch(`/dados_receitas?mes=${encodeURIComponent(mesSelecionado)}`);
    //     const json = await dadosAtualizados.json();

    //     criarGrafico(json.labels, json.values);

    //     modal.style.display = "none";
    //     form.reset();
    //   } else {
    //     alert("Erro ao salvar receita." + response);
    //   }
    // } catch (error) {
    //   alert("Erro de conexão: " + error.message);
    // }
  });
});
