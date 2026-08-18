from flask import Blueprint, render_template, session, redirect, url_for, request, flash,jsonify, send_file, request, Response, current_app
import os
import json
from service.gasto_service import GastoService
from io import BytesIO
import pandas as pd
from xhtml2pdf import pisa
import random
from datetime import datetime, timedelta
from datetime import date
from collections import defaultdict
import calendar
import locale
import hmac
import hashlib
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from collections import defaultdict

from service.despesa_service import DespesaService

from service.admin_service import AdminService

from service import pagamento_service

from service.categorias import CATEGORIAS_PADRAO

from service.whatsapp_service import WhatsappService
from service.whatsapp_client import enviar_mensagem_whatsapp
from service.claude_agent_service import responder_mensagem
from service.whatsapp_waha_client import enviar_mensagem_whatsapp_waha
from service import tutorial_service
from service import email_service
from service import recuperacao_senha_service
from service import metas_service
from service import insights_service
from service.categorias import icone_categoria

import locale

gasto_bp = Blueprint('gasto', __name__)
despesa_bp = Blueprint('despesa', __name__)
admin_bp = Blueprint('admin', __name__)
whatsapp_bp = Blueprint('whatsapp', __name__)

mensagens_erro = [
    "Usuario ou senha incorretos",
    "Verifique suas credenciais ⚠️",
    #"Cara, olha o que tu ta digitando 🤦🏽‍♂️",
    #"Acesso negado! você é gay 🏳️‍🌈",
    #"Acesso negado! você é gay 🏳️‍🌈",
    #"Acesso negado! você é gay 🏳️‍🌈",
    #"Mds, quem sabe clica em esqueci a senha 🤦🏽‍♂️",
]

# ============================================================
# Token de exportação (Excel/PDF): os botões de exportar abrem a URL
# no navegador do aparelho (fora do WebView do app, pra conseguir usar
# o gerenciador de download nativo — ver flutter_app/lib/main.dart),
# e esse navegador externo não tem o cookie de sessão do WebView. Sem
# um jeito de autenticar essa requisição, session['usuario'] vem vazio
# e a rota quebra com 500. O token abaixo é assinado com a mesma
# secret_key do app, carrega só o usuário, e expira em 10 minutos —
# tempo de sobra pra abrir o link, mas curto o bastante pra não virar
# um link "eterno" se vazar.
def _serializer_exportacao():
    return URLSafeTimedSerializer(current_app.secret_key, salt='exportacao')

def gerar_token_exportacao(usuario):
    return _serializer_exportacao().dumps(usuario)

def validar_token_exportacao(token, max_age=600):
    if not token:
        return None
    try:
        return _serializer_exportacao().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

# ============================================================
# Teste grátis expirado sem assinatura: bloqueia só CADASTRO/EDIÇÃO de
# gasto, despesa e receita — consultar, listar e excluir continuam
# liberados em qualquer plano (ver `precisa_assinar` em gasto_service).
# ============================================================
MENSAGEM_BLOQUEIO_PLANO = 'Seu período de teste terminou. Assine um plano para continuar cadastrando.'

def bloqueado_para_cadastro(usuario):
    return gasto_bp.gasto_service.precisa_assinar(usuario)

# ============================================================
# Compra de plano (Mercado Pago Checkout Pro): só a Play Store pode
# vender assinatura de dentro de um app Android — vender por um
# processador externo enquanto o app está aberto no WebView viola a
# política de pagamentos do Google (é o mesmo caso que derrubou o
# Fortnite da Play Store). Por isso o botão de comprar só aparece pra
# quem está acessando pelo navegador comum, nunca de dentro do app
# empacotado — reconhecido pelo sufixo próprio no User-Agent
# (flutter_app/lib/main.dart).
# ============================================================
def veio_do_app_wrapper():
    return 'DoisNoAzulApp' in request.headers.get('User-Agent', '')

#####ROTAS#####

