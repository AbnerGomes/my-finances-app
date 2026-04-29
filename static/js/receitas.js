console.log("JS RECEITAS CARREGOU");

document.addEventListener("DOMContentLoaded", () => {

  const modal = document.getElementById("modal");
  const addBtn = document.getElementById("addReceitaBtn");
  const form = document.getElementById("formReceita");

  const idInput = document.getElementById("receita-id");
  const descInput = document.getElementById("receita-desc");
  const valorInput = document.getElementById("receita-valor");

  //const mesInput = document.getElementById("receita-mes");
  const dataInput = document.getElementById("receita-data");
  dataInput.value = new Date().toISOString().split("T")[0];

  // ================= ABRIR MODAL =================
  addBtn.addEventListener("click", () => {
    idInput.value = "";
    descInput.value = "";
    valorInput.value = "";

    document.getElementById("modal-title").innerText = "Nova Receita";

    modal.style.display = "flex";
  });

  // ================= EDITAR =================
  document.addEventListener("click", function (e) {
    if (e.target.classList.contains("edit-receita")) {

      modal.style.display = "flex";

      document.getElementById("modal-title").innerText = "Editar Receita";

      idInput.value = e.target.dataset.id;
      descInput.value = e.target.dataset.descricao;
      valorInput.value = e.target.dataset.valor;
      //mesInput.value = e.target.dataset.mes;
      dataInput.value = e.target.dataset.data;
    }
  });

  // ================= DELETE =================
  let receitaIdParaDeletar = null;
  let cardParaRemover = null;

  document.addEventListener("click", function (e) {

    const btn = e.target.closest(".delete-receita"); // 🔥 MELHOR
  
    if (btn) {
      receitaIdParaDeletar = btn.dataset.id;
      cardParaRemover = btn.closest(".receita-card");
  
      console.log("CARD:", cardParaRemover); // debug
  
      document.getElementById("modal-confirm").style.display = "flex";
    }
  
  });

  document.getElementById("btn-confirmar-delete").addEventListener("click", async () => {

    if (!receitaIdParaDeletar || !cardParaRemover) {
      console.error("Dados inválidos para delete");
      return;
    }
  
    const card = cardParaRemover; // 🔥 SALVA REFERÊNCIA
    const grupo = card.closest(".grupo-receitas");

    try {
      await fetch("/deletar_receita", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ id: receitaIdParaDeletar })
      });
  
      showToast("Receita excluída!");
  
      // const grupo = cardParaRemover.closest(".grupo-receitas");
  
      card.style.transition = "0.3s";
      card.style.transform = "translateX(-100%)";
      card.style.opacity = "0";

      setTimeout(() => {
        console.log(card)
        if (card) {
          card.remove();
          console.log("ENTROU ??????")
        }
      
        // 🔥 DEBUG
        console.log("Grupo HTML:", grupo?.innerHTML);
      
        console.log("TAMANHO ANTES DA REMOCAO");
        console.log(grupo.querySelectorAll(".receita-card").length);
        if (grupo && grupo.querySelectorAll(".receita-card").length === 0) {
          console.log("REMOVENDO GRUPO");
      
          grupo.innerHTML = ""; // limpa tudo
          grupo.remove();
          console.log("TAMANHO APOS A REMOCAO");
        }
        
      }, 300);
  
    } catch (err) {
      console.error(err);
      showToast("Erro ao excluir", false);
    }
  
    fecharModalConfirm();
  });

  // ================= CANCELAR MODAL =================
  document.getElementById("btn-cancelar").addEventListener("click", fecharModalConfirm);

  function fecharModalConfirm() {
    document.getElementById("modal-confirm").style.display = "none";
    receitaIdParaDeletar = null;
    cardParaRemover = null;
  }

  // ================= FECHAR MODAL =================
  window.fecharModal = function () {
    modal.style.display = "none";
  };

  window.onclick = function (e) {
    if (e.target === modal) modal.style.display = "none";
  };

  // ================= SALVAR =================
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const id = idInput.value;

    const data = {
      id: id,
      receita: descInput.value,
      valor: valorInput.value,
      //mes: mesInput.value
      data: dataInput.value
    };

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
      }

    } catch {
      showToast("Erro de conexão", false);
    }
  });

  // ================= SWIPE DELETE =================
  // let startX = 0;

  // document.querySelectorAll(".receita-card").forEach(card => {

  //   card.addEventListener("touchstart", e => {
  //     startX = e.touches[0].clientX;
  //   });

  //   card.addEventListener("touchend", e => {
  //     let endX = e.changedTouches[0].clientX;

  //     if (startX - endX > 80) {
  //       card.style.transform = "translateX(-100px)";
  //       card.style.opacity = "0.5";

  //       const id = card.querySelector(".delete-receita").dataset.id;

  //       setTimeout(() => {
  //         if (confirm("Excluir receita?")) {
  //           fetch("/deletar_receita", {
  //             method: "POST",
  //             headers: {"Content-Type": "application/json"},
  //             body: JSON.stringify({ id })
  //           }).then(() => location.reload());
  //         } else {
  //           card.style.transform = "translateX(0)";
  //           card.style.opacity = "1";
  //         }
  //       }, 200);
  //     }
  //   });

  // });

});


// ================= TOAST =================
function showToast(msg, success = true) {
  const toast = document.getElementById("toast");

  toast.textContent = msg;
  toast.style.background = success ? "#16a34a" : "#dc2626";

  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}