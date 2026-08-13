import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def enviar_email(destinatario, assunto, corpo_texto, corpo_html=None):
    """Envia um e-mail via Gmail SMTP, usando uma "Senha de app" do Google
    (não a senha normal da conta — ver EMAIL_SETUP.md pra gerar uma).
    Devolve True/False; nunca levanta exceção pra quem chama, só loga o
    erro (uma falha aqui não pode derrubar o fluxo de recuperação de
    senha inteiro)."""
    usuario_gmail = os.environ.get('GMAIL_USER')
    senha_app = os.environ.get('GMAIL_APP_PASSWORD')

    if not usuario_gmail or not senha_app:
        print('GMAIL_USER/GMAIL_APP_PASSWORD não configurados — ver EMAIL_SETUP.md. E-mail não enviado.')
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = assunto
    msg['From'] = f'Dois no Azul <{usuario_gmail}>'
    msg['To'] = destinatario

    msg.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))
    if corpo_html:
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as servidor:
            servidor.starttls()
            servidor.login(usuario_gmail, senha_app)
            servidor.sendmail(usuario_gmail, destinatario, msg.as_string())
        return True
    except Exception as e:
        print('Erro ao enviar e-mail:', e)
        return False
