# Bot por WhatsApp com WAHA (à parte do bot oficial da Meta)

Isso é um **segundo caminho, paralelo**, pro mesmo bot (mesmo Claude, mesmo
banco, mesma tabela `whatsapp_usuarios`) — só que recebendo/enviando mensagem
via **WAHA** (WhatsApp HTTP API, usa seu WhatsApp pessoal via QR code, sem
precisar de verificação de empresa da Meta). Nada do bot oficial
(`/webhook/whatsapp`, `service/whatsapp_client.py`) foi alterado — quando o
MEI/verificação sair, aquele caminho continua exatamente como estava.

⚠️ **WAHA não é oficial/aprovado pela Meta** — ele conecta como se fosse o
WhatsApp Web. Existe risco (baixo, mas real) do número levar bloqueio por uso
automatizado. Pra só testar com um número pessoal, geralmente é tranquilo;
não é recomendado pra volume alto ou pro número principal de alguém.

## Como as duas pontas precisam se enxergar

O fluxo completo tem duas direções, e **as duas precisam de URL pública**:

- **WAHA → seu Flask**: quando chega mensagem no WhatsApp, o WAHA avisa via
  webhook em `https://my-financess-app.onrender.com/webhook/whatsapp-waha`
  (isso já está pronto, é só configurar no WAHA).
- **Seu Flask → WAHA**: quando o bot responde, o Flask (rodando no Render)
  precisa chamar a API do WAHA pra mandar a mensagem de volta. Se o WAHA
  estiver rodando só na sua máquina (`localhost`), o Render **não consegue
  alcançar isso** — só a primeira direção funcionaria, a resposta nunca
  chegaria.

Por isso, o jeito mais simples de deixar funcionando de ponta a ponta é
rodar o WAHA também com uma URL pública. Duas opções:

### Opção A — WAHA no Render (recomendado, estável)

1. No painel do Render, **New → Web Service**.
2. Em vez de conectar um repositório Git, escolha **"Deploy an existing
   image from a registry"** e use a imagem `devlikeapro/waha`.
3. Configure as variáveis de ambiente do próprio WAHA (usuário/senha do
   dashboard — ver documentação do WAHA pra saber as chaves exatas, mudam
   entre versões).
4. Porta: `3000`.
5. Depois do deploy, você terá uma URL tipo
   `https://waha-doisnoazul.onrender.com`.

> Atenção: sessão do WAHA fica em disco (`/app/.sessions`) — sem um **disco
> persistente** configurado no Render, a sessão (o vínculo com seu WhatsApp)
> some a cada novo deploy/reinício, e você precisaria escanear o QR de novo.
> Para só ir testando isso é aceitável; pra deixar estável vale configurar um
> "Persistent Disk" no Render apontando pra essa pasta.

### Opção B — WAHA local + túnel (mais rápido pra testar agora)

1. Rode localmente:
   ```sh
   docker run -it --env-file .env -v "$(pwd)/sessions:/app/.sessions" --rm -p 3000:3000 --name waha devlikeapro/waha
   ```
2. Exponha publicamente com um túnel, ex. **ngrok**:
   ```sh
   ngrok http 3000
   ```
   Isso te dá uma URL tipo `https://abcd1234.ngrok-free.app` — use essa URL
   no lugar de `http://localhost:3000` em tudo abaixo. Repare que essa URL
   muda toda vez que você reinicia o ngrok (no plano grátis), então
   precisaria atualizar `WAHA_API_URL` no Render de novo a cada sessão de
   teste.

## 1. Iniciar a sessão e escanear o QR

1. Acesse `http://localhost:3000/dashboard` (ou a URL pública, se optou pela
   Opção A) e entre com o usuário/senha configurados.
2. Inicie a sessão `"default"` e espere o status virar `SCAN_QR`.
3. Escaneie o QR code **com o WhatsApp do seu celular** (Configurações →
   Aparelhos conectados → Conectar um aparelho) — é o mesmo processo do
   WhatsApp Web.
4. Espere o status virar `WORKING`.

## 2. Configurar o webhook do WAHA

Ao criar/atualizar a sessão, mande esse `config` (pelo dashboard ou API):

```json
{
  "name": "default",
  "config": {
    "webhooks": [
      {
        "url": "https://my-financess-app.onrender.com/webhook/whatsapp-waha",
        "events": ["message"]
      }
    ]
  }
}
```

## 3. Variáveis de ambiente (no Render, do seu app Flask)

| Variável | Valor |
|---|---|
| `WAHA_API_URL` | URL pública do seu WAHA (ex: `https://waha-doisnoazul.onrender.com` ou a do ngrok) |
| `WAHA_API_KEY` | a mesma API key configurada no `.env` do WAHA |
| `WAHA_SESSION` | `default` (ou o nome que você usou) |

## 4. Vincular seu número e testar

Como é a **mesma tabela** `whatsapp_usuarios` do bot oficial, se você já
vinculou seu número em Configurações antes, **não precisa vincular de novo**
— o WAHA vai reconhecer o mesmo número automaticamente.

Manda uma mensagem pro seu próprio número (ou peça pra alguém mandar) pelo
WhatsApp normal — deve chegar no `/webhook/whatsapp-waha`, passar pela Claude
e responder pelo WAHA. Acompanhe o log do Render pra ver o que está
acontecendo em cada etapa (os mesmos `print()` de diagnóstico usados no bot
oficial também aparecem aqui, com "WAHA" na mensagem de erro quando algo
falha).
