document.addEventListener('click', function (event) {
    //deletar  
    if (event.target && event.target.classList.contains('footer-icon')) {
        const modal = document.getElementById('modal-confirmar-exclusao');
        // const fecharModal = document.getElementById('fechar-modal-excluir');
        // const confirmarBtn = document.getElementById('confirmar-exclusao');

        // Abre o modal ao clicar na engrenagem
        modal.style.display = 'block';

    }
});    


document.addEventListener('DOMContentLoaded', function () {
    // só existe em configuracoes_exclusao.html (tela de "conta excluída");
    // config.js também é carregado em configuracoes.html, que não tem
    // esse modal — sem o guard, isso jogava um erro de JS toda vez que
    // a tela normal de Configurações abria
    const modal = document.getElementById('modal-delecao-ok');
    if (modal) modal.style.display = 'block';

    // "Ocultar valores ao abrir" — preferência lida pela home (scripts.js)
    // pra já abrir com o olhinho fechado, quando marcada
    const chkOcultar = document.getElementById('chk-ocultar-valores-padrao');
    if (chkOcultar) {
        chkOcultar.checked = localStorage.getItem('ocultarValoresPadrao') === 'S';
        chkOcultar.addEventListener('change', function () {
            localStorage.setItem('ocultarValoresPadrao', chkOcultar.checked ? 'S' : 'N');
        });
    }

    // WhatsApp: benefício de plano pago — quem não assinou vê a seção
    // travada; toca e mostra um aviso em vez de deixar mexer
    const cardWhatsappEmBreve = document.getElementById('whatsapp-em-breve');
    if (cardWhatsappEmBreve) {
        cardWhatsappEmBreve.addEventListener('click', function () {
            showToast('Assine um plano pago para vincular seu WhatsApp.');
        });
    }

    // WhatsApp: quem já tem plano vê o formulário liberado — salvar/
    // desvincular via fetch (em vez de recarregar a página inteira) só
    // pra poder mostrar o toast de sucesso, igual ao aviso de bloqueio
    const formWhatsapp = document.getElementById('form-whatsapp');
    if (formWhatsapp) {
        formWhatsapp.addEventListener('submit', async function (e) {
            e.preventDefault();

            const botao = formWhatsapp.querySelector('.whatsapp-btn-salvar');
            if (botao) botao.disabled = true;

            try {
                const resposta = await fetch(formWhatsapp.action, {
                    method: 'POST',
                    body: new FormData(formWhatsapp),
                });
                const corpo = await resposta.json();
                showToast(resposta.ok ? corpo.mensagem : (corpo.erro || 'Erro ao salvar'), resposta.ok);
            } catch {
                showToast('Erro de conexão. Tenta de novo.', false);
            } finally {
                if (botao) botao.disabled = false;
            }
        });
    }
});

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