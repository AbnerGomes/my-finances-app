var donutChart = null; // Variável global inicializada

var barChart = null;

let periodoAtual = 'mesatual';

// Controle de exibição do saldo (olho de mostrar/ocultar)
let saldoOculto = false;
let saldoAtualFormatado = 'R$ 0,00';

function filtrarGastosBtn(periodo) {

    periodoAtual = periodo; // guarda o período

    let name = document.getElementById('current-username').textContent;

    let isCasal = name == 'Casal' ? 'S' : 'N'

    filtrarGastos(periodo, isCasal)

}

// Clareia (quantidade > 0) ou escurece (quantidade < 0) uma cor hex, usada
// para gerar o gradiente de cada fatia do donut (efeito de profundidade/3D).
function ajustarCor(hex, quantidade) {
    let cor = String(hex).replace('#', '');
    if (cor.length === 3) cor = cor.split('').map(c => c + c).join('');
    if (cor.length !== 6) return hex;

    const num = parseInt(cor, 16);
    let r = (num >> 16) & 255;
    let g = (num >> 8) & 255;
    let b = num & 255;

    const ajustar = (canal) => quantidade >= 0
        ? canal + (255 - canal) * quantidade
        : canal * (1 + quantidade);

    r = Math.min(255, Math.max(0, Math.round(ajustar(r))));
    g = Math.min(255, Math.max(0, Math.round(ajustar(g))));
    b = Math.min(255, Math.max(0, Math.round(ajustar(b))));

    return `rgb(${r}, ${g}, ${b})`;
}

// Gera um gradiente radial suave (mais claro no canto superior esquerdo,
// mais escuro na borda) para dar uma sensação de volume/sobreposição a
// cada fatia do donut, em vez de uma cor chapada.
function gerarGradienteFatia(ctx, corBase) {
    const w = ctx.canvas.width || 260;
    const h = ctx.canvas.height || 260;
    const raio = Math.max(w, h) * 0.6;

    const grad = ctx.createRadialGradient(
        w * 0.38, h * 0.34, raio * 0.05,
        w * 0.5, h * 0.5, raio
    );
    grad.addColorStop(0, ajustarCor(corBase, 0.35));
    grad.addColorStop(0.55, corBase);
    grad.addColorStop(1, ajustarCor(corBase, -0.22));
    return grad;
}

// Plugin do Chart.js: desenha uma sombra suave e desfocada sob o donut,
// dando a impressão de que ele "flutua" sobre o card (efeito 3D/camadas).
const donutSombraPlugin = {
    id: 'donutSombra3d',
    beforeDatasetsDraw(chart) {
        const meta = chart.getDatasetMeta(0);
        const arco = meta && meta.data && meta.data[0];
        if (!arco) return;

        const { ctx } = chart;
        const cx = arco.x;
        const cy = arco.y;
        const raioExterno = arco.outerRadius;

        ctx.save();
        ctx.beginPath();
        ctx.ellipse(cx, cy + raioExterno * 0.14, raioExterno * 0.94, raioExterno * 0.8, 0, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(3, 7, 18, 0.5)';
        try {
            ctx.filter = 'blur(12px)';
        } catch (e) { /* navegadores sem suporte a filter em canvas ignoram a sombra */ }
        ctx.fill();
        ctx.restore();
    }
};

// Mesma paleta usada nos badges de despesas.html/extrato.html (.categoria-X
// em comum.css) — cores pastel/vibrantes escolhidas pra ler bem sobre o
// fundo escuro de qualquer tema do app.
const coresCategorias = {
  'Alimentação': '#facc15',
  'Ifood': '#fb923c',
  'Entretenimento e Lazer': '#c084fc',
  'Entretenimento': '#c084fc', // compat com registros antigos (pré-renomeação)
  'Mobilidade': '#818cf8',
  'Saúde e Beleza': '#4ade80',
  'Saúde': '#4ade80', // compat com registros antigos (pré-renomeação)
  'Moradia': '#60a5fa',
  'Outros': '#67e8f9',
  'Dívidas': '#f87171',
  'Educação': '#5eead4',
  'Pets': '#deb887',
  'Investimentos': '#a3e635',
  'Telefonia': '#38bdf8'
};

// Ícones (Material Icons) usados na lista de categorias da nova home
const iconesCategorias = {
  'Alimentação': 'restaurant',
  'Ifood': 'delivery_dining',
  'Entretenimento e Lazer': 'sports_esports',
  'Entretenimento': 'sports_esports', // compat com registros antigos (pré-renomeação)
  'Mobilidade': 'directions_car',
  'Saúde e Beleza': 'favorite',
  'Saúde': 'favorite', // compat com registros antigos (pré-renomeação)
  'Moradia': 'home',
  'Outros': 'category',
  'Dívidas': 'credit_card',
  'Educação': 'school',
  'Pets': 'pets',
  'Investimentos': 'trending_up',
  'Telefonia': 'smartphone'
};

// Atualiza o "Saldo total" (card de cima) e o valor central do donut,
// respeitando o estado de oculto/visível.
function renderSaldoTotal() {
  const el = document.getElementById('saldo-total');
  const elCenter = document.getElementById('donut-center-saldo');
  const texto = saldoOculto ? 'R$ ••••••' : saldoAtualFormatado;

  if (el) el.textContent = texto;
  if (elCenter) elCenter.textContent = texto;
}

// Monta a lista de categorias com barra de progresso (baseada nos
// mesmos dados que já alimentam o donut chart, sem chamada extra ao backend)
function renderCategorias(categorias, valores) {
  const container = document.getElementById('categorias-list');
  if (!container) return;

  if (!categorias || categorias.length === 0) {
    container.innerHTML = '<p class="categorias-vazio">Nenhum gasto neste período.</p>';
    return;
  }

  const total = valores.reduce((acc, v) => acc + parseFloat(v || 0), 0) || 1;

  let html = '';

  categorias.forEach((cat, i) => {
    const valor = parseFloat(valores[i] || 0);
    const pct = Math.min(Math.round((valor / total) * 100), 100);
    const cor = coresCategorias[cat] || '#8A93B8';
    const icone = iconesCategorias[cat] || 'category';
    const valorFormatado = valor.toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });

    html += `
      <div class="categoria-row">
        <div class="categoria-info">
          <span class="categoria-icone material-icons" style="color:${cor};">${icone}</span>
          <span class="categoria-nome">${cat}</span>
          <span class="categoria-valor">R$ ${valorFormatado}</span>
        </div>
        <div class="categoria-bar-track">
          <div class="categoria-bar-fill" style="width:${pct}%; background:${cor};"></div>
        </div>
        <span class="categoria-pct">${pct}%</span>
      </div>`;
  });

  container.innerHTML = html;
}