def init_routes(app, gasto_service,despesa_service,admin_service,whatsapp_service=None):

    app.register_blueprint(gasto_bp)
    app.register_blueprint(despesa_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(whatsapp_bp)

    # Armazena a instância do service dentro do blueprint
    gasto_bp.gasto_service = gasto_service
    despesa_bp.despesa_service = despesa_service
    admin_bp.admin_service = admin_service
    whatsapp_bp.whatsapp_service = whatsapp_service or WhatsappService()

#def configure_routes(app, gasto_service):
@gasto_bp.route('/')
def login():
    # já tem sessão válida (login lembrado) — pula a tela de login e
    # vai direto pra home, em vez de pedir senha de novo toda hora
    if 'usuario' in session:
        return redirect(url_for('gasto.index'))
    return render_template('login.html')

@gasto_bp.route('/voltar_ao_login', methods=['GET','POST'])
def voltar_ao_login():
    return render_template('voltar_ao_login.html')

@gasto_bp.route('/logout')
def logout():
    # signOut() (comum.js) só navegava pra "/" sem nunca limpar a sessão —
    # como "/" já redireciona de volta pro index quando há sessão válida,
    # sair da conta nunca funcionava de verdade, só voltava pra home.
    session.clear()
    return redirect(url_for('gasto.login'))

@gasto_bp.route('/login', methods=['POST'])
def login_post():

    if request.method == 'POST':
        usuario = request.form['email'].lower()

        senha = request.form['senha']

        usuario_bd =  gasto_bp.gasto_service.validar_login(usuario, senha)

        if usuario_bd is not None:

            session.permanent = True  # mantém a sessão entre reaberturas do app (ver PERMANENT_SESSION_LIFETIME)
            session['usuario'] = usuario_bd

            gasto_bp.gasto_service.registrar_login(usuario)

            dados = gasto_bp.gasto_service.filtrarGastos('mesatual',usuario_bd,'N')

            total_gasto = sum([
                float(item.get('valor', 0)) 
                for item in dados 
                if isinstance(item.get('valor', 0), (int, float)) or str(item.get('valor', 0)).replace('.', '', 1).isdigit()
            ])

            return redirect(url_for('gasto.index'))  # Redireciona para a tela principal
        else:
            erro = random.choice(mensagens_erro)
            flash(erro,"danger")
    return render_template('login.html')


@gasto_bp.route('/index')
def index():
   
    if 'usuario' not in session:

        return redirect(url_for('gasto.login'))

    usuario = session['usuario']  # Só acessa se já tiver passado pela verificação

    #verifica se é administrador
    if usuario == 'admin' or usuario == 'adminstrador':
        return redirect(url_for('admin.admin'))

    dados = gasto_bp.gasto_service.filtrarGastos('mesatual',usuario,'N') #verifica_dados_bd(usuario)

    if not dados:
        dados = [(categoria, 0) for categoria in CATEGORIAS_PADRAO]

    total_gasto = sum([
    float(item['valor']) if isinstance(item, dict) and 'valor' in item else float(item[0])
    for item in dados
    if (
        (isinstance(item, dict) and isinstance(item.get('valor', 0), (int, float))) or 
        (isinstance(item, tuple) and len(item) > 0 and str(item[0]).replace('.', '', 1).isdigit())
    )
    ])

    #verifica se é conta casal e exibe dropdon
    tem_conjuge = gasto_bp.gasto_service.tem_conjuge(usuario)

    # depois de 7 dias de conta, sem assinatura ativa, bloqueia o uso
    precisa_assinar = gasto_bp.gasto_service.precisa_assinar(usuario)

    tutorial_visto = tutorial_service.tutorial_visto(usuario, 'home')

    return render_template('index.html',usuario=usuario,temConjuge=tem_conjuge,precisaAssinar=precisa_assinar,tutorialVisto=tutorial_visto)


@gasto_bp.route('/tutorial/marcar_visto', methods=['POST'])
def marcar_tutorial_visto():
    # "não mostrar mais" dos tutoriais/dicas (home, despesas, receitas,
    # extrato) — persiste no banco por usuário+tela, em vez de só
    # localStorage (não sobrevivia de forma confiável dentro do WebView
    # do app Android, a dica voltava a aparecer toda hora)
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    data = request.get_json(silent=True) or {}
    tutorial = data.get('tutorial')

    if not tutorial:
        return jsonify({'erro': 'Dados incompletos'}), 400

    tutorial_service.marcar_tutorial_visto(session['usuario'], tutorial)
    return jsonify({'sucesso': True})

@gasto_bp.route('/cadastrar_gasto', methods=['GET', 'POST'])
def cadastrar_gasto():
    if request.method == 'POST':

        if 'usuario' not in session:
            flash('Você precisa estar logado para adicionar um gasto.')
            return redirect(url_for('gasto.login'))

        if bloqueado_para_cadastro(session['usuario']):
            flash(MENSAGEM_BLOQUEIO_PLANO, 'danger')
            return redirect(url_for('gasto.extrato'))

        gasto = request.form['gasto']
        valor = request.form['valor']
        data = request.form['data']
        categoria = request.form['categoria']

        usuario = session['usuario']

        # Salvar o gasto no banco
        sucesso = gasto_bp.gasto_service.salvar_gasto(gasto, valor, data, categoria,usuario)

        # se o nome/valor bater com alguma despesa do mesmo mês ainda não
        # paga, NÃO marca sozinho (gerava duplicidade) — só acha e devolve
        # pro front perguntar ao usuário se ele quer marcar como paga
        despesa_correspondente = despesa_bp.despesa_service.buscar_despesa_correspondente(usuario, gasto, valor, data)

        return jsonify({'sucesso': True, 'despesaCorrespondente': despesa_correspondente})

    # return render_template('cadastrar_gasto.html')
    return redirect(url_for('gasto.extrato'))

@gasto_bp.route('/cadastrar_gasto_rapido', methods=['POST'])
def cadastrar_gasto_rapido():

    if 'usuario' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    if bloqueado_para_cadastro(session['usuario']):
        return jsonify({'erro': MENSAGEM_BLOQUEIO_PLANO}), 403

    data = request.get_json()

    descricao = data.get('gasto')
    valor = data.get('valor')
    categoria = data.get('categoria')
    usuario = session['usuario']

    hoje = datetime.now().strftime('%Y-%m-%d')

    try:
        gasto_bp.gasto_service.salvar_gasto(descricao, valor, hoje, categoria,usuario)

        # se o nome/valor bater com alguma despesa do mesmo mês ainda não
        # paga, NÃO marca sozinho (gerava duplicidade) — só acha e devolve
        # pro front perguntar ao usuário se ele quer marcar como paga
        despesa_correspondente = despesa_bp.despesa_service.buscar_despesa_correspondente(usuario, descricao, valor, hoje)

        return jsonify({'sucesso': True, 'despesaCorrespondente': despesa_correspondente})

    except Exception as e:
        return jsonify({'erro': 'Falha ao salvar'}), 500

@gasto_bp.route('/extrato', methods=['GET', 'POST'])
@gasto_bp.route('/extrato/<isCasal>', methods=['GET', 'POST'])
def extrato():
    usuario = session['usuario']

    if request.is_json:
        data = request.get_json()
        isCasal = data.get('isCasal')
    else:
        isCasal = request.form.get('isCasal')

    if request.method == 'GET':
        isCasal =request.args.get('isCasal')

    #page = request.args.get('page', 1, type=int)  # Obtém o número da página (padrão é 1)
    #per_page = 12  # Número de gastos por página
    
     # pega data atual
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)

    # Pega filtros da URL ou define padrão
    data_inicio = request.args.get('data_inicio') or primeiro_dia.strftime('%Y-%m-%d')
    data_fim = request.args.get('data_fim') or hoje.strftime('%Y-%m-%d')
    categoria = request.args.get('categoria') or 'Todas'

    # Busca os gastos ordenados do mais recente para o mais antigo
    gastos = gasto_bp.gasto_service.extrato_gastos(usuario,data_inicio,data_fim,categoria,isCasal)  

    total_gastos = len(gastos)

    #acoes rapidas
    acoes = gasto_bp.gasto_service.buscar_acoes_rapidas(usuario)

    #start = (page - 1) * per_page
    #end = start + per_page

    #gastos_pagina = gastos[start:end]

    # Agrupar os gastos por data
    gastos_agrupados = defaultdict(list)
    for gasto in gastos:
       data = gasto[3]  # Supondo que o 4º item (índice 3) seja a data
       gastos_agrupados[data].append(gasto)


    # lista de categorias (filtro só mostra categorias já usadas pelo
    # usuário — e pelo cônjuge, no modo Casal)
    categorias = gasto_bp.gasto_service.get_categorias_disponiveis(usuario, isCasal)

    # categorias padrão + próprias (usadas nos selects de cadastrar/editar gasto)
    categorias_completas = gasto_bp.gasto_service.get_categorias_completas(usuario, isCasal)

    #gastos_pagina = gastos[start:end]

    soma_gastos = 0

    #se for geral do filtro selecionado
    soma_gastos = sum(gasto[2] for gasto in gastos)

    #verifica se é conta casal e exibe dropdon
    tem_conjuge = gasto_bp.gasto_service.tem_conjuge(usuario)

    if isCasal is None:
        isCasal ='N'

    return render_template(
        'extrato.html',
        gastos_agrupados=gastos_agrupados,
        #page=page,
        total=total_gastos,
        #per_page=per_page,
        now=datetime.now(),
        data_inicio=data_inicio,
        data_fim=data_fim,
        categoria= categoria,
        soma_gastos=soma_gastos
        ,usuario =usuario,
        isCasal=isCasal,
        temConjuge=tem_conjuge,
        categorias=categorias,
        categorias_completas=categorias_completas,
        acoes=acoes,
        token_exportacao=gerar_token_exportacao(usuario),
        bloqueadoParaCadastro=bloqueado_para_cadastro(usuario),
        tutorialVisto=tutorial_service.tutorial_visto(usuario, 'extrato')
    )


@gasto_bp.route('/filtrarGastos/<periodo>/<isCasal>')
def filtrar(periodo,isCasal):
    usuario = session['usuario']

    dados = gasto_bp.gasto_service.filtrarGastos(periodo,usuario,isCasal)
    return jsonify(dados)

@gasto_bp.route('/filtrarGastosMensais/<isCasal>')
def filtrarMesAno(isCasal):
    usuario = session['usuario']

    if isCasal is None:
    
        if request.is_json:
            data = request.get_json()
            isCasal = data.get('isCasal')
        else:
            isCasal = request.form.get('isCasal')

        if request.method == 'GET':
            isCasal =request.args.get('isCasal')

    dados = gasto_bp.gasto_service.filtrarGastosMensais(usuario,isCasal)
    return jsonify(dados)


