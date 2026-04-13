console.log("JS RECEITAS CARREGOU");
document.addEventListener("DOMContentLoaded", () => {

  const modal = document.getElementById("modal");
  const addBtn = document.getElementById("addReceitaBtn");
  const form = document.getElementById("formReceita");

  const idInput = document.getElementById("receita-id");
  const descInput = document.getElementById("receita-desc");
  const valorInput = document.getElementById("receita-valor");
  const mesInput = document.getElementById("receita-mes");

  // abrir modal novo
  addBtn.addEventListener("click", () => {
    console.log("clicou"); // TESTE
    idInput.value = "";
    descInput.value = "";
    valorInput.value = "";
    modal.style.display = "flex";
  });

  // editar
  document.addEventListener("click", function (e) {

    if (e.target.classList.contains("edit-receita")) {
  
      document.getElementById("modal").style.display = "flex";
  
      document.getElementById("modal-title").innerText = "Editar Receita";
  
      document.getElementById("receita-id").value = e.target.dataset.id;
      document.getElementById("receita-desc").value = e.target.dataset.descricao;
      document.getElementById("receita-valor").value = e.target.dataset.valor;
      document.getElementById("receita-mes").value = e.target.dataset.mes;
    }
  
  });

  // deletar
  let receitaIdParaDeletar = null;
  let cardParaRemover = null;

  // abrir modal ao clicar na lixeira
  document.addEventListener("click", function (e) {

    if (e.target.classList.contains("delete-receita")) {

      receitaIdParaDeletar = e.target.dataset.id;
      cardParaRemover = e.target.closest(".receita-card");

      document.getElementById("modal-confirm").style.display = "flex";
    }

  });

  //confirmação do delete
  document.getElementById("btn-confirmar-delete").addEventListener("click", async () => {

    if (!receitaIdParaDeletar) return;
  
    try {
      await fetch("/deletar_receita", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ id: receitaIdParaDeletar })
      });
  
      showToast("Receita excluída!");
  
      cardParaRemover = e.target.closest(".receita-card");
      const grupo = cardParaRemover?.closest(".grupo-receitas");

      if (cardParaRemover) {
        cardParaRemover.style.transition = "0.3s";
        cardParaRemover.style.transform = "translateX(-100%)";
        cardParaRemover.style.opacity = "0";

        setTimeout(() => {
          cardParaRemover.remove();

          if (grupo && grupo.querySelectorAll(".receita-card").length === 0) {
            grupo.remove();
          }

        }, 300);
      }
  
    } catch {
      showToast("Erro ao excluir", false);
    }
  
    fecharModalConfirm();
  });

  //cancelar + fechar
  document.getElementById("btn-cancelar").addEventListener("click", fecharModalConfirm);

  function fecharModalConfirm() {
    document.getElementById("modal-confirm").style.display = "none";
    receitaIdParaDeletar = null;
    cardParaRemover = null;
  }


  // fechar modal
  window.fecharModal = function () {
    modal.style.display = "none";
  };

  window.onclick = function (e) {
    if (e.target === modal) modal.style.display = "none";
  };

  // salvar (create + update)
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const id = idInput.value;

  const data = {
    id: id,
    receita: descInput.value,
    valor: valorInput.value,
    mes: mesInput.value
  };

  // 
  const url = id ? "/editar_receita" : "/salvar_receita";

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });

    if (response.ok) {
      showToast(id ? "Receita atualizada!" : "Receita criada!");
      location.reload();
    } else {
      showToast("Erro ao salvar", false);
      return;
    }

  } catch (err) {
    showToast("Erro de conexão", false);
  }
});

});


function showToast(msg, success = true) {
  const toast = document.getElementById("toast");

  toast.textContent = msg;
  toast.style.background = success ? "#16a34a" : "#dc2626";

  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

let startX = 0;

document.querySelectorAll(".receita-card").forEach(card => {

  card.addEventListener("touchstart", e => {
    startX = e.touches[0].clientX;
  });

  card.addEventListener("touchend", e => {
    let endX = e.changedTouches[0].clientX;

    if (startX - endX > 80) {
      card.style.transform = "translateX(-100px)";
      card.style.opacity = "0.5";

      const id = card.querySelector(".delete-receita").dataset.id;

      setTimeout(() => {
        if (confirm("Excluir receita?")) {
          fetch("/deletar_receita", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ id })
          }).then(() => location.reload());
        } else {
          card.style.transform = "translateX(0)";
          card.style.opacity = "1";
        }
      }, 200);
    }
  });

});

addReceitaBtn.addEventListener("click", () => {
  console.log("clicou");

  idInput.value = "";
  descInput.value = "";
  valorInput.value = "";

  document.getElementById("modal-title").innerText = "Nova Receita"; // 🔥 ADD ISSO

  modal.style.display = "flex";
});