// Função para buscar e atualizar os dados do gráfico
function filtrarGastos(periodo, isCasal) {
    var ctx = document.getElementById('donutChart').getContext('2d');

    $.getJSON(`/filtrarGastos/${periodo}/${isCasal}`, function (dados) {

        const mensagem = document.getElementById("mensagem");
        const total = document.getElementById("total");

        if (dados.length === 0 || dados === null || dados === undefined) {

            // MENSAGEM
            const modal_mensagem = document.getElementById('modal-mensagem');
            modal_mensagem.style.display = 'block';

            mensagem.innerHTML = "Nenhum gasto encontrado para esse período.";
            total.style.display = "none";

            renderCategorias([], []);
        }
        else {
            total.style.display = "block";
            mensagem.style.display = "none";

            let categorias = dados.map(item => item.categoria);
            let valores = dados.map(item => item.valor);

            let cores = categorias.map(cat =>
                coresCategorias[cat] || '#cccccc'
            );

            donutChart.data.labels = categorias;
            donutChart.data.datasets[0].data = valores;
            donutChart.data.datasets[0].backgroundColor =
                cores.map(cor => gerarGradienteFatia(ctx, cor));

            donutChart.update();

            renderCategorias(categorias, valores);

            // Calcula e mostra o total
            let totalGasto = valores.reduce((acc, val) => acc + parseFloat(val || 0), 0);

            periodo = periodo == 'mesanterior'
                ? 'mesanterior'
                : 'mesatual';

            // buscar receitas do backend
            fetch(`/total_saldo_mes?periodo=${periodo}&isCasal=${isCasal}`)
                .then(res => res.json())
                .then(data => {

                    let totalReceitas = parseFloat(data.total_receitas || 0);
                    let totalGastos = parseFloat(data.total_gastos || 0);

                    // Atualiza gastos
                    document.getElementById("total-gastos").innerText =
                        totalGastos.toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });

                    document.getElementById("total-receitas").innerText =
                        totalReceitas.toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });

                    let saldo = totalReceitas - totalGastos; // total do mês

                    saldoAtualFormatado = 'R$ ' + saldo.toLocaleString('pt-BR', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });

                    renderSaldoTotal();

                    const corSaldo = saldo >= 0 ? '#22c55e' : '#fb923c';
                    const saldoEl = document.getElementById("saldo-total");
                    const donutCenterEl = document.getElementById("donut-center-saldo");

                    if (saldoEl) saldoEl.style.color = corSaldo;
                    if (donutCenterEl) donutCenterEl.style.color = corSaldo;
                });

            let totalFormatado = totalGasto.toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
            document.getElementById("valor-total").innerText = totalFormatado;

            let mesSelecionado = document.getElementById("resumo-titulo");
            if (mesSelecionado) {
                mesSelecionado.innerText =
                    periodo == 'mesanterior'
                        ? 'Resumo do mês anterior'
                        : 'Visão geral do mês';
            }
        }
    });
}