@gasto_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        pronome = request.form.get("pronome", "")

        if pronome not in ('Ele/Dele', 'Ela/Dela'):
            flash("Selecione um gênero válido.", "danger")
            return redirect(url_for('gasto.cadastro'))

        try:
            sucesso = gasto_bp.gasto_service.cadastrar_usuario(nome, email, telefone, senha, pronome)
        except Exception:
            flash("Não foi possível criar a conta. Tente novamente. 😓", "danger")
            return redirect(url_for('gasto.cadastro'))

        if not sucesso:
            flash("Esse e-mail já está cadastrado! 🤦🏽‍♂️", "danger")
            return redirect(url_for('gasto.cadastro'))

        flash("Conta criada com sucesso! Faça login para continuar. 😄", "success")
        return redirect(url_for('gasto.login'))

    return render_template("cadastro.html")


@gasto_bp.route('/esqueci', methods=['GET', 'POST'])
def esqueci():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if email and recuperacao_senha_service.email_existe(email):
            codigo = recuperacao_senha_service.gerar_codigo(email)
            email_service.enviar_email(
                email,
                'Código de recuperação — Dois no Azul',
                f'Seu código de recuperação de senha é: {codigo}\n\n'
                f'Ele vale por {recuperacao_senha_service.VALIDADE_MINUTOS} minutos. '
                f'Se você não pediu isso, pode ignorar este e-mail.',
                corpo_html=(
                    f'<p>Seu código de recuperação de senha do <strong>Dois no Azul</strong> é:</p>'
                    f'<p style="font-size:28px; font-weight:700; letter-spacing:4px;">{codigo}</p>'
                    f'<p>Ele vale por {recuperacao_senha_service.VALIDADE_MINUTOS} minutos. '
                    f'Se você não pediu isso, pode ignorar este e-mail.</p>'
                ),
            )

        # mesma mensagem independente do e-mail existir ou não — evita
        # que alguém use essa tela pra descobrir quais e-mails têm conta
        flash('Se esse e-mail estiver cadastrado, você vai receber um código em instantes.', 'success')
        return redirect(url_for('gasto.redefinir_senha', email=email))

    return render_template("esqueci.html")


