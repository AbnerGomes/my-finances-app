document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById('receitasChart');
    const labels = JSON.parse(canvas.dataset.labels);
    const values = JSON.parse(canvas.dataset.values);
  
    const backgroundColors = [
      'rgba(26, 188, 156, 1)',
      'rgba(255, 206, 86, 0.7)',
      'rgba(199, 65, 25, 0.7)',
      'rgba(176, 224, 230, 1)'
    ];
  
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
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
                return `${context.label}: R$ ${value.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
              }
            }
          }
        }
      }
    });
  });
  


  document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal");
    const addBtn = document.getElementById("addReceitaBtn");
  
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
  });
  