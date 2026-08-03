import os
import json
from datetime import datetime

import mercadopago

from .db_service import get_connection

# Preços e nomes dos planos oferecidos em /planos (templates/planos.html).
# Mudar preço aqui não muda o que já foi vendido — só afeta novas compras.
PLANOS = {
    'mensal': {'titulo': 'Plano Mensal - Dois no Azul', 'valor': 9.90},
    'anual': {'titulo': 'Plano Anual - Dois no Azul', 'valor': 99.90},
}


def _sdk():
    return mercadopago.SDK(os.environ['MP_ACCESS_TOKEN'])


def criar_preferencia_pagamento(tipo_plano, usuario_email, base_url):
    """Cria uma "preferência" (sessão de checkout) no Mercado Pago e
    devolve o dict de resposta deles — o campo `init_point` é a URL da
    página de pagamento hospedada pelo Mercado Pago (Checkout Pro), pra
    onde o usuário deve ser redirecionado."""
    plano = PLANOS.get(tipo_plano)
    if not plano:
        return None

    if not os.environ.get('MP_ACCESS_TOKEN'):
        print('MP_ACCESS_TOKEN não configurado — ver WHATSAPP_SETUP.md/passo a passo de pagamento.')
        return None

    referencia = json.dumps({'usuario': usuario_email, 'plano': tipo_plano})

    preference_data = {
        'items': [{
            'title': plano['titulo'],
            'quantity': 1,
            'unit_price': plano['valor'],
            'currency_id': 'BRL',
        }],
        'payer': {'email': usuario_email},
        'back_urls': {
            'success': f'{base_url}/pagamento/retorno?status=sucesso',
            'failure': f'{base_url}/pagamento/retorno?status=falha',
            'pending': f'{base_url}/pagamento/retorno?status=pendente',
        },
        'auto_return': 'approved',
        'notification_url': f'{base_url}/webhook/mercadopago',
        'external_reference': referencia,
        'statement_descriptor': 'DOISNOAZUL',
    }

    resultado = _sdk().preference().create(preference_data)

    if resultado.get('status') not in (200, 201):
        print('Erro ao criar preferência Mercado Pago:', resultado)
        return None

    return resultado['response']


def buscar_pagamento(payment_id):
    """Consulta o status REAL de um pagamento direto na API do Mercado
    Pago (nunca confia só no que o webhook manda no corpo da requisição
    — esse é só um aviso "olha, algo mudou", quem confirma é essa consulta)."""
    resultado = _sdk().payment().get(payment_id)

    if resultado.get('status') != 200:
        print('Erro ao consultar pagamento Mercado Pago:', resultado)
        return None

    return resultado['response']


def ativar_assinatura(usuario_email, tipo_plano):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO mensalidade (usuario, mes_ano, status, ativo, tipo_plano)
           VALUES (%s, %s, 'pago', 'S', %s)""",
        (usuario_email, datetime.now().strftime('%Y-%m'), tipo_plano)
    )
    conn.commit()
    conn.close()