@gasto_bp.route('/redefinir_senha', methods=['GET', 'POST'])
def redefinir_senha():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        codigo = request.form.get('codigo', '').strip()
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not email or not codigo or not nova_senha:
            flash('Preencha todos os campos.', 'danger')
            return redirect(url_for('gasto.redefinir_senha', email=email))

        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('gasto.redefinir_senha', email=email))

        if len(nova_senha) < 6:
            flash('A senha precisa ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('gasto.redefinir_senha', email=email))

        id_codigo = recuperacao_senha_service.verificar_codigo(email, codigo)

        if not id_codigo:
            flash('Código inválido ou expirado. Peça um novo código.', 'danger')
            return redirect(url_for('gasto.redefinir_senha', email=email))

        recuperacao_senha_service.redefinir_senha(email, nova_senha)
        recuperacao_senha_service.marcar_codigo_usado(id_codigo)

        flash('Senha alterada com sucesso! Faça login com a nova senha.', 'success')
        return redirect(url_for('gasto.login'))

    email = request.args.get('email', '')
    return render_template("redefinir_senha.html", email=email)


@gasto_bp.route('/politica-privacidade')
def politica_privacidade():
    # pública — não depende de login, exigido pela Google Play
    return render_template("politica_privacidade.html")


@gasto_bp.route('/planos')
def planos():
    if 'usuario' not in session:
        return redirect(url_for('gasto.login'))

    return render_template("planos.html", dentroDoApp=veio_do_app_wrapper())


@gasto_bp.route('/assinar_plano/<tipo>')
def assinar_plano(tipo):
    if 'usuario' not in session:
        return redirect(url_for('gasto.login'))

    # comprar só é permitido pelo navegador comum — ver veio_do_app_wrapper()
    if veio_do_app_wrapper():
        flash('Para assinar um plano, abra o Dois no Azul pelo navegador do seu celular ou computador.', 'danger')
        return redirect(url_for('gasto.planos'))

    resultado = gasto_bp.gasto_service.get_usuario_by_name(session['usuario'])
    usuario_email = resultado[0] if resultado else None

    if not usuario_email:
        flash('Não foi possível identificar sua conta.', 'danger')
        return redirect(url_for('gasto.planos'))

    base_url = request.url_root.rstrip('/')
    preferencia = pagamento_service.criar_preferencia_pagamento(tipo, usuario_email, base_url)

    if not preferencia or 'init_point' not in preferencia:
        flash('Não foi possível iniciar o pagamento agora. Tente novamente em instantes.', 'danger')
        return redirect(url_for('gasto.planos'))

    return redirect(preferencia['init_point'])


@gasto_bp.route('/gerar_checkout/<tipo>', methods=['POST'])
def gerar_checkout(tipo):
    # chamado via fetch de DENTRO do app (WebView), autenticado com a
    # sessão de quem está logado ali — devolve a URL de pagamento pronta
    # (init_point do Mercado Pago) em vez de redirecionar, porque quem
    # chama essa rota não vai navegar pra ela: o Flutter (main.dart) pega
    # essa URL e abre num navegador externo de verdade (dnaexterno://).
    # Isso evita o problema de abrir o navegador externo direto em
    # /assinar_plano — o navegador externo não tem a sessão do app (é
    # outro contexto, cookie não é compartilhado), então cairia na tela
    # de login em vez de ir direto pro checkout.
    if 'usuario' not in session:
        return jsonify({'erro': 'Sessão expirada, entra no app de novo.'}), 401

    resultado = gasto_bp.gasto_service.get_usuario_by_name(session['usuario'])
    usuario_email = resultado[0] if resultado else None

    if not usuario_email:
        return jsonify({'erro': 'Não foi possível identificar sua conta.'}), 400

    base_url = request.url_root.rstrip('/')
    preferencia = pagamento_service.criar_preferencia_pagamento(tipo, usuario_email, base_url)

    if not preferencia or 'init_point' not in preferencia:
        return jsonify({'erro': 'Não foi possível iniciar o pagamento agora. Tente novamente em instantes.'}), 502

    return jsonify({'checkoutUrl': preferencia['init_point']})


@gasto_bp.route('/pagamento/retorno')
def pagamento_retorno():
    # pra onde o Mercado Pago manda o navegador de volta depois do
    # checkout — a ativação de verdade acontece no webhook (mais abaixo),
    # que é chamado servidor-a-servidor e não depende do usuário
    # completar esse redirecionamento de volta.
    status = request.args.get('status')

    mensagens = {
        'sucesso': ('Pagamento aprovado! Seu plano já deve estar ativo em instantes.', 'success'),
        'pendente': ('Pagamento pendente — assim que for aprovado, seu plano é ativado automaticamente.', 'warning'),
        'falha': ('Pagamento não foi concluído. Você pode tentar novamente quando quiser.', 'danger'),
    }
    mensagem, categoria = mensagens.get(status, ('Retorno do pagamento recebido.', 'info'))
    flash(mensagem, categoria)

    return redirect(url_for('gasto.index'))


@gasto_bp.route('/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    dados = request.get_json(silent=True) or {}
    payment_id = (dados.get('data') or {}).get('id') or request.args.get('id') or request.args.get('data.id')

    if not payment_id:
        return '', 200

    try:
        pagamento = pagamento_service.buscar_pagamento(payment_id)

        if pagamento and pagamento.get('status') == 'approved':
            referencia = json.loads(pagamento.get('external_reference') or '{}')
            usuario_email = referencia.get('usuario')
            tipo_plano = referencia.get('plano')

            if usuario_email and tipo_plano:
                pagamento_service.ativar_assinatura(usuario_email, tipo_plano)
    except Exception as e:
        print('Erro processando webhook Mercado Pago:', e)

    # sempre 200 — senão o Mercado Pago fica reenviando o mesmo evento
    return '', 200


@gasto_bp.route('/cadastrar_conjuge', methods=['POST'])
def cadastrar_conjuge():
    if 'usuario' not in session:
        return redirect(url_for('gasto.login'))

    usuario = session['usuario']

    nome = request.form.get('nome', '').strip()
    email = request.form.get('email', '').strip()
    telefone = request.form.get('telefone', '').strip()
    senha = request.form.get('senha', '')
    pronome = request.form.get('pronome', '')

    if not nome or not email or not senha or pronome not in ('Ele/Dele', 'Ela/Dela'):
        flash("Preencha todos os campos corretamente.", "danger")
        return redirect(url_for('gasto.index'))

    try:
        sucesso = gasto_bp.gasto_service.cadastrar_conjuge(usuario, nome, email, telefone, senha, pronome)
    except Exception:
        flash("Não foi possível cadastrar o cônjuge. Tente novamente.", "danger")
        return redirect(url_for('gasto.index'))

    if sucesso:
        flash("Cônjuge cadastrado com sucesso! 😄", "success")
    else:
        flash("Esse email já está cadastrado! 🤦🏽‍♂️", "danger")

    return redirect(url_for('gasto.index'))

@gasto_bp.route('/editar_gasto', methods=[ 'POST'])
def editar_gasto():

    if 'usuario' not in session:
        flash('Você precisa estar logado para adicionar um gasto.')
        return redirect(url_for('gasto.login'))

    if bloqueado_para_cadastro(session['usuario']):
        flash(MENSAGEM_BLOQUEIO_PLANO, 'danger')
        return redirect(url_for('gasto.extrato'))

    gasto = request.form['gasto']
    valor = request.form['valor']
    data = request.form['data']
    categoria = request.form['categoria']

    id = request.form['id']

    usuario = session['usuario']

    sucesso = gasto_bp.gasto_service.editar_gasto(gasto,categoria,valor,data,id,usuario)

    if not sucesso:
        flash('Você só pode editar os seus próprios gastos.', 'danger')

    return redirect(url_for('gasto.extrato'))

@gasto_bp.route('/deletar_gasto', methods=['POST'])
def deletar_gasto():

    if 'usuario' not in session:
        flash('Você precisa estar logado para deletar um gasto.')
        return redirect(url_for('gasto.login')) 

    id_gasto = request.form.get('id')

    if not id_gasto:
        # flash('ID do gasto não fornecido!', 'danger')
        return redirect(url_for('gasto.extrato'))

    usuario = session['usuario']

    try:
        sucesso = gasto_bp.gasto_service.deletar_gasto(id_gasto, usuario)
        if not sucesso:
            flash('Você só pode excluir os seus próprios gastos.', 'danger')
    except Exception as e:
        print("Erro ao deletar gasto:", e)
        flash('Erro ao tentar deletar o gasto. 😓', 'danger')

    return redirect(url_for('gasto.extrato'))


@despesa_bp.route('/despesas', methods=['GET','POST'])
@despesa_bp.route('/despesas/<isCasal>', methods=['GET','POST'])
def despesas(): 
    usuario = session['usuario']
    
    if request.is_json:
        data = request.get_json()
        isCasal = data.get('isCasal')
    else:
        isCasal = request.form.get('isCasal')

    if request.method == 'GET':
        isCasal =request.args.get('isCasal')

    # pega data atual
    hoje = date.today()
    primeiro_mes = hoje.replace(day=1)

    mes_atual = hoje.strftime('%Y-%m')

    pendentes_antigos = request.args.get('pendentes_antigos')

    # Pega o filtro vindo da URL ou usa o primeiro dia do mês atual
    #mes_ano_str = request.args.get('mes_ano') or primeiro_mes.strftime('%Y-%m')
    if pendentes_antigos == 'S':
        hoje = datetime.today()
        primeiro_dia_mes = hoje.replace(day=1)
        mes_anterior = (primeiro_dia_mes - timedelta(days=1)).strftime('%Y-%m')

        mes_ano_str = mes_anterior
    else:
        mes_ano_str = request.args.get('mes_ano') or primeiro_mes.strftime('%Y-%m')

    # Busca os gastos ordenados do mais recente para o mais antigo
    despesas = despesa_bp.despesa_service.busca_despesas(usuario,mes_ano_str[-7:],'Todas',isCasal)  

    tem_conjuge = despesa_bp.despesa_service.tem_conjuge(usuario)

    tem_pendencias = despesa_bp.despesa_service.tem_pendencias_mes_anterior(usuario, isCasal)

    if mes_ano_str < mes_atual:
        tem_pendencias = False
    
    soma_despesas = 0

    soma_despesas = sum(despesa[2] for despesa in despesas)

    if isCasal is None:
        isCasal ='N'

    categorias_completas = despesa_bp.despesa_service.get_categorias_completas(usuario, isCasal)

    return render_template(
        'despesas.html',
        despesas=despesas,
        mes_ano=mes_ano_str[-7:]  # yyyy-mm para o input month
        ,usuario=usuario,
        isCasal=isCasal,
        temConjuge=tem_conjuge,
        somaDespesas=soma_despesas,
        temPendencias=tem_pendencias,
        categorias_completas=categorias_completas,
        bloqueadoParaCadastro=bloqueado_para_cadastro(usuario),
        tutorialVisto=tutorial_service.tutorial_visto(usuario, 'despesas')
    )

@despesa_bp.route('/atualizar_status', methods=['POST'])
def atualizar_status():
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    data = request.get_json()
    id_despesa = data.get('id_despesa')
    novo_status = data.get('novo_status')

    if not id_despesa or not novo_status:
        return jsonify({'erro': 'Dados incompletos'}), 400

    # Chama método da camada service para atualizar no banco
    resultado = despesa_bp.despesa_service.atualizar_status(id_despesa, novo_status, session['usuario'])

    if resultado.get('sucesso'):
        return jsonify({
            'mensagem': 'Status atualizado com sucesso',
            # true só quando REALMENTE virou Pago agora (não estava
            # Pago antes) — é o gatilho pro front perguntar se quer
            # lançar um gasto correspondente
            'virouPago': resultado.get('virouPago', False),
            'despesa': resultado.get('despesa'),
            'idDespesa': id_despesa,
        })
    else:
        return jsonify({'erro': 'Você só pode alterar o status das suas próprias despesas.'}), 403


@despesa_bp.route('/criar_gasto_da_despesa', methods=['POST'])
def criar_gasto_da_despesa():
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    if bloqueado_para_cadastro(session['usuario']):
        return jsonify({'erro': MENSAGEM_BLOQUEIO_PLANO}), 403

    data = request.get_json()
    id_despesa = data.get('id_despesa')

    if not id_despesa:
        return jsonify({'erro': 'Dados incompletos'}), 400

    sucesso = despesa_bp.despesa_service.criar_gasto_da_despesa(id_despesa, session['usuario'])

    if sucesso:
        return jsonify({'mensagem': 'Gasto lançado com sucesso'})
    return jsonify({'erro': 'Não foi possível lançar o gasto'}), 400


@despesa_bp.route('/marcar_despesa_paga', methods=['POST'])
def marcar_despesa_paga():
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    data = request.get_json()
    id_despesa = data.get('id_despesa')

    if not id_despesa:
        return jsonify({'erro': 'Dados incompletos'}), 400

    sucesso = despesa_bp.despesa_service.marcar_despesa_paga_por_id(id_despesa, session['usuario'])

    if sucesso:
        return jsonify({'mensagem': 'Despesa marcada como paga'})
    return jsonify({'erro': 'Não foi possível marcar a despesa como paga'}), 400


@despesa_bp.route('/replicar_despesa', methods=['POST'])
def replicar_despesa():
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    if bloqueado_para_cadastro(session['usuario']):
        return jsonify({'erro': MENSAGEM_BLOQUEIO_PLANO}), 403

    data = request.get_json()
    id_despesa = data.get('id_despesa')

    if not id_despesa:
        return jsonify({'erro': 'Dados incompletos'}), 400

    sucesso = despesa_bp.despesa_service.replicar_despesa_mes_seguinte(id_despesa, session['usuario'])

    if sucesso:
        return jsonify({'mensagem': 'Despesa replicada para o mês seguinte'})
    else:
        return jsonify({'erro': 'Você só pode replicar suas próprias despesas.'}), 403



@despesa_bp.route('/cadastrar_despesa', methods=['POST','GET'])
def cadastrar_despesa():

    #if request.method == 'POST':
    if 'usuario' not in session:
        flash('Você precisa estar logado para adicionar um gasto.')
        return redirect(url_for('gasto.login'))

    if bloqueado_para_cadastro(session['usuario']):
        flash(MENSAGEM_BLOQUEIO_PLANO, 'danger')
        return redirect(url_for('despesa.despesas'))

    despesa = request.form['despesa']
    valor = request.form['valor']

    tipo_despesa = request.form['tipo_despesa']
    data = request.form['mes_ano']
    
    categoria = request.form['categoria']
    
    usuario = session['usuario']
    
    replicar_ano = request.form.get('replicar_ano') == 'on'

    if tipo_despesa == 'Fixa':
        tipo_despesa = 'F'
    elif tipo_despesa == 'Variável':
        tipo_despesa = 'V'
    elif tipo_despesa == 'Exceção':
        tipo_despesa = 'E'

    # Salvar o gasto no banco (Fixa + "replicar" cria uma linha pro mês
    # selecionado e mais uma pra cada mês seguinte até dezembro)
    if tipo_despesa == 'F' and replicar_ano:
        despesa_bp.despesa_service.salvar_despesa_replicada(despesa, valor, data, categoria, usuario, tipo_despesa)
    else:
        despesa_bp.despesa_service.salvar_despesa(despesa, valor, data, categoria,usuario,tipo_despesa)
    #flash('Despesa cadastrada com sucesso!', 'success')

    return redirect(url_for('despesa.despesas'))

    #return render_template('despesas.html',usuario=usuario)  


@despesa_bp.route('/editar_despesa', methods=[ 'POST'])
def editar_despesa():

    if 'usuario' not in session:
        flash('Você precisa estar logado para editar uma despesa.')
        return redirect(url_for('gasto.login'))

    if bloqueado_para_cadastro(session['usuario']):
        flash(MENSAGEM_BLOQUEIO_PLANO, 'danger')
        return redirect(url_for('despesa.despesas'))

    despesa = request.form['despesa']
    valor = request.form['valor']
    categoria = request.form['categoria']
    id = request.form['id']

    usuario = session['usuario']

    sucesso = despesa_bp.despesa_service.editar_despesa(despesa,categoria,valor,id,usuario)

    if not sucesso:
        flash('Você só pode editar as suas próprias despesas.', 'danger')

    return redirect(url_for('despesa.despesas'))

@despesa_bp.route('/deletar_despesa', methods=['POST'])
def deletar_despesa():

    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    if request.is_json:
        data = request.get_json()
        id_despesa = data.get('id')
    else:
        id_despesa = request.form.get('id')

    if not id_despesa:
        return jsonify({'erro': 'ID não enviado'}), 400

    usuario = session['usuario']

    try:
        sucesso = despesa_bp.despesa_service.deletar_despesa(id_despesa, usuario)
        if not sucesso:
            return jsonify({'erro': 'Você só pode excluir as suas próprias despesas.'}), 403
        return jsonify({'sucesso': True})
    except Exception as e:
        print("Erro ao deletar:", e)
        return jsonify({'erro': 'Falha ao deletar'}), 500

#exportação
@gasto_bp.route('/exportar/excel')
def exportar_excel():
    usuario = session.get('usuario') or validar_token_exportacao(request.args.get('token'))
    if not usuario:
        return jsonify({'erro': 'Sessão expirada. Volte pro extrato e tente exportar de novo.'}), 401

    if request.is_json:
        data = request.get_json()
        isCasal = data.get('isCasal')
    else:
        isCasal = request.form.get('isCasal')

     # pega data atual
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)

    # Pega filtros da URL ou define padrão
    data_inicio = request.args.get('data_inicio') or primeiro_dia.strftime('%Y-%m-%d')
    data_fim = request.args.get('data_fim') or hoje.strftime('%Y-%m-%d')
    categoria = request.args.get('categoria') or 'Todas'

    # Busca os gastos ordenados do mais recente para o mais antigo
    gastos = gasto_bp.gasto_service.extrato_gastos(usuario,data_inicio,data_fim,categoria,isCasal)  

    colunas = [ 'categoria', 'gasto' ,'valor','data'] 
    gastos_filtrados = [g[:4] for g in gastos]
    df = pd.DataFrame(gastos_filtrados,columns=colunas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extrato')

    output.seek(0)
    return send_file(output, download_name='extrato.xlsx', as_attachment=True)


@gasto_bp.route('/exportar/pdf')
def exportar_pdf():
    usuario = session.get('usuario') or validar_token_exportacao(request.args.get('token'))
    if not usuario:
        return jsonify({'erro': 'Sessão expirada. Volte pro extrato e tente exportar de novo.'}), 401

    if request.is_json:
        data = request.get_json()
        isCasal = data.get('isCasal')
    else:
        isCasal = request.form.get('isCasal')

     # pega data atual
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)

    # Pega filtros da URL ou define padrão
    data_inicio = request.args.get('data_inicio') or primeiro_dia.strftime('%Y-%m-%d')
    data_fim = request.args.get('data_fim') or hoje.strftime('%Y-%m-%d')
    categoria = request.args.get('categoria') or 'Todas'

     # Busca os gastos ordenados do mais recente para o mais antigo
    gastos = gasto_bp.gasto_service.extrato_gastos(usuario,data_inicio,data_fim,categoria,isCasal)  

    soma_gastos = 0

    soma_gastos = sum(gasto[2] for gasto in gastos)

    html = render_template("extrato_pdf.html", dados=gastos,soma_gastos=soma_gastos)
    output = BytesIO()
    pisa.CreatePDF(html, dest=output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='extrato.pdf'
    )

    # # Monta a URL do PDF com os filtros
    # pdf_url = url_for(
    #     'gasto.gerar_pdf',
    #     _external=True,
    #     data_inicio=data_inicio,
    #     data_fim=data_fim,
    #     categoria=categoria,
    #     usuario=usuario,
    #     isCasal=isCasal
    # )
    
    # viewer_url = f"https://docs.google.com/viewer?embedded=true&url={pdf_url}"

    # return redirect(viewer_url)


@gasto_bp.route('/gerar/pdf')
def gerar_pdf():    
    print("#################GERAR################")
    # Pega filtros da URL ou define padrão
    data_inicio = request.args.get('data_inicio') 
    data_fim = request.args.get('data_fim') 
    categoria = request.args.get('categoria') or 'Todas'
    usuario =request.args.get('usuario') or None
    isCasal = request.args.get('isCasal') or 'N'


    # Busca os gastos ordenados do mais recente para o mais antigo
    gastos = gasto_bp.gasto_service.extrato_gastos(usuario,data_inicio,data_fim,categoria,isCasal)  

    soma_gastos = 0

    soma_gastos = sum(gasto[2] for gasto in gastos)

    html = render_template("extrato_pdf.html", dados=gastos,soma_gastos=soma_gastos)
    output = BytesIO()
    pisa.CreatePDF(html, dest=output)
    output.seek(0)

    # response = Response(output.getvalue(), mimetype='application/pdf')
    # response.headers['Content-Disposition'] = 'inline; filename=extrato.pdf'
    # return response

    # return redirect(f"https://docs.google.com/viewer?embedded=true&url={url_for('gasto.exportar_pdf', _external=True)}")

    # return send_file(output, download_name='extrato.pdf', as_attachment=True)
    return send_file(output, mimetype='application/pdf', download_name='extrato.pdf')

@gasto_bp.route('/valida_mensalista', methods=['GET'], strict_slashes=False)
def valida_mensalista():
    # if valida_mensalista():
    usuario = session['usuario']
    
        # Pega a data atual
    data_atual = datetime.now()

    # Formata como "MM/YYYY"
    mes_ano = data_atual.strftime("%m/%Y")

    status_usuario = admin_bp.admin_service.valida_mensalista(usuario,mes_ano);

    if status_usuario:
        if status_usuario[0][0] == 'pago':
            return jsonify(status='ok')
        else:
            return jsonify(status='mensalista')
    else:
        return jsonify(status='mensalista')

@gasto_bp.route('/configuracoes')
def configuracoes():
    
    if 'usuario' not in session:
        
        return redirect(url_for('gasto.login')) 

    usuario = session['usuario']  # Só acessa se já tiver passado pela verificação

    #dados = gasto_bp.gasto_service.busca_config(usuario) #verifica_dados_bd(usuario)

    tem_conjuge = gasto_bp.gasto_service.tem_conjuge(usuario)
    telefone_whatsapp = whatsapp_bp.whatsapp_service.get_telefone_vinculado(usuario)

    # número do bot pra abrir a conversa direto (wa.me) — hoje é o número
    # de teste da Meta; troque a env var no Render quando migrar pro
    # número definitivo, sem precisar mexer no código
    numero_whatsapp_bot = os.environ.get('WHATSAPP_BOT_NUMERO', '15551493833')

    # bot do WhatsApp é benefício de plano pago — mesmo quem ainda está
    # dentro dos 7 dias de teste grátis (não bloqueado pra cadastro) não
    # tem acesso, só quem já assinou de verdade
    tem_plano_ativo = gasto_bp.gasto_service.tem_assinatura_ativa(usuario)

    return render_template(
        'configuracoes.html',
        usuario=usuario,
        temConjuge=tem_conjuge,
        telefoneWhatsapp=telefone_whatsapp,
        numeroWhatsappBot=numero_whatsapp_bot,
        temPlanoAtivo=tem_plano_ativo,
    )


@gasto_bp.route('/configuracoes/whatsapp', methods=['POST'])
def salvar_telefone_whatsapp():
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    usuario = session['usuario']

    # bot do WhatsApp é benefício de plano pago — bloqueia aqui também
    # (não só escondendo o formulário na tela) pra ninguém vincular
    # número direto pela rota sem ter assinatura
    if not gasto_bp.gasto_service.tem_assinatura_ativa(usuario):
        return jsonify({'erro': 'Assine um plano pago para vincular seu WhatsApp.'}), 403

    telefone = request.form.get('telefone', '').strip()

    if telefone:
        whatsapp_bp.whatsapp_service.vincular_telefone(telefone, usuario)
        return jsonify({'mensagem': 'WhatsApp vinculado com sucesso!'})
    else:
        whatsapp_bp.whatsapp_service.desvincular_telefone(usuario)
        return jsonify({'mensagem': 'WhatsApp desvinculado.'})


# ============================================================
# Bot do WhatsApp: webhook do Meta Cloud API. GET é a verificação que a
# Meta faz uma vez ao salvar a URL do webhook; POST é toda mensagem que
# chega. Ver WHATSAPP_SETUP.md pra config completa (variáveis de
# ambiente, passo a passo no Meta, etc).
# ============================================================
@whatsapp_bp.route('/webhook/whatsapp', methods=['GET'])
def whatsapp_verificar():
    modo = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    desafio = request.args.get('hub.challenge')

    if modo == 'subscribe' and token and token == os.environ.get('WHATSAPP_VERIFY_TOKEN'):
        return desafio, 200

    return 'Token de verificação inválido', 403


@whatsapp_bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_receber():
    # confirma que a requisição realmente veio da Meta (assinada com o
    # App Secret) antes de processar qualquer coisa
    segredo = os.environ.get('WHATSAPP_APP_SECRET', '')
    if segredo:
        assinatura = request.headers.get('X-Hub-Signature-256', '')
        esperado = 'sha256=' + hmac.new(segredo.encode(), request.data, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(esperado, assinatura):
            return '', 403

    dados = request.get_json(silent=True) or {}

    try:
        entrada = dados['entry'][0]['changes'][0]['value']
        mensagens = entrada.get('messages')

        # atualizações de status (enviado/entregue/lido/falhou) de mensagens
        # que ESTE app mandou — loga pra dar pra ver no log do Render
        # enquanto se investiga um problema de entrega
        status_atualizacoes = entrada.get('statuses')
        if status_atualizacoes:
            for s in status_atualizacoes:
                print(
                    "STATUS WHATSAPP:", s.get('status'),
                    "| destinatario:", s.get('recipient_id'),
                    "| erro:", s.get('errors')
                )

        if not mensagens:
            # não é uma mensagem nova (ex: confirmação de entrega/leitura) — ignora
            return jsonify(status='ignorado'), 200

        mensagem = mensagens[0]
        telefone_remetente = mensagem['from']  # ex: '5551995035983'
        texto = (mensagem.get('text') or {}).get('body', '').strip()

        if not texto:
            return jsonify(status='ignorado'), 200

        usuario_nome = whatsapp_bp.whatsapp_service.get_usuario_por_telefone(telefone_remetente)

        if not usuario_nome:
            enviar_mensagem_whatsapp(
                telefone_remetente,
                "Esse número ainda não está vinculado a nenhuma conta do Dois no Azul. "
                "Entra no app, vai em Configurações e cadastra seu WhatsApp por lá."
            )
            return jsonify(status='numero_nao_vinculado'), 200

        resposta_texto = responder_mensagem(texto, usuario_nome)
        enviar_mensagem_whatsapp(telefone_remetente, resposta_texto)

    except Exception as e:
        print("Erro processando webhook WhatsApp:", e)

    # sempre responde 200 pro Meta não ficar reenviando o mesmo evento
    return jsonify(status='ok'), 200


# ============================================================
# Bot "à parte" via WAHA — mesmo bot/Claude/banco de cima, só que
# recebendo mensagens de uma instância WAHA (WhatsApp pessoal, sem
# precisar de verificação de empresa da Meta) em vez do Cloud API
# oficial. Não mexe em nada do bloco acima (rotas /webhook/whatsapp
# oficiais continuam do jeito que estavam). Ver WAHA_SETUP.md.
# ============================================================
@whatsapp_bp.route('/webhook/whatsapp-waha', methods=['POST'])
def whatsapp_waha_receber():
    dados = request.get_json(silent=True) or {}

    try:
        if dados.get('event') != 'message':
            return jsonify(status='ignorado'), 200

        payload = dados.get('payload') or {}

        # ignora mensagens que o PRÓPRIO bot mandou (senão ele responde
        # a si mesmo em loop)
        if payload.get('fromMe'):
            return jsonify(status='ignorado'), 200

        chat_id_resposta = payload.get('from', '')  # pra onde responder — mantém o formato original (pode ser '@lid')

        # Status/Stories de contatos (e broadcast lists em geral) chegam
        # como "message" também, com from = "status@broadcast" (ou
        # "...@broadcast") — não são conversa nenhuma. BUG REAL já
        # confirmado: sem esse filtro, o bot tratava isso como "número
        # desconhecido" e respondia... pro próprio endereço de Status,
        # postando a resposta como Status visível pra todos os contatos
        # (aconteceu logo após reconectar o celular, que resincroniza
        # Status recentes).
        if chat_id_resposta.endswith('@broadcast'):
            print("WEBHOOK WAHA: ignorado evento de broadcast/status, from =", chat_id_resposta)
            return jsonify(status='ignorado'), 200

        texto = (payload.get('body') or '').strip()

        # com "Addressing Mode" LID (engine GOWS), o "from" vem como um
        # ID opaco tipo '211961635729457@lid' em vez do número — pra achar
        # o usuário no banco (que guarda número de telefone, não LID),
        # usa o número de verdade que fica em _data.Info.SenderAlt
        # ('555182111050:3@s.whatsapp.net'), descartando o sufixo ':N' de
        # dispositivo antes do '@'. A resposta continua indo pro chat_id
        # original (LID), que é o que o WAHA precisa pra entregar certo.
        telefone_remetente = chat_id_resposta
        if telefone_remetente.endswith('@lid'):
            sender_alt = (
                payload.get('_data', {})
                .get('Info', {})
                .get('SenderAlt', '')
            )
            if sender_alt:
                telefone_remetente = sender_alt.split(':')[0]

        if not chat_id_resposta or not texto:
            return jsonify(status='ignorado'), 200

        usuario_nome = whatsapp_bp.whatsapp_service.get_usuario_por_telefone(telefone_remetente)

        if not usuario_nome:
            enviar_mensagem_whatsapp_waha(
                chat_id_resposta,
                "Esse número ainda não está vinculado a nenhuma conta do Dois no Azul. "
                "Entra no app, vai em Configurações e cadastra seu WhatsApp por lá."
            )
            return jsonify(status='numero_nao_vinculado'), 200

        resposta_texto = responder_mensagem(texto, usuario_nome)
        enviar_mensagem_whatsapp_waha(chat_id_resposta, resposta_texto)

    except Exception as e:
        print("Erro processando webhook WAHA:", e)

    return jsonify(status='ok'), 200


@admin_bp.route('/deletar_usuario', methods=['GET','POST'], strict_slashes=False)
def deletar_usuario():

    # if valida_mensalista():
    usuario = session['usuario']
    
    admin_bp.admin_service.deletar_usuario(usuario)

    return render_template('configuracoes_exclusao.html')  

@despesa_bp.route('/metas')
def metas():
    if 'usuario' not in session:
        return redirect(url_for('gasto.login'))

    usuario = session['usuario']
    isCasal = request.args.get('isCasal') or 'N'

    tem_conjuge = despesa_bp.despesa_service.tem_conjuge(usuario)
    if isCasal == 'S' and not tem_conjuge:
        isCasal = 'N'

    cards = metas_service.listar_metas(usuario, isCasal)
    for card in cards:
        card['icone'] = icone_categoria(card['categoria'])

    categorias_completas = despesa_bp.despesa_service.get_categorias_completas(usuario, isCasal)
    # só oferece pra criar meta em categorias que ainda não têm uma
    categorias_ja_com_meta = {c['categoria'] for c in cards}
    categorias_disponiveis = [c for c in categorias_completas if c not in categorias_ja_com_meta]

    return render_template(
        "metas.html",
        cards=cards,
        usuario=usuario,
        isCasal=isCasal,
        temConjuge=tem_conjuge,
        categoriasDisponiveis=categorias_disponiveis,
        bloqueadoParaCadastro=bloqueado_para_cadastro(usuario),
    )


@despesa_bp.route('/metas/criar', methods=['POST'])
def criar_meta():
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    usuario = session['usuario']

    if bloqueado_para_cadastro(usuario):
        return jsonify({'erro': MENSAGEM_BLOQUEIO_PLANO}), 403

    data = request.get_json(silent=True) or {}
    categoria = (data.get('categoria') or '').strip()
    limite = data.get('limite')

    if not categoria or not limite:
        return jsonify({'erro': 'Dados incompletos'}), 400

    try:
        limite = float(limite)
        if limite <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'erro': 'Informe um limite válido'}), 400

    resultado = metas_service.criar_meta(usuario, categoria, limite)

    if resultado['sucesso']:
        return jsonify({'mensagem': 'Meta criada com sucesso!'})
    return jsonify({'erro': resultado['erro']}), 400


