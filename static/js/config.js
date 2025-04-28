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
    const modal = document.getElementById('modal-delecao-ok');
    modal.style.display = 'block';
});