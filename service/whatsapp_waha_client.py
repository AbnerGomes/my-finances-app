import os
import requests

# Bot "à parte" via WAHA (WhatsApp HTTP API), rodando com o número
# pessoal do usuário, sem precisar de verificação de empresa da Meta —
# só pra continuar testando enquanto o MEI/verificação da conta oficial
# não sai. Fica isolado do bot oficial (routes.py: whatsapp_verificar/
# whatsapp_receber, service/whatsapp_client.py) — nada ali foi tocado.


def enviar_mensagem_whatsapp_waha(telefone_destino, texto):
    """Envia uma mensagem de texto via WAHA.
    telefone_destino: só dígitos (com DDI), ex: 5551995035983 — o sufixo
    "@c.us" exigido pelo WAHA é adicionado aqui."""
    base_url = os.environ['WAHA_API_URL'].rstrip('/')
    api_key = os.environ.get('WAHA_API_KEY', '')
    session = os.environ.get('WAHA_SESSION', 'default')

    chat_id = telefone_destino if '@' in telefone_destino else f'{telefone_destino}@c.us'

    payload = {
        'chatId': chat_id,
        'text': texto,
        'session': session,
    }
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['X-Api-Key'] = api_key

    resposta = requests.post(f'{base_url}/api/sendText', json=payload, headers=headers, timeout=15)
    if not resposta.ok:
        print('Erro ao enviar mensagem WAHA:', resposta.status_code, resposta.text)
    return resposta.ok
