from flask import Blueprint, render_template, session, redirect, url_for, request, flash,jsonify, send_file, request, Response
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

from service.admin_service import AdminService

import locale

gasto_bp = Blueprint('gasto', __name__)
despesa_bp = Blueprint('despesa', __name__)
admin_bp = Blueprint('admin', __name__)

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

def init_routes(app, gasto_service,despesa_service,admin_service):
    print(app.url_map)
    app.register_blueprint(gasto_bp)
    app.register_blueprint(despesa_bp)
    app.register_blueprint(admin_bp)

    # Armazena a instância do service dentro do blueprint
    gasto_bp.gasto_service = gasto_service
    despesa_bp.despesa_service = despesa_service
    admin_bp.admin_service = admin_service
    
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

        usuario_bd =  gasto_bp.gasto_service.validar_login(usuario, senha)

        if usuario_bd is not None:
            
            session['usuario'] = usuario_bd
            
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
        dados = [('Alimentação', 0), ('Saúde', 0), ('Mobilidade', 0), ('Entretenimento', 0), ('Moradia', 0), ('Outros', 0), ('Dívidas', 0), ('Educação', 0)]

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

    return render_template('index.html',usuario=usuario,temConjuge=tem_conjuge)

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

    #start = (page - 1) * per_page
    #end = start + per_page

    #gastos_pagina = gastos[start:end]

    # Agrupar os gastos por data
    gastos_agrupados = defaultdict(list)
    for gasto in gastos:
       data = gasto[3]  # Supondo que o 4º item (índice 3) seja a data
       gastos_agrupados[data].append(gasto)


    # lista de categorias
    categorias = gasto_bp.gasto_service.get_categorias_disponiveis(usuario)

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
        categoria=categoria,
        soma_gastos=soma_gastos
        ,usuario =usuario,
        isCasal=isCasal,
        temConjuge=tem_conjuge
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
        usuario = request.form["email"]
        senha = request.form["senha"]
        nome = request.form["nome"]
        telefone = request.form["telefone"]

        dados = gasto_bp.gasto_service.valida_usuario_existente(usuario,senha,nome,telefone)   
        
        if dados:
            flash("Usuário já existe! 🤦🏽‍♂️")
            return redirect(url_for('gasto.cadastro',usuario=usuario)) 

        flash("Usuário cadastrado com sucesso! 😄", "success")

        return render_template("cadastro.html",usuario=usuario)
    
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

    # Pega o filtro vindo da URL ou usa o primeiro dia do mês atual
    mes_ano_str = request.args.get('mes_ano') or primeiro_mes.strftime('%Y-%m')

    # Busca os gastos ordenados do mais recente para o mais antigo
    despesas = despesa_bp.despesa_service.busca_despesas(usuario,mes_ano_str[-7:],'Todas',isCasal)  

    tem_conjuge = despesa_bp.despesa_service.tem_conjuge(usuario)

    soma_despesas = 0

    soma_despesas = sum(despesa[2] for despesa in despesas)

    if isCasal is None:
        isCasal ='N'

    return render_template(
        'despesas.html',
        despesas=despesas,
        mes_ano=mes_ano_str[-7:]  # yyyy-mm para o input month
        ,usuario=usuario,
        isCasal=isCasal,
        temConjuge=tem_conjuge,
        somaDespesas=soma_despesas
    )

@despesa_bp.route('/atualizar_status', methods=['POST'])
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



@despesa_bp.route('/cadastrar_despesa', methods=['POST','GET'])
def cadastrar_despesa():
    print('foi')
    #if request.method == 'POST':
    if 'usuario' not in session:
        flash('Você precisa estar logado para adicionar um gasto.')
        return redirect(url_for('gasto.login')) 

    despesa = request.form['despesa']
    valor = request.form['valor']

    tipo_despesa = request.form['tipo_despesa']
    data = request.form['mes_ano']
    print(data)

    
    categoria = request.form['categoria']
    
    usuario = session['usuario']
    
    if tipo_despesa == 'Fixa':
        tipo_despesa = 'F'
    elif tipo_despesa == 'Variável':
        tipo_despesa = 'V'
    elif tipo_despesa == 'Exceção':
        tipo_despesa = 'E' 

    # Salvar o gasto no banco
    despesa_bp.despesa_service.salvar_despesa(despesa, valor, data, categoria,usuario,tipo_despesa)
    #flash('Despesa cadastrada com sucesso!', 'success')  

    return despesas()

    #return render_template('despesas.html',usuario=usuario)  


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
    usuario = session['usuario']

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

    print(mes_ano)
    print(usuario)

    status_usuario = admin_bp.admin_service.valida_mensalista(usuario,mes_ano);

    print(status_usuario)

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

    return render_template('configuracoes.html',usuario=usuario)    


