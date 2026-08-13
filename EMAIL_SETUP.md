# Recuperação de senha por e-mail (Gmail SMTP)

A tela "Esqueci minha senha" manda um código de 6 dígitos por e-mail
(válido por 15 minutos) usando o seu próprio Gmail (`abwgomes@gmail.com`)
como remetente, via SMTP — não precisa de nenhuma biblioteca nova nem
conta em outro serviço.

## 1. Gerar uma "Senha de app" no Google

O Gmail **não aceita mais a senha normal da conta** pra login via SMTP
por outros programas — precisa de uma "Senha de app" (App Password),
específica pra isso.

1. Sua conta Google precisa ter a **verificação em duas etapas (2FA)
   ativada** — se ainda não tiver, ative primeiro em
   [myaccount.google.com/security](https://myaccount.google.com/security).
2. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   (ou: Conta Google → Segurança → Verificação em duas etapas → Senhas de app,
   lá embaixo da página).
3. Dê um nome pra identificar (ex: "Dois no Azul") e clique em **Criar**.
4. O Google mostra uma senha de 16 caracteres (tipo `abcd efgh ijkl mnop`) —
   **copia ela na hora**, só aparece uma vez. Pode remover os espaços ou
   deixar, tanto faz.

## 2. Configurar no Render

No painel do Render, no seu app principal → **Environment**, adiciona:

| Variável | Valor |
|---|---|
| `GMAIL_USER` | `abwgomes@gmail.com` (o e-mail que vai aparecer como remetente) |
| `GMAIL_APP_PASSWORD` | a senha de 16 caracteres gerada no passo 1 |

Salva e espera o redeploy automático (ou clica em "Manual Deploy").

Se quiser testar localmente também, adiciona as mesmas duas variáveis no
seu `.env`.

## 3. Testar

1. Na tela de login, clica em "Esqueci minha senha".
2. Digita um e-mail que já tem conta no app.
3. Deve chegar um e-mail com um código de 6 dígitos em alguns segundos
   (confere a caixa de spam também, principalmente nos primeiros testes).
4. Digita o código + a nova senha na tela seguinte.

Se **não** configurar essas variáveis, o app não trava — só não envia o
e-mail (fica logado no Render: `GMAIL_USER/GMAIL_APP_PASSWORD não
configurados`), então dá pra fazer o deploy da funcionalidade mesmo antes
de configurar isso, e ligar depois.

## Limites do Gmail

Conta Gmail pessoal tem um limite de ~500 e-mails/dia via SMTP — bem
acima do que uma recuperação de senha de um app pequeno deveria gerar.
Se um dia isso crescer muito, vale migrar pra um serviço transacional
(Resend, SendGrid, etc.), mas pra agora não tem necessidade.