@despesa_bp.route('/metas/<int:id_meta>/editar', methods=['POST'])
def editar_meta(id_meta):
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    usuario = session['usuario']

    if bloqueado_para_cadastro(usuario):
        return jsonify({'erro': MENSAGEM_BLOQUEIO_PLANO}), 403

    data = request.get_json(silent=True) or {}
    limite = data.get('limite')

    try:
        limite = float(limite)
        if limite <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'erro': 'Informe um limite válido'}), 400

    sucesso = metas_service.editar_meta(usuario, id_meta, limite)

    if sucesso:
        return jsonify({'mensagem': 'Meta atualizada!'})
    return jsonify({'erro': 'Não foi possível atualizar essa meta.'}), 400


@despesa_bp.route('/metas/<int:id_meta>/excluir', methods=['POST'])
def excluir_meta(id_meta):
    # exclusão fica livre em qualquer plano, mesma regra de despesas/gastos/receitas
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    sucesso = metas_service.excluir_meta(session['usuario'], id_meta)

    if sucesso:
        return jsonify({'mensagem': 'Meta excluída.'})
    return jsonify({'erro': 'Não foi possível excluir essa meta.'}), 400


@gasto_bp.route('/insights_mes/<isCasal>')
def insights_mes(isCasal):
    if 'usuario' not in session:
        return jsonify({'erro': 'Você precisa estar logado.'}), 401

    usuario = session['usuario']

    resumo = despesa_bp.despesa_service.resumo_mes_atual(usuario, isCasal)
    pendencias_anteriores = despesa_bp.despesa_service.tem_pendencias_mes_anterior(usuario, isCasal)
    metas = metas_service.listar_metas(usuario, isCasal)
    atual = gasto_bp.gasto_service.filtrarGastos('mesatual', usuario, isCasal) or []
    anterior = gasto_bp.gasto_service.filtrarGastos('mesanterior', usuario, isCasal) or []

    insight = insights_service.calcular_insight(resumo, pendencias_anteriores, metas, atual, anterior)
    pendentes = despesa_bp.despesa_service.despesas_pendentes_mes_atual(usuario, isCasal)

    return jsonify({'despesas': resumo, 'pendentes': pendentes, 'insight': insight})


