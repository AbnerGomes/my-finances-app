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
            "Consulta o total gasto e o detalhamento por categoria em um período. Use para perguntas "
            "como 'quanto gastei hoje', 'quanto gastei ontem', 'quanto gastei esse mês', "
            "'qual categoria eu mais gasto' ou 'quanto gastei com X'."
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
                    "description": "Opcional. Preencha se o usuário perguntar sobre uma categoria específica (ex: 'Ifood'), pra filtrar o resultado.",
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
        periodo_query = None if periodo == "geral" else periodo
        linhas = gasto_service.filtrarGastos(periodo_query, usuario_nome, "N") or []

        categoria_filtro = tool_input.get("categoria")
        if categoria_filtro:
            linhas = [
                l for l in linhas
                if l["categoria"].strip().lower() == categoria_filtro.strip().lower()
            ]

        total = sum(float(l["valor"] or 0) for l in linhas)
        return {
            "total": round(total, 2),
            "por_categoria": [
                {"categoria": l["categoria"], "valor": round(float(l["valor"] or 0), 2)}
                for l in linhas
            ],
        }

    return {"erro": f"tool desconhecida: {nome_tool}"}


def responder_mensagem(mensagem_usuario, usuario_nome, gasto_service=None):
    """Recebe o texto de uma mensagem de WhatsApp já vinculada a uma conta
    (usuario_nome = mesmo valor de session['usuario']/autenticacao.nome),
    roda o loop de tool-use da Claude e devolve o texto de resposta final
    a ser enviado de volta pelo WhatsApp."""

    gasto_service = gasto_service or GastoService()
    client = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

    categorias = gasto_service.get_categorias_completas(usuario_nome, "N")
    hoje = date.today().isoformat()

    system_prompt = (
        f"Você é o assistente financeiro do app \"Dois no Azul\", respondendo por WhatsApp.\n"
        f"A data de hoje é {hoje}. O usuário já está autenticado — nunca pergunte quem ele é.\n"
        f"Categorias já usadas por este usuário: {', '.join(categorias) if categorias else '(nenhuma ainda)'}.\n"
        f"Ao registrar um gasto, reaproveite uma categoria existente da lista acima sempre que fizer "
        f"sentido; só use uma categoria nova se nenhuma existente encaixar.\n"
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
