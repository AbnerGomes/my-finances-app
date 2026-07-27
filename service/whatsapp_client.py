import os
import requests

GRAPH_API_VERSION = "v22.0"


def enviar_mensagem_whatsapp(telefone_destino, texto):
    """Envia uma mensagem de texto via WhatsApp Cloud API (Meta).
    telefone_destino: só dígitos, com DDI (ex: 5551995035983)."""
    token = os.environ["WHATSAPP_TOKEN"]
    phone_number_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone_destino,
        "type": "text",
        "text": {"body": texto},
    }
    headers = {"Authorization": f"Bearer {token}"}

    resposta = requests.post(url, json=payload, headers=headers, timeout=15)
    if not resposta.ok:
        print("Erro ao enviar mensagem WhatsApp:", resposta.status_code, resposta.text)
    return resposta.ok