@gasto_bp.route('/receitas', methods=['GET', 'POST'], strict_slashes=False)
def receitas():

    # mês no formato YYYY-MM (mesmo padrão do filtro de despesas) — vem do
    # seletor de mês/ano do front (criarSeletorDeMes, em comum.js), que
    # substitui o antigo <select> nativo por mês (que além de feio também
    # não deixava escolher o ANO, então trocar de ano não era possível).
    mes = request.args.get('mes') or datetime.now().strftime('%Y-%m')
    usuario = session['usuario']

    isCasal = request.args.get('isCasal') or request.form.get('isCasal') or 'N'

    mes_formatado = f"{mes}-01"

    tem_conjuge = gasto_bp.gasto_service.tem_conjuge(usuario)

    receitas_lista = gasto_bp.gasto_service.listar_receitas(usuario, mes_formatado, isCasal)

    receitas_agrupadas = agrupar_receitas(receitas_lista)

    total_receitas = sum(r[2] for r in receitas_lista)

    return render_template('receitas.html',
                           usuario=usuario,
                           temConjuge=tem_conjuge,
                           isCasal=isCasal,
                           mes_atual=mes,
                           receitas_lista=receitas_lista,
                           total_receitas=total_receitas,
                           receitas_agrupadas=receitas_agrupadas,
                           bloqueadoParaCadastro=bloqueado_para_cadastro(usuario),
                           tutorialVisto=tutorial_service.tutorial_visto(usuario, 'receitas')
                           )

