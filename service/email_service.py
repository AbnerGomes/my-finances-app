import os

import requests

# API HTTPS (não SMTP) — Render bloqueia conexão SMTP de saída (porta
# 587/465) nas contas gratuitas, confirmado em produção com
# "[Errno 101] Network is unreachable" ao tentar Gmail SMTP direto. A
# API do Resend roda sobre HTTPS normal, então não tem esse problema.
RESEND_API_URL = 'https://api.resend.com/emails'


def enviar_email(destinatario, assunto, corpo_texto, corpo_html=None):
    """Envia um e-mail via API do Resend. Devolve True/False; nunca
    levanta exceção pra quem chama, só loga o erro (uma falha aqui não
    pode derrubar o fluxo de recuperação de senha inteiro)."""
    api_key = os.environ.get('RESEND_API_KEY')
    remetente = os.environ.get('RESEND_FROM', 'Dois no Azul <onboarding@resend.dev>')

    if not api_key:
        print('RESEND_API_KEY não configurado — ver EMAIL_SETUP.md. E-mail não enviado.')
        return False

    payload = {
        'from': remetente,
        'to': [destinatario],
        'subject': assunto,
        'text': corpo_texto,
    }
    if corpo_html:
        payload['html'] = corpo_html

    try:
        resposta = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=15,
        )
        if not resposta.ok:
            print('Erro ao enviar e-mail (Resend):', resposta.status_code, resposta.text)
            return False
        return True
    except Exception as e:
        print('Erro ao enviar e-mail (Resend):', e)
        return False
