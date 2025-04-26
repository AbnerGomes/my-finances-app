from flask import Blueprint, render_template, session, redirect, url_for, request, flash,jsonify, send_file, request
from service.gasto_service import GastoService
from io import BytesIO
import pandas as pd
from xhtml2pdf import pisa
import random
from datetime import datetime
from datetime import date
from collections import defaultdict
import calendar

from service.despesa_service import DespesaService

gasto_bp = Blueprint('gasto', __name__)
despesa_bp = Blueprint('despesa', __name__)


mensagens_erro = [
    "Senha ou usuario errado 🖕🏼 ",
    "Verifique suas credenciais ⚠️",
    "Seu usuario pode estar inativo 😕",
    "Cara, olha o que tu ta digitando 🤦🏽‍♂️",
    "Acesso negado! você é gay 🏳️‍🌈",
    "Tu é burro(a) ou tu é burro(a)? 🤦🏽‍♂️",
    "Vai bloquear teu usuario 😅",
    "Mds, quem sabe clica em redefinir senha 🤦🏽‍♂️",
]

#####ROTAS#####

def init_routes(app, gasto_service,despesa_service):
    print(app.url_map)
    app.register_blueprint(gasto_bp)
    app.register_blueprint(despesa_bp)

    # Armazena a instância do service dentro do blueprint
    gasto_bp.gasto_service = gasto_service
    despesa_bp.despesa_service = despesa_service

#def configure_routes(app, gasto_service):
@gasto_bp.route('/')
def login():
    return render_template('login.html')

@gasto_bp.route('/voltar_ao_login', methods=['GET','POST'])
def voltar_ao_login():
    return render_template('voltar_ao_login.html')

@gasto_bp.route('/login', methods=['POST'])
def login_post():
    print('abner')
    if request.method == 'POST':
        usuario = request.form['email']
        print(usuario)
        senha = request.form['senha']
        print(senha)
        if gasto_bp.gasto_service.validar_login(usuario, senha):
            session['usuario'] = usuario
            
            dados = gasto_bp.gasto_service.filtrarGastos('mesatual',usuario)

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

    dados = gasto_bp.gasto_service.filtrarGastos('mesatual',usuario) #verifica_dados_bd(usuario)

    if not dados:
        dados = [('Alimentação', 0), ('Saúde', 0), ('Mobilidade', 0), ('Entretenimento', 0), ('Moradia', 0), ('Outros', 0), ('Dívidas', 0), ('Educação', 0)]

    total_gasto = sum([
    float(item['valor']) if isinstance(item, dict) and 'valor' in item else float(item[0])
    for item in dados
    if (
        (isinstance(item, dict) and isinstance(item.get('valor', 0), (int, float))) or 
        (isinstance(item, tuple) and len(item) > 0 and str(item[0]).replace('.', '', 1).isdigit())
    )
    ])

    return render_template('index.html')

@gasto_bp.route('/cadastrar_gasto', methods=['GET', 'POST'])
def cadastrar_gasto():
    if request.method == 'POST':
        print('cad entrou')
        if 'usuario' not in session:
            flash('Você precisa estar logado para adicionar um gasto.')
            return redirect(url_for('gasto.login')) 

        gasto = request.form['gasto']
        valor = request.form['valor']
        data = request.form['data']
        categoria = request.form['categoria']
        
        usuario = session['usuario']
        
        # Salvar o gasto no banco
        sucesso = gasto_bp.gasto_service.salvar_gasto(gasto, valor, data, categoria,usuario)
        #flash('Gasto cadastrado com sucesso!', 'success')  

        return """<script>                    
                    window.location.href = '/extrato';
                </script>"""

    # return render_template('cadastrar_gasto.html')
    return extrato()  