function filtrarGastosMensais(isCasal) {
    var ctx = document.getElementById('barChart').getContext('2d');

    $.getJSON(`/filtrarGastosMensais/${isCasal}`, function (dados) {

        if (dados.length === 0 || dados === null || dados === undefined) {
            // sem dados — mantém o gráfico como está
        }
        else {
            let mes_ano = dados.map(item => item.mes_ano);
            let valores = dados.map(item => item.valor);

            barChart.data.labels = mes_ano;
            barChart.data.datasets[0].data = valores;
            barChart.update();
        }
    });
}

function atualizarTemaGraficos() {

    const primaryColor = getComputedStyle(document.body)
        .getPropertyValue('--primary')
        .trim();

    const primaryLight = getComputedStyle(document.body)
        .getPropertyValue('--primary-light')
        .trim();

    // BAR CHART
    if (barChart) {

        const ctx = barChart.ctx;
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);

        gradient.addColorStop(0, primaryLight);
        gradient.addColorStop(1, primaryColor);

        barChart.data.datasets[0].backgroundColor = gradient;
        barChart.data.datasets[0].borderColor = primaryColor;
        barChart.data.datasets[0].borderRadius = 12;
        barChart.data.datasets[0].borderSkipped = false;

        barChart.update();
    }
}

document.addEventListener("DOMContentLoaded", function () {

    // Só respeita o modo Casal salvo se esta conta realmente tiver um
    // cônjuge vinculado (pill "Casal" presente no DOM); caso contrário
    // força Individual, mesmo que tenha ficado salvo de outra conta/sessão.
    const pillCasalExiste = !!document.getElementById('pill-casal');
    const modoInicial = (pillCasalExiste && typeof getModoSalvo === 'function')
        ? getModoSalvo()
        : 'N';

    filtrarGastos('mesatual', modoInicial);
    filtrarGastosMensais(modoInicial);

    const pillIndividualInit = document.getElementById('pill-individual');
    const pillCasalInit = document.getElementById('pill-casal');
    if (pillIndividualInit) pillIndividualInit.classList.toggle('active', modoInicial !== 'S');
    if (pillCasalInit) pillCasalInit.classList.toggle('active', modoInicial === 'S');

    const userIconInit = document.getElementById('user-icon');
    const userIcon1Init = document.getElementById('user-icon1');
    const glifoInicial = modoInicial === 'S' ? 'people' : 'person';
    if (userIconInit) userIconInit.textContent = glifoInicial;
    if (userIcon1Init) userIcon1Init.textContent = glifoInicial;

    var ctx = document.getElementById('donutChart');

    if (!ctx) {
        console.error("Erro: Elemento 'donutChart' não encontrado!");
        return;
    }

    if (donutChart) {
        donutChart.destroy();
    }

    const ctxDonut2d = ctx.getContext('2d');
    const coresIniciais = ['#facc15', '#fb923c', '#c084fc', '#818cf8', '#4ade80', '#60a5fa', '#67e8f9', '#f87171', '#5eead4', '#deb887'];
    const dnaCard = getComputedStyle(document.body).getPropertyValue('--dna-card').trim() || '#141c3f';

    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Alimentação', 'Ifood', 'Entretenimento e Lazer', 'Mobilidade', 'Saúde e Beleza', 'Moradia', 'Outros', 'Dívidas', 'Educação', 'Pets'],
            datasets: [{
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                backgroundColor: coresIniciais.map(cor => gerarGradienteFatia(ctxDonut2d, cor)),
                borderColor: dnaCard,
                borderWidth: 3,
                borderRadius: 6,
                spacing: 3,
                hoverOffset: 10,
                hoverBorderColor: dnaCard
            }]
        },
        options: {
            cutout: '72%',
            animation: {
                animateScale: true,
                duration: 900,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        },
        plugins: [donutSombraPlugin]
    });

    // gráfico de barras
    var ctxBar = document.getElementById('barChart').getContext('2d');

    const primaryColor = getComputedStyle(document.body)
        .getPropertyValue('--primary')
        .trim();

    const primaryLight = getComputedStyle(document.body)
        .getPropertyValue('--primary-light')
        .trim();

    const gradient = ctxBar.createLinearGradient(0, 0, 0, 350);
    gradient.addColorStop(0, primaryLight);
    gradient.addColorStop(1, primaryColor);

    barChart = new Chart(ctxBar, {
        type: 'bar',
        data: {
            labels: ['Jan/2025', 'Fev/2025', 'Mar/2025', 'Abr/2025', 'Mai/2025', 'Jun/2025', 'Jul/2025'],
            datasets: [{
                label: 'Gastos Mensais (R$)',
                data: [100, 5000, 1500, 10000, 1800, 600, 20],
                backgroundColor: gradient,
                borderColor: primaryColor,
                borderWidth: 1,
                borderRadius: 12,
                borderSkipped: false,
                maxBarThickness: 42,
                hoverBorderWidth: 2,
                hoverBorderColor: primaryLight
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 1200,
                easing: 'easeOutQuart'
            },
            indexAxis: 'x',
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#8A93B8',
                        font: {
                            size: 12,
                            weight: 'normal'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#111827',
                    padding: 12,
                    cornerRadius: 10,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Mes/Ano',
                        color: '#8A93B8',
                        font: { size: 10, weight: 'bold' }
                    },
                    ticks: {
                        color: '#8A93B8',
                        font: { size: 10 }
                    },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    title: { display: false },
                    ticks: {
                        color: '#8A93B8',
                        font: { size: 10 }
                    },
                    grid: { display: false }
                }
            },
            layout: {
                padding: { top: 20 }
            }
        }
    });
});