@gasto_bp.route('/salvar_receita', methods=['POST'], strict_slashes=False)
def salvar_receita():

    usuario = session['usuario']

    if bloqueado_para_cadastro(usuario):
        return jsonify({'erro': MENSAGEM_BLOQUEIO_PLANO}), 403

    data = request.get_json()

    origem = data.get("receita")
    valor = data.get("valor")

     #receitas-refactor
    #mes = data.get("mes").lower()  # converte para minúsculo

    data_receita = data.get("data")  # yyyy-mm-dd

    meses_portugues = {
        "janeiro": "01",
        "fevereiro": "02",
        "março": "03",
        "abril": "04",
        "maio": "05",
        "junho": "06",
        "julho": "07",
        "agosto": "08",
        "setembro": "09",
        "outubro": "10",
        "novembro": "11",
        "dezembro": "12"
    }

    # numero_mes = meses_portugues.get(mes)
    # if not numero_mes:
    #     return jsonify({"error": "Mês inválido"}), 400

    #receitas-refactor
    #mes_formatado = f"{numero_mes}-2026"

    try:
        sucesso = gasto_bp.gasto_service.salvar_receita(usuario, data_receita, origem, valor)
        return jsonify({"success": True}) if sucesso else jsonify({"alert": False})
    except Exception as e:
        return str(e), 500                           


