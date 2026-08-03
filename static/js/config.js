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

    // WhatsApp: com um número já salvo, o campo nasce travado e o Salvar
    // desabilitado — "Editar" libera os dois pra trocar o número
    const btnEditarWhatsapp = document.getElementById('whatsapp-btn-editar');
    const inputWhatsapp = document.getElementById('whatsapp-telefone-input');
    const btnSalvarWhatsapp = document.getElementById('whatsapp-btn-salvar');
    if (btnEditarWhatsapp && inputWhatsapp && btnSalvarWhatsapp) {
        btnEditarWhatsapp.addEventListener('click', function () {
            inputWhatsapp.removeAttribute('readonly');
            btnSalvarWhatsapp.removeAttribute('disabled');
            inputWhatsapp.focus();
        });
    }
});