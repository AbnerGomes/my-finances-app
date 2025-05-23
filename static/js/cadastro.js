const telefoneInput = document.getElementById("telefone");

telefoneInput.addEventListener("input", function(e) {
  let valor = e.target.value.replace(/\D/g, ""); // remove tudo que não for dígito

  if (valor.length > 11) valor = valor.slice(0, 11);

  if (valor.length <= 10) {
    // Formato (XX) XXXX-XXXX
    valor = valor.replace(/(\d{2})(\d{4})(\d{0,4})/, "($1) $2-$3");
  } else {
    // Formato (XX) XXXXX-XXXX
    valor = valor.replace(/(\d{2})(\d{5})(\d{0,4})/, "($1) $2-$3");
  }

  e.target.value = valor;
});

function validarTelefone() {
  const valor = telefoneInput.value;
  const regex = /^\(\d{2}\)\s?\d{4,5}-\d{4}$/;
  if (!regex.test(valor)) {
    alert("Digite um número válido no formato (11) 91234-5678");
    return false;
  }
  return true;
}