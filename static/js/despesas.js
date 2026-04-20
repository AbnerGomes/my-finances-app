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

  if (filtroMes) {
    window.location.href = `/despesas?mes_ano=${filtroMes}`;
  } else {
    showToast("Selecione um mês", false);
  }
}

// ================= MODAIS =================
function abrirModal(id) {
  document.getElementById(id).style.display = "flex";
}

function fecharModal(id) {
  document.getElementById(id).style.display = "none";
}

// ================= EVENTOS =================
document.addEventListener('DOMContentLoaded', () => {

  // 👉 BOTÃO ADICIONAR (AGORA CORRETO)
  const btnAdd = document.getElementById("addDespesaBtn");

  if (btnAdd) {
    btnAdd.addEventListener("click", (e) => {
      e.stopPropagation();

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
    btn.addEventListener("click", () => {
      document.getElementById('editar-categoria').value = btn.dataset.categoria;
      document.getElementById('editar-descricao').value = btn.dataset.descricao;
      document.getElementById('editar-valor').value = btn.dataset.valor;
      document.getElementById('editar-id').value = btn.dataset.id;

      abrirModal("modal-editar");
    });
  });

  // 👉 DELETE (SEM BUG)
  document.querySelectorAll(".delete-despesa").forEach(btn => {

    btn.addEventListener("click", () => {

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

});