@gasto_bp.route('/extrato', methods=['GET', 'POST'])
def extrato():
    usuario = session['usuario']

    page = request.args.get('page', 1, type=int)  # Obtém o número da página (padrão é 1)
    per_page = 12  # Número de gastos por página
    
     # pega data atual
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)

    # Pega filtros da URL ou define padrão
    data_inicio = request.args.get('data_inicio') or primeiro_dia.strftime('%Y-%m-%d')
    data_fim = request.args.get('data_fim') or hoje.strftime('%Y-%m-%d')
    categoria = request.args.get('categoria') or 'Todas'

    # Busca os gastos ordenados do mais recente para o mais antigo
    gastos = gasto_bp.gasto_service.extrato_gastos(usuario,data_inicio,data_fim,categoria)  

    total_gastos = len(gastos)

    start = (page - 1) * per_page
    end = start + per_page

    gastos_pagina = gastos[start:end]

    # Agrupar os gastos por data
    gastos_agrupados = defaultdict(list)
    for gasto in gastos_pagina:
        data = gasto[3]  # Supondo que o 4º item (índice 3) seja a data
        gastos_agrupados[data].append(gasto)


    # lista de categorias
    categorias = gasto_bp.gasto_service.get_categorias_disponiveis(usuario)

    gastos_pagina = gastos[start:end]

    soma_gastos = 0

    #se for geral do filtro selecionado
    soma_gastos = sum(gasto[2] for gasto in gastos)

    return render_template(
        'extrato.html',
        gastos_agrupados=gastos_agrupados,
        page=page,
        total=total_gastos,
        per_page=per_page,
        now=datetime.now(),
        data_inicio=data_inicio,
        data_fim=data_fim,
        categoria=categoria,
        soma_gastos=soma_gastos
    )


@gasto_bp.route('/filtrarGastos/<periodo>')
def filtrar(periodo):
    usuario = session['usuario']

    dados = gasto_bp.gasto_service.filtrarGastos(periodo,usuario)
    return jsonify(dados)


@gasto_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        usuario = request.form["email"]
        senha = request.form["senha"]

        dados = gasto_bp.gasto_service.valida_usuario_existente(usuario,senha)   
        
        if dados:
            flash("Usuário já existe! 🤦🏽‍♂️")
            return redirect(url_for('gasto.cadastro')) 

        flash("Usuário cadastrado com sucesso! 😄", "success")

        return render_template("cadastro.html")
    
    return render_template("cadastro.html")


@gasto_bp.route('/esqueci', methods=['GET', 'POST'])
def esqueci():
    return render_template("esqueci.html")    

@gasto_bp.route('/editar_gasto', methods=[ 'POST'])
def editar_gasto():

    if 'usuario' not in session:
        flash('Você precisa estar logado para adicionar um gasto.')
        return redirect(url_for('gasto.login')) 

    gasto = request.form['gasto']
    valor = request.form['valor']
    data = request.form['data']
    categoria = request.form['categoria']
    
    id = request.form['id']

    # usuario = session['usuario']
    
    gasto_bp.gasto_service.editar_gasto(gasto,categoria,valor,data,id)

    return extrato() 

@gasto_bp.route('/deletar_gasto', methods=['POST'])
def deletar_gasto():
    print('foi')
    if 'usuario' not in session:
        flash('Você precisa estar logado para deletar um gasto.')
        return redirect(url_for('gasto.login')) 

    id_gasto = request.form.get('id')

    print('gasto' + id_gasto)

    if not id_gasto:
        # flash('ID do gasto não fornecido!', 'danger')
        return redirect(url_for('gasto.extrato')) 

    try:
        gasto_bp.gasto_service.deletar_gasto(id_gasto)
        # flash('Gasto deletado com sucesso!', 'success')
    except Exception as e:
        print("Erro ao deletar gasto:", e)
        flash('Erro ao tentar deletar o gasto. 😓', 'danger')

    return extrato() 

@despesa_bp.route('/despesas', methods=['GET'])
def despesas(): 
    usuario = session['usuario']
    
    # pega data atual
    hoje = date.today()
    primeiro_mes = hoje.replace(day=1)

    # Pega o filtro vindo da URL ou usa o primeiro dia do mês atual
    mes_ano_str = request.args.get('mes_ano') or primeiro_mes.strftime('%Y-%m')
    print(mes_ano_str)

    # Busca os gastos ordenados do mais recente para o mais antigo
    despesas = despesa_bp.despesa_service.busca_despesas(usuario,mes_ano_str,'Todas')  

    return render_template(
        'despesas.html',
        despesas=despesas,
        mes_ano=mes_ano_str[:7]  # yyyy-mm para o input month
    )

@despesa_bp.route('/despesas', methods=['POST'])
def atualizar_status():
    data = request.get_json()
    id_despesa = data.get('id_despesa')
    novo_status = data.get('novo_status')

    if not id_despesa or not novo_status:
        return jsonify({'erro': 'Dados incompletos'}), 400

    # Chama método da camada service para atualizar no banco
    sucesso = despesa_bp.despesa_service.atualizar_status(id_despesa, novo_status)

    if sucesso:
        return jsonify({'mensagem': 'Status atualizado com sucesso'})
    else:
        return jsonify({'erro': 'Falha ao atualizar'}), 500



