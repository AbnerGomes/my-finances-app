# Bot financeiro por WhatsApp — o que fazer para deixar rodando

Esse recurso deixa o usuário registrar gastos e consultar dados ("quanto
gastei hoje", "qual categoria eu mais gasto"...) mandando mensagem de
WhatsApp pro número da Meta Cloud API. A Claude decide, a partir da
mensagem, se deve chamar a tool `registrar_gasto` (insere no banco) ou
`consultar_gastos_periodo` (consulta o banco), sempre restrita à conta já
vinculada àquele número de telefone.

## 0. Rodar a migração no banco

Antes de qualquer coisa, criar a tabela que liga telefone → conta:

```sql
CREATE TABLE whatsapp_usuarios (
    id SERIAL PRIMARY KEY,
    telefone TEXT UNIQUE NOT NULL,
    usuario TEXT NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW()
);
```

Rode isso no seu Postgres do Render (mesmo jeito que rodou os INSERTs em
massa antes — via psql ou uma ferramenta de banco apontando pro
`DATABASE_URL`).

## 1. Criar a conta de API da Claude (separada do Claude Pro)

Sua assinatura Claude Pro (claude.ai) **não** dá acesso a isso — é preciso
uma conta separada:

1. Acesse **console.anthropic.com** e crie uma conta (pode ser com o
   mesmo email).
2. Em **Billing**, adicione um cartão e coloque um crédito pré-pago
   (ex: US$ 5 já cobre bastante tempo de teste — ver estimativa de custo
   mais abaixo).
3. Em **API Keys**, gere uma chave (`sk-ant-...`) — essa é a
   `ANTHROPIC_API_KEY`.

## 2. Criar o app no Meta e o número de WhatsApp (Cloud API oficial)

1. Vá em **developers.facebook.com** → **Meus Apps** → **Criar app** →
   tipo **Negócios**.
2. Dentro do app, adicione o produto **WhatsApp**.
3. O Meta te dá automaticamente um **número de teste grátis** e um
   **token temporário** (válido por 24h) — use isso pra testar primeiro,
   sem mexer no seu número pessoal.
4. Anote:
   - **Phone number ID** (aparece na tela do produto WhatsApp) →
     `WHATSAPP_PHONE_NUMBER_ID`
   - **Token de acesso** (temporário no começo; depois de validar, gere
     um **permanente** via *System User* em Business Settings) →
     `WHATSAPP_TOKEN`
   - **App Secret** (em Configurações do App → Básico) →
     `WHATSAPP_APP_SECRET`

> ⚠️ **Sobre usar seu número pessoal (51 995035983):** só registre esse
> número na Cloud API se ele **não estiver mais em uso no app normal do
> WhatsApp** nesse aparelho — a Cloud API assume o número por completo, e
> ele deixa de funcionar como conversa normal de WhatsApp App nesse
> celular. Pra testar sem esse risco, use o número de teste grátis do
> Meta primeiro; só migre pro seu número quando tiver certeza.

## 3. Variáveis de ambiente

No Render (Settings → Environment) e localmente (`.env`/export antes de
rodar), configure:

| Variável | De onde vem |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `WHATSAPP_TOKEN` | token da Cloud API (temporário ou permanente) |
| `WHATSAPP_PHONE_NUMBER_ID` | tela do produto WhatsApp no Meta |
| `WHATSAPP_APP_SECRET` | Configurações do App → Básico, no Meta |
| `WHATSAPP_VERIFY_TOKEN` | uma string qualquer que **você** inventa (ex: `dna-webhook-2026`) — só precisa bater dos dois lados |
| `CLAUDE_MODEL_WHATSAPP` | opcional — default é `claude-sonnet-5`; pode trocar para `claude-haiku-4-5` se quiser ainda mais barato |

## 4. Configurar o Webhook no Meta

1. No produto WhatsApp → **Configuration** → **Webhook** → **Edit**.
2. **Callback URL**: `https://<seu-app>.onrender.com/webhook/whatsapp`
3. **Verify Token**: o mesmo valor que você colocou em
   `WHATSAPP_VERIFY_TOKEN`.
4. Clique em **Verify and Save** (o Meta chama o GET do endpoint — se
   tudo estiver certo, aparece verificado).
5. Em **Webhook fields**, clique **Subscribe** no campo **messages**.

## 5. Vincular seu número de WhatsApp à sua conta no app

Já é self-service: entre no app → **Configurações** → tem um campo novo
"WhatsApp" → digite o número (com DDD, sem +55) → **Salvar**. Isso grava
na tabela `whatsapp_usuarios`, ligando aquele telefone à sua conta.

## 6. Testar

Manda uma mensagem pro número configurado no Meta (o de teste, no
começo), de dentro do WhatsApp normal:

- `"gastei 35 reais com ifood hoje"` → deve registrar e confirmar.
- `"quanto gastei esse mês?"` → deve responder com o total.
- `"qual categoria eu mais gasto?"` → deve responder com a maior.

## Custo estimado

Cada mensagem trocada custa uma fração de centavo em tokens da Claude
(sistema+tools+resposta ficam na casa de ~2500 tokens de entrada e ~150
de saída). Com Sonnet 5: ~R$ 0,03–0,04 por mensagem. Com Haiku 4.5
(`CLAUDE_MODEL_WHATSAPP=claude-haiku-4-5`): menos da metade disso. Pra uso
pessoal (algumas dezenas de mensagens por dia), estamos falando de menos
de R$ 10–20/mês — mais barato ainda com o Meta Cloud API, que não cobra
por mensagem recebida/respondida dentro da janela de 24h de conversa
iniciada pelo usuário.

## O que NÃO está incluído ainda (possíveis próximos passos)

- Suporte a "Modo Casal" no bot (hoje sempre consulta como Individual).
- Consultas por ano inteiro (só tem hoje/ontem/semana/mês atual e
  anterior/geral).
- Confirmação antes de registrar um gasto (hoje registra direto quando a
  Claude entende que é um gasto).
