# Recuperação de senha por e-mail (Resend)

A tela "Esqueci minha senha" manda um código de 6 dígitos por e-mail
(válido por 15 minutos), usando a API do **Resend** (envio via HTTPS).

> ⚠️ **Por que não Gmail SMTP direto**: foi a primeira tentativa, mas o
> Render bloqueia conexão SMTP de saída (porta 587/465) nas contas —
> confirmado em produção com o erro `[Errno 101] Network is
> unreachable`. A API do Resend evita isso porque roda sobre HTTPS
> normal (porta 443), que não é bloqueada.

## 1. Criar conta no Resend

1. Acesse [resend.com](https://resend.com) e crie uma conta (gratuita,
   sem cartão de crédito — 3.000 e-mails/mês, 100/dia).
2. No painel, vá em **API Keys** → **Create API Key**. Dá um nome (ex:
   "Dois no Azul") e copia a chave gerada (começa com `re_`) — só
   aparece uma vez.

## 2. Configurar no Render

No painel do Render, no seu app principal → **Environment**, adiciona:

| Variável | Valor |
|---|---|
| `RESEND_API_KEY` | a chave gerada no passo 1 (`re_...`) |
| `RESEND_FROM` | opcional — ver limitação abaixo antes de mudar o padrão |

Salva e espera o redeploy (ou clica em "Manual Deploy").

## 3. ⚠️ Limitação importante: domínio de envio

**Sem verificar um domínio próprio no Resend**, o remetente só pode ser
`onboarding@resend.dev` (o padrão já configurado no código) — e o
Resend só entrega e-mails pro **próprio endereço que você usou pra criar
a conta** nesse modo. Ou seja: **funciona pra você testar**, mas
**não funciona pra outros usuários reais** pedirem recuperação de senha
ainda.

Pra liberar o envio pra qualquer usuário, é preciso:

1. Ter um domínio próprio (ex: `doisnoazul.com.br` — se não tiver
   ainda, precisaria registrar um).
2. No Resend, ir em **Domains** → **Add Domain**, colocar o domínio.
3. Adicionar os registros DNS (SPF, DKIM) que o Resend mostrar, no
   painel de onde o domínio foi registrado.
4. Esperar o Resend verificar (geralmente minutos, pode levar até 24h).
5. Trocar a variável `RESEND_FROM` pra algo como
   `Dois no Azul <naoresponda@doisnoazul.com.br>`.

**Se você não tem domínio ainda**, dá pra deixar assim mesmo por
enquanto (funcionando só pra você testar) e resolver o domínio depois,
sem pressa — nenhum código precisa mudar, só a variável de ambiente.

## 4. Testar

1. Na tela de login, clica em "Esqueci minha senha".
2. Digita o e-mail que você usou pra criar a conta Resend (por causa da
   limitação acima).
3. Deve chegar o código em alguns segundos (confere spam também).

Sem `RESEND_API_KEY` configurada, o app não trava — só não envia o
e-mail (fica logado no Render: `RESEND_API_KEY não configurado`).