@despesa_bp.route('/cadastrar_despesa', methods=['GET', 'POST'])
def cadastrar_despesa():
    print('foi')
    if request.method == 'POST':
        if 'usuario' not in session:
            flash('Você precisa estar logado para adicionar um gasto.')
            return redirect(url_for('gasto.login')) 

        despesa = request.form['despesa']
        valor = request.form['valor']

        data = request.form['mes_ano']
        print(data)

        
        categoria = request.form['categoria']
        
        usuario = session['usuario']
        
        # Salvar o gasto no banco
        despesa_bp.despesa_service.salvar_despesa(despesa, valor, data, categoria,usuario)
        flash('Despesa cadastrada com sucesso!', 'success')  

        return """<script>                    
                    window.location.href = '/cadastrar_despesa';
                </script>"""

    return render_template('cadastrar_despesa.html')  


@despesa_bp.route('/editar_despesa', methods=[ 'POST'])
def editar_despesa():

    if 'usuario' not in session:
        flash('Você precisa estar logado para editar uma despesa.')
        return redirect(url_for('gasto.login')) 

    despesa = request.form['despesa']
    valor = request.form['valor']
    categoria = request.form['categoria']
    id = request.form['id']
    
    # usuario = session['usuario']
    
    despesa_bp.despesa_service.editar_despesa(despesa,categoria,valor,id)

    return despesas() 

@despesa_bp.route('/deletar_despesa', methods=['POST'])
def deletar_despesa():
    print('foi')
    if 'usuario' not in session:
        flash('Você precisa estar logado para deletar uma despesa.')
        return redirect(url_for('gasto.login')) 

    id_despesa = request.form.get('id')

    if not id_despesa:
        flash('ID do despesa não fornecido!', 'danger')
        return redirect(url_for('gasto.extrato')) 

    try:
        despesa_bp.despesa_service.deletar_despesa(id_despesa)
        flash('Despesa deletada com sucesso!', 'success')
    except Exception as e:
        print("Erro ao deletar despesa:", e)
        flash('Erro ao tentar deletar o despesa. 😓', 'danger')

    return despesas() 

#exportação
@gasto_bp.route('/exportar/excel')
def exportar_excel():
    usuario = session['usuario']

     # pega data atual
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)

    # Pega filtros da URL ou define padrão
    data_inicio = request.args.get('data_inicio') or primeiro_dia.strftime('%Y-%m-%d')
    data_fim = request.args.get('data_fim') or hoje.strftime('%Y-%m-%d')
    categoria = request.args.get('categoria') or 'Todas'

    # Busca os gastos ordenados do mais recente para o mais antigo
    gastos = gasto_bp.gasto_service.extrato_gastos(usuario,data_inicio,data_fim,categoria)  

    colunas = [ 'categoria', 'gasto' ,'valor','data','id']  # ajuste conforme sua estrutura real
    df = pd.DataFrame(gastos,columns=colunas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Extrato')

    output.seek(0)
    return send_file(output, download_name='extrato.xlsx', as_attachment=True)


@gasto_bp.route('/exportar/pdf')
def exportar_pdf():
    usuario = session['usuario']

     # pega data atual
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)

    # Pega filtros da URL ou define padrão
    data_inicio = request.args.get('data_inicio') or primeiro_dia.strftime('%Y-%m-%d')
    data_fim = request.args.get('data_fim') or hoje.strftime('%Y-%m-%d')
    categoria = request.args.get('categoria') or 'Todas'

    # Busca os gastos ordenados do mais recente para o mais antigo
    gastos = gasto_bp.gasto_service.extrato_gastos(usuario,data_inicio,data_fim,categoria)  

    soma_gastos = 0

    soma_gastos = sum(gasto[2] for gasto in gastos)

    html = render_template("extrato_pdf.html", dados=gastos,soma_gastos=soma_gastos)
    output = BytesIO()
    pisa.CreatePDF(html, dest=output)
    output.seek(0)

    return send_file(output, download_name='extrato.pdf', as_attachment=True)


@gasto_bp.route('/verificar_mensalista')
def verificar_mensalista():
    # if valida_mensalista():
    usuario = session['usuario']
    if usuario == 'abner@gmail.com':
        return jsonify(status='ok')
    else:
        return jsonify(status='mensalista')




@gasto_bp.route('/configuracoes')
def configuracoes():
    
    if 'usuario' not in session:
        
        return redirect(url_for('gasto.login')) 

    usuario = session['usuario']  # Só acessa se já tiver passado pela verificação

    #dados = gasto_bp.gasto_service.busca_config(usuario) #verifica_dados_bd(usuario)

    return render_template('configuracoes.html')    