@admin_bp.route('/deletar_usuario', methods=['GET','POST'], strict_slashes=False)
def deletar_usuario():
    print('dento')
    # if valida_mensalista():
    usuario = session['usuario']
    
    admin_bp.admin_service.deletar_usuario(usuario)
    print('oquei')
    return render_template('configuracoes_exclusao.html')  

@despesa_bp.route('/metas') 
def metas():
    # Exemplo real com gasto e cálculo do percentual
    cards = [
        {
            "id": 1,
            "nome": "Ifood",
            "limite": 300,
            "gasto": 135,
            "percentual": min(int((135 / 300) * 100), 100),
            "imagem_url": "/static/images/ifood.png"
        },
        {
            "id": 2,
            "nome": "Futebol",
            "limite": 100,
            "gasto": 85,
            "percentual": min(int((85 / 100) * 100), 100),
            "imagem_url": "/static/images/futebol.png",
        },
        {
            "id": 3,
            "nome": "Carro",
            "limite": 800,
            "gasto": 820,
            "percentual": min(int((820 / 800) * 100), 100),
            "imagem_url": "/static/images/carro.png"
        }
    ]
    return render_template("metas.html", cards=cards,usuario='Abner Gomes',isCasal='N')


@gasto_bp.route('/receitas',methods=['GET','POST'], strict_slashes=False)
def receitas():
    mes = request.args.get('mes', '05-2025')
    categorias = request.args.getlist('categorias') or 'Todas'

    categorias = categorias.format(','.join('?' * len(categorias)))

    usuario = session['usuario']

    resultados = gasto_bp.gasto_service.get_receitas_mes(usuario,mes,categorias)

    todas_categorias = sorted([row[0] for row in resultados])

    labels = [r[0].capitalize() for r in resultados]
    values = [float(r[1]) for r in resultados]

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        # fallback para padrão do sistema
        locale.setlocale(locale.LC_TIME, '')

    data = datetime.strptime(mes, '%m-%Y')

    mes_nome = data.strftime('%B')  # 'maio'

    meses = ['janeiro', 'fevereiro', 'marco', 'abril','maio']  # Adicione os demais

    #verifica se é conta casal e exibe dropdon
    tem_conjuge = gasto_bp.gasto_service.tem_conjuge(usuario)

    return render_template('receitas.html',
                           usuario=usuario,
                           temConjuge=tem_conjuge,
                           labels=labels,
                           values=values,
                           meses=meses,
                           mes_atual=mes_nome,
                           categorias=categorias,
                           todas_categorias=todas_categorias)

@gasto_bp.route('/salvar_receita', methods=['GET','POST'], strict_slashes=False)
def salvar_receita():

    usuario = session['usuario']

    data = request.get_json()
    origem = data.get("receita")
    valor = data.get("valor")
    mes = data.get("mes")

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        # fallback para padrão do sistema
        locale.setlocale(locale.LC_TIME, '')

    mes_referencia = datetime.strptime(mes, '%B') 

    # Formata para 'mm-yyyy'
    mes_formatado = str(mes_referencia.month) + '-2025'

    if len(mes_formatado) == 6:
        mes_formatado = '0' + mes_formatado

    # Salve no banco (exemplo com SQLAlchemy ou seu método atual)
    try:
        if gasto_bp.gasto_service.salvar_receita(usuario,mes_formatado,origem,valor) is True:
            return jsonify({"success": True})
        else:
            return jsonify({"alert": False})    
    except Exception as e:
        return str(e), 500                           


@gasto_bp.route('/dados_receitas', methods=['GET'], strict_slashes=False)
def dados_receitas():
    usuario = session['usuario']

    mes = request.args.get("mes")

    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except locale.Error:
        # fallback para padrão do sistema
        locale.setlocale(locale.LC_TIME, '')

    mes_referencia = datetime.strptime(mes, '%B') 

    # Formata para 'mm-yyyy'
    mes_formatado = str(mes_referencia.month) + '-2025'

    if len(mes_formatado) == 6:
        mes_formatado = '0' + mes_formatado

    receitas = gasto_bp.gasto_service.get_receitas_mes(usuario,mes_formatado,'Todas')

    dados = {}
    for r in receitas:
        dados[r[0]] = dados.get(r[0], 0) + r[1]

    return jsonify({
        "labels": list(dados.keys()),
        "values": list(dados.values())
    })
