from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, request,session
import json
import sqlite3
import os
from datetime import datetime, timedelta
import random
import service
from service.gasto_service import GastoService
import os.path
from routes.routes import init_routes

from service.despesa_service import DespesaService
from service.admin_service import AdminService
from service.whatsapp_service import WhatsappService

app = Flask(__name__)

# Defina uma chave secreta
app.secret_key = 'gomes-abner-py-finn-flask-app-2025'

# Sessão "lembrada" por 30 dias (em vez do padrão do Flask, que expira
# quando o navegador/webview encerra) — combinado com session.permanent =
# True no login, evita ter que logar de novo toda vez que o app é
# reaberto.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Evita que o navegador sirva uma versão em cache de css/js depois de uma
# edição — sem isso, alterações em static/ podem não aparecer pro usuário
# até ele limpar o cache manualmente. Sobrescreve o `url_for` usado dentro
# dos templates (só nos templates — o resto do código Python continua
# usando o url_for normal do Flask), então nenhum template precisa mudar.
@app.context_processor
def cache_busted_url_for():
    def url_for_com_versao(endpoint, **values):
        if endpoint == 'static' and 'filename' in values:
            file_path = os.path.join(app.root_path, 'static', values['filename'])
            try:
                values['v'] = int(os.stat(file_path).st_mtime)
            except OSError:
                pass
        return url_for(endpoint, **values)
    return dict(url_for=url_for_com_versao)

# Inicializa o service
gasto_service = GastoService()
despesa_service = DespesaService()
admin_service = AdminService()
whatsapp_service = WhatsappService()
#create_db() # chamar antes do flask iniciar

# Configura rotas
#configure_routes(app, gasto_service)
init_routes(app, gasto_service,despesa_service,admin_service,whatsapp_service),#regitra com blueprint

if __name__ == '__main__':
    #create_db()  # Cria o banco e a tabela ao iniciar o app
    app.run(debug=True) # remover em producao gunicorn ira rodar no render