@gasto_bp.route('/dados_receitas', methods=['GET'], strict_slashes=False)
def dados_receitas():
    usuario = session['usuario']

    mes = request.args.get("mes")

    meses_portugues = {
        "janeiro": "01",
        "fevereiro": "02",
        "março": "03",
        "abril": "04",
        "maio": "05",
        "junho": "06",
        "julho": "07",
        "agosto": "08",
        "setembro": "09",
        "outubro": "10",
        "novembro": "11",
        "dezembro": "12"
    }

    numero_mes = meses_portugues.get(mes)
    if not numero_mes:
        return jsonify({"error": "Mês inválido"}), 400

    mes_formatado = f"{numero_mes}-2025"
     
    receitas = gasto_bp.gasto_service.get_receitas_mes(usuario,mes_formatado,'Todas')

    dados = {}
    for r in receitas:
        dados[r[0]] = dados.get(r[0], 0) + r[1]

    return jsonify({
        "labels": list(dados.keys()),
        "values": list(dados.values())
    })

@gasto_bp.route('/deletar_receita', methods=['POST'], strict_slashes=False)
def deletar_receita():
    usuario = session['usuario']
    data = request.get_json()

    id_receita = data.get('id')

    if not id_receita:
        return jsonify({"error": "ID não informado"}), 400

    try:
        sucesso = gasto_bp.gasto_service.deletar_receita(usuario, id_receita)

        if sucesso:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Não foi possível deletar"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@gasto_bp.route('/editar_receita', methods=['POST'], strict_slashes=False)
def editar_receita():
    usuario = session['usuario']

    if bloqueado_para_cadastro(usuario):
        return jsonify({'erro': MENSAGEM_BLOQUEIO_PLANO}), 403

    data = request.get_json()

    id_receita = data.get("id")
    origem = data.get("receita")
    valor = data.get("valor")
    #receitas-refactor
    #mes = data.get("mes").lower()

    data_receita = data.get("data")

    meses_portugues = {
        "janeiro": "01",
        "fevereiro": "02",
        "março": "03",
        "abril": "04",
        "maio": "05",
        "junho": "06",
        "julho": "07",
        "agosto": "08",
        "setembro": "09",
        "outubro": "10",
        "novembro": "11",
        "dezembro": "12"
    }

    #numero_mes = meses_portugues.get(mes)
    # if not numero_mes:
    #     return jsonify({"error": "Mês inválido"}), 400

    #mes_formatado = f"{numero_mes}-2026"

    try:
        sucesso = gasto_bp.gasto_service.editar_receita(
            usuario, id_receita, origem, valor, data_receita
        )

        if sucesso:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Falha ao editar"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500        


@gasto_bp.route('/total_saldo_mes')
def total_receitas_mes():
    usuario = session['usuario']

    periodo = request.args.get('periodo', 'mesatual')
    isCasal = request.args.get('isCasal', 'N')

    total_receitas = gasto_bp.gasto_service.get_total_receitas_mes(usuario,periodo,isCasal)
    total_gastos = gasto_bp.gasto_service.get_total_gastos_mes(usuario,periodo,isCasal)

    # quanto ainda falta pagar de despesas do mês (só faz sentido pro mês
    # ATUAL — "vai faltar ou sobrar dinheiro" é uma pergunta sobre o
    # futuro, não sobre um mês anterior já fechado)
    valor_pendente = 0
    if periodo == 'mesatual':
        resumo_despesas = despesa_bp.despesa_service.resumo_mes_atual(usuario, isCasal)
        valor_pendente = resumo_despesas.get('valor_pendente', 0)

    return jsonify({
        "total_receitas": total_receitas or 0,
        "total_gastos": total_gastos or 0,
        "valor_pendente": valor_pendente,
    })


def agrupar_receitas(receitas):
    agrupado = defaultdict(list)

    for r in receitas:
        # r[1] = descrição
        descricao = r[1]

        # 🔥 pega primeira palavra
        chave = descricao.split(" ")[0]

        agrupado[chave].append(r)

    return dict(agrupado)    
