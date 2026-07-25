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
});