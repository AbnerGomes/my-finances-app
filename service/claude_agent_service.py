import os
import json
from datetime import date

import anthropic

from service.gasto_service import GastoService

# Pode trocar pra "claude-haiku-4-5" (mais barato) via env var, sem mexer no código.
MODEL = os.environ.get("CLAUDE_MODEL_WHATSAPP", "claude-sonnet-5")

_PERIODOS_VALIDOS = [
    "hoje", "ontem", "semanaatual", "semanapassada", "mesatual", "mesanterior", "geral",
]

TOOLS = [
    {
        "name": "registrar_gasto",
        "description": (
            "Registra um novo gasto no extrato do usuário. Use quando o usuário disser que "
            "gastou, pagou ou comprou algo, informando um valor. Se a data não for mencionada, "
            "use a data de hoje."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "descricao": {
                    "type": "string",
                    "description": "Descrição curta do gasto, ex: 'Ifood', 'Uber', 'Supermercado'.",
                },
                "valor": {
                    "type": "number",
                    "description": "Valor em reais, ex: 45.90.",
                },
                "categoria": {
                    "type": "string",
                    "description": "Categoria do gasto. Reaproveite uma das categorias já usadas pelo usuário sempre que fizer sentido.",
                },
                "data": {
                    "type": "string",
                    "description": "Data no formato YYYY-MM-DD. Se o usuário não informar, use a data de hoje.",
                },
            },
            "required": ["descricao", "valor", "categoria", "data"],
            "additionalProperties": False,
        },
    },
    {
        "name": "consultar_gastos_periodo",
        "description": (
            "Consulta os gastos em um período: total, valor por categoria, e a lista de cada gasto "
            "individual (com a descrição/nome de cada um e de quem é). Use para perguntas como "
            "'quanto gastei hoje', 'quanto gastei esse mês', 'qual categoria eu mais gasto', "
            "'quanto gastei com X', ou sobre o cônjuge/casal (ex: 'quanto a Ana gastou', 'quanto "
            "gastamos'). IMPORTANTE: escolha o parâmetro 'escopo' com fidelidade ao que foi "
            "perguntado — se perguntaram só pelo cônjuge (pelo nome dele/dela, ou 'meu marido/minha "
            "esposa'), use 'conjuge' e responda SÓ sobre ele, sem misturar com os gastos do usuário. "
            "Se perguntaram pelos dois juntos ('nós', 'a gente', 'gastamos'), use 'ambos'. Se "
            "perguntaram só pelo usuário ('eu', 'meu'), use 'proprio'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "periodo": {
                    "type": "string",
                    "enum": _PERIODOS_VALIDOS,
                    "description": (
                        "hoje, ontem, semanaatual (domingo até hoje), semanapassada, "
                        "mesatual (dia 1 do mês até hoje), mesanterior, ou geral "
                        "(todo o histórico, sem filtro de data)."
                    ),
                },
                "categoria": {
                    "type": "string",
                    "description": "Opcional. Preencha se o usuário perguntar sobre uma categoria específica (ex: 'Delivery'), pra filtrar o resultado.",
                },
                "escopo": {
                    "type": "string",
                    "enum": ["proprio", "conjuge", "ambos"],
                    "description": (
                        "'proprio' (padrão) = só os gastos do próprio usuário. 'conjuge' = só os "
                        "gastos do cônjuge/parceiro(a), isolados (NUNCA inclui os do usuário). "
                        "'ambos' = os dois combinados (é assim que o Modo Casal do app funciona)."
                    ),
                },
            },
            "required": ["periodo"],
            "additionalProperties": False,
        },
    },
]


def _executar_tool(nome_tool, tool_input, usuario_nome, gasto_service):
    if nome_tool == "registrar_gasto":
        sucesso = gasto_service.salvar_gasto(
            tool_input["descricao"],
            tool_input["valor"],
            tool_input["data"],
            tool_input["categoria"],
            usuario_nome,
        )
        return {"sucesso": sucesso}

    if nome_tool == "consultar_gastos_periodo":
        periodo = tool_input["periodo"]
        escopo = tool_input.get("escopo", "proprio")
        if escopo not in ("proprio", "conjuge", "ambos"):
            escopo = "proprio"

        itens = gasto_service.consultar_gastos_bot(usuario_nome, periodo, escopo)

        if itens is None:
            # escopo='conjuge' pedido, mas o usuário não tem cônjuge vinculado
            return {"erro": "Esse usuário não tem cônjuge/parceiro(a) vinculado ainda."}

        categoria_filtro = tool_input.get("categoria")
        if categoria_filtro:
            itens = [
                i for i in itens
                if i["categoria"].strip().lower() == categoria_filtro.strip().lower()
            ]

        total = sum(i["valor"] for i in itens)
        por_categoria = {}
        for i in itens:
            por_categoria[i["categoria"]] = por_categoria.get(i["categoria"], 0) + i["valor"]

        return {
            "escopo": escopo,  # confirma pra Claude de quem é esse resultado
            "total": round(total, 2),
            "por_categoria": [
                {"categoria": c, "valor": round(v, 2)} for c, v in por_categoria.items()
            ],
            # gastos individuais (com nome/descrição e de quem é) — pra Claude
            # poder citar o gasto específico quando fizer sentido, em vez de
            # só dar o total
            "itens": [
                {"descricao": i["descricao"], "valor": round(i["valor"], 2), "categoria": i["categoria"], "data": i["data"], "de": i["de"]}
                for i in itens
            ],
        }

    return {"erro": f"tool desconhecida: {nome_tool}"}


# Se a chamada pra API da Claude falhar por qualquer motivo (sem crédito,
# rate limit, instabilidade, chave inválida, etc.), quem está do outro
# lado do WhatsApp não pode ver um erro técnico — melhor uma mensagem
# educada dizendo que o assistente está temporariamente fora, sem
# expor detalhe nenhum de infraestrutura.
MENSAGEM_ASSISTENTE_INDISPONIVEL = (
    "O assistente está em manutenção temporária 🛠️ — mas você pode continuar "
    "usando o app normalmente. Em caso de dúvidas, entre em contato com o "
    "administrador pela tela de Configurações do app."
)


def responder_mensagem(mensagem_usuario, usuario_nome, gasto_service=None):
    """Recebe o texto de uma mensagem de WhatsApp já vinculada a uma conta
    (usuario_nome = mesmo valor de session['usuario']/autenticacao.nome),
    roda o loop de tool-use da Claude e devolve o texto de resposta final
    a ser enviado de volta pelo WhatsApp.

    Qualquer falha (API da Claude sem crédito, erro de rede, etc.) é
    tratada aqui dentro — nunca propaga pra quem chamou, pra sempre poder
    mandar uma resposta de volta pro WhatsApp em vez de deixar o usuário
    sem resposta nenhuma."""
    try:
        return _responder_mensagem(mensagem_usuario, usuario_nome, gasto_service)
    except Exception as e:
        print("Erro ao chamar a API da Claude (assistente WhatsApp):", e)
        return MENSAGEM_ASSISTENTE_INDISPONIVEL


def _responder_mensagem(mensagem_usuario, usuario_nome, gasto_service=None):
    gasto_service = gasto_service or GastoService()
    client = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

    categorias = gasto_service.get_categorias_completas(usuario_nome, "N")
    tem_conjuge = gasto_service.tem_conjuge(usuario_nome)
    hoje = date.today().isoformat()

    aviso_conjuge = (
        "O usuário TEM um cônjuge/parceiro(a) vinculado (Modo Casal ativo). Ao consultar gastos, "
        "escolha o escopo com fidelidade: perguntou só pelo cônjuge (pelo nome dele/dela, ou 'meu "
        "marido'/'minha esposa' sem se incluir) → escopo='conjuge', e fale SÓ dele/dela na resposta, "
        "nunca misture com os gastos do usuário. Perguntou pelos dois ('nós', 'a gente', 'gastamos') "
        "→ escopo='ambos'. Perguntou só por si mesmo ('eu', 'meu') → escopo='proprio'."
        if tem_conjuge else
        "O usuário NÃO tem cônjuge/parceiro(a) vinculado ainda. Se ele perguntar sobre gastos do "
        "cônjuge/casal, avise que precisa vincular um cônjuge em Configurações → Modo Casal primeiro."
    )

    system_prompt = (
        f"Você é o assistente financeiro do app \"Dois no Azul\", respondendo por WhatsApp.\n"
        f"A data de hoje é {hoje}. O usuário já está autenticado — nunca pergunte quem ele é.\n"
        f"Categorias já usadas por este usuário: {', '.join(categorias) if categorias else '(nenhuma ainda)'}.\n"
        f"{aviso_conjuge}\n"
        f"Ao registrar um gasto, reaproveite uma categoria existente da lista acima sempre que fizer "
        f"sentido; só use uma categoria nova se nenhuma existente encaixar.\n"
        f"Ao responder sobre gastos consultados, seja específico: cite a descrição/nome de cada gasto "
        f"relevante (não só o total) quando o período tiver poucos itens (ex.: 'hoje') ou quando o "
        f"usuário perguntar sobre algo específico. Em respostas sobre o cônjuge ou 'ambos', use o "
        f"campo 'de' de cada item pra saber de quem é cada gasto e atribuir corretamente (ex.: 'Ana "
        f"gastou R$ 7,99 com Café da manhã'). Pra períodos longos com muitos itens, resuma por "
        f"categoria em vez de listar tudo.\n"
        f"Responda sempre em português, de forma curta e direta — é uma conversa de WhatsApp, não um "
        f"relatório. Valores monetários: escreva em reais com vírgula, ex: R$ 45,90."
    )

    messages = [{"role": "user", "content": mensagem_usuario}]

    for _ in range(5):  # limite de segurança contra loop infinito de tool use
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            texto = next((b.text for b in response.content if b.type == "text"), "")
            return texto or "Não consegui gerar uma resposta agora, tenta de novo em instantes."

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for bloco in response.content:
            if bloco.type != "tool_use":
                continue
            try:
                resultado = _executar_tool(bloco.name, bloco.input, usuario_nome, gasto_service)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": bloco.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": bloco.id,
                    "content": f"Erro ao executar: {e}",
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})

    return "Desculpa, não consegui processar seu pedido agora. Tenta reformular?"
