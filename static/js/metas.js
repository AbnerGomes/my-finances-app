// ================= TOAST =================
function showToast(msg, success = true) {
  const toast = document.getElementById('toast');
  if (!toast) return;

  toast.textContent = msg;
  toast.style.background = success ? '#16a34a' : '#dc2626';

  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}

// Sobrescreve o changeMode do comum.js: esta página é server-rendered
// (não AJAX como a home), então trocar de modo recarrega a página com
// o parâmetro certo — mesmo padrão de despesas/receitas/extrato.
function changeMode(isCasal) {
  if (typeof salvarModo === 'function') salvarModo(isCasal);
  window.location.href = `/metas?isCasal=${isCasal}`;
}

document.addEventListener('DOMContentLoaded', () => {
  const modalNova = document.getElementById('modal-nova-meta');
  const modalEditar = document.getElementById('modal-editar-meta');

  const abrirBtn = document.getElementById('openModalBtn');
  const fecharNovaBtn = document.getElementById('closeModalBtn');
  const fecharEditarBtn = document.getElementById('closeModalEditarBtn');

  if (abrirBtn) {
    abrirBtn.addEventListener('click', (e) => {
      if (bloquearSePlanoExpirado(e)) return;
      modalNova.style.display = 'block';
    });
  }

  if (fecharNovaBtn) {
    fecharNovaBtn.addEventListener('click', () => { modalNova.style.display = 'none'; });
  }
  if (fecharEditarBtn) {
    fecharEditarBtn.addEventListener('click', () => { modalEditar.style.display = 'none'; });
  }

  window.addEventListener('click', (e) => {
    if (e.target === modalNova) modalNova.style.display = 'none';
    if (e.target === modalEditar) modalEditar.style.display = 'none';
  });

  // ================= CRIAR META =================
  const formNova = document.getElementById('form-nova-meta');
  if (formNova) {
    formNova.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (bloquearSePlanoExpirado(e)) return;

      const dados = new FormData(formNova);
      const categoria = dados.get('categoria');
      const limite = dados.get('limite');

      try {
        const resposta = await fetch('/metas/criar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ categoria, limite }),
        });
        const corpo = await resposta.json();

        if (!resposta.ok) {
          showToast(corpo.erro || 'Erro ao criar meta', false);
          return;
        }

        showToast(corpo.mensagem || 'Meta criada!');
        setTimeout(() => window.location.reload(), 600);
      } catch {
        showToast('Erro de conexão. Tenta de novo.', false);
      }
    });
  }

  // ================= EDITAR META =================
  document.querySelectorAll('.btn-editar-meta').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (bloquearSePlanoExpirado(e)) return;

      document.getElementById('editar-meta-id').value = btn.dataset.id;
      document.getElementById('editar-meta-categoria').textContent = btn.dataset.categoria;
      document.getElementById('editar-meta-limite').value = btn.dataset.limite;
      modalEditar.style.display = 'block';
    });
  });

  const formEditar = document.getElementById('form-editar-meta');
  if (formEditar) {
    formEditar.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (bloquearSePlanoExpirado(e)) return;

      const idMeta = document.getElementById('editar-meta-id').value;
      const limite = document.getElementById('editar-meta-limite').value;

      try {
        const resposta = await fetch(`/metas/${idMeta}/editar`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ limite }),
        });
        const corpo = await resposta.json();

        if (!resposta.ok) {
          showToast(corpo.erro || 'Erro ao atualizar meta', false);
          return;
        }

        showToast(corpo.mensagem || 'Meta atualizada!');
        setTimeout(() => window.location.reload(), 600);
      } catch {
        showToast('Erro de conexão. Tenta de novo.', false);
      }
    });
  }

  // ================= EXCLUIR META =================
  document.querySelectorAll('.btn-excluir-meta').forEach((btn) => {
    btn.addEventListener('click', () => {
      const categoria = btn.dataset.categoria;
      const idMeta = btn.dataset.id;

      mostrarConfirmacao(
        `Quer excluir a meta de "${categoria}"?`,
        async () => {
          try {
            const resposta = await fetch(`/metas/${idMeta}/excluir`, { method: 'POST' });
            const corpo = await resposta.json();

            if (!resposta.ok) {
              showToast(corpo.erro || 'Erro ao excluir meta', false);
              return;
            }

            showToast(corpo.mensagem || 'Meta excluída.');
            setTimeout(() => window.location.reload(), 600);
          } catch {
            showToast('Erro de conexão. Tenta de novo.', false);
          }
        }
      );
    });
  });
});