// data atual já carregada no cadastro de gasto
document.addEventListener("DOMContentLoaded", function () {
    let hoje = new Date().toISOString().split('T')[0];
    let campoData = document.getElementById("data");
    if (campoData) {
        campoData.value = hoje;
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.period-chip');

    buttons.forEach(button => {
        button.addEventListener('click', function () {
            buttons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });

    let name = document.getElementById('current-username').textContent;
    let isCasal = name == 'Casal' ? 'S' : 'N'

    if (isCasal == 'S') {
        document.getElementById('user-icon').textContent = 'people';
    }
    else {
        document.getElementById('user-icon').textContent = 'person';
    }

    // botão de ocultar/mostrar o saldo total
    const btnToggleSaldo = document.getElementById('toggle-saldo');
    if (btnToggleSaldo) {
        btnToggleSaldo.addEventListener('click', function () {
            saldoOculto = !saldoOculto;
            const icon = document.getElementById('toggle-saldo-icon');
            if (icon) icon.textContent = saldoOculto ? 'visibility_off' : 'visibility';
            renderSaldoTotal();
        });
    }

    // fecha modais pelo "x"
    document.querySelectorAll('.modal .close').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const modal = btn.closest('.modal');
            if (modal) modal.style.display = 'none';
        });
    });

    // mensagens flash somem sozinhas — ver auto-dismiss em comum.js
    // (movido pra lá pois despesas/extrato também passaram a usá-las)

    // máscara de telefone no modal de cadastro do cônjuge
    const telefoneConjuge = document.getElementById('conjuge-telefone');
    if (telefoneConjuge) {
        telefoneConjuge.addEventListener('input', function (e) {
            let valor = e.target.value.replace(/\D/g, '');
            if (valor.length > 11) valor = valor.slice(0, 11);

            if (valor.length <= 10) {
                valor = valor.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
            } else {
                valor = valor.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
            }
            e.target.value = valor;
        });
    }
});

// Abre o modal de cadastro do cônjuge (botão "Vincular cônjuge" no toggle Individual/Casal)
function abrirModalConjuge() {
    const modal = document.getElementById('modal-conjuge');
    if (modal) modal.style.display = 'flex';
}

document.addEventListener("click", function (e) {
    if (e.target.classList.contains("period-chip")) {
        document.querySelectorAll(".period-chip").forEach(btn => {
            btn.classList.remove("active");
        });
        e.target.classList.add("active");
    }

    if (e.target && e.target.classList.contains('botao-salvar')) {
        const modal_mensagem = document.getElementById('modal-mensagem');
        modal_mensagem.style.display = 'none';
    }

    // fecha o modal ao clicar no fundo escuro (fora do card)
    document.querySelectorAll('.modal').forEach(function (modal) {
        if (e.target === modal) modal.style.display = 'none';
    });
});

// Sobrescreve o changeMode do comum.js: nesta página também precisamos
// recarregar os dois gráficos e alternar o pill "Individual / Casal".
function changeMode(isCasal) {

    if (typeof salvarModo === 'function') salvarModo(isCasal);

    filtrarGastos('mesatual', isCasal);
    filtrarGastosMensais(isCasal);

    const pillIndividual = document.getElementById('pill-individual');
    const pillCasal = document.getElementById('pill-casal');

    if (pillIndividual) pillIndividual.classList.toggle('active', isCasal !== 'S');
    if (pillCasal) pillCasal.classList.toggle('active', isCasal === 'S');

    if (isCasal == 'S') {
        document.getElementById('user-icon').textContent = 'people';
        document.getElementById('user-icon1').textContent = 'people';
    }
    else {
        document.getElementById('user-icon1').textContent = 'person';
        document.getElementById('user-icon').textContent = 'person';
    }
}