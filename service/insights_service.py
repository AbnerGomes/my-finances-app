"""Motor de "avisos inteligentes" da home — regras determinísticas, sem
banco e sem chamada de LLM (nada de custo/latência de API aqui, e o
resultado tem que ser sempre previsível). Recebe dados já buscados
pelas rotas e devolve o insight de maior prioridade (ou None).
"""

LIMIAR_META_PROXIMA = 80  # % do limite a partir do qual já avisa "quase lá"
LIMIAR_CATEGORIA_SEM_META_SEM_HISTORICO = 300  # R$ — piso pra não avisar de categoria nova/pequena
FATOR_AUMENTO_CATEGORIA = 1.3  # 30% acima do mês anterior já é considerado "atípico"


def _maior_percentual(metas, minimo, maximo=None):
    # só considera metas do tipo 'limite' — pra 'objetivo' chegar ou
    # passar de 100% é a meta sendo batida, não um estouro pra alertar
    candidatas = [
        m for m in metas
        if m.get('tipo', 'limite') == 'limite'
        and m['percentual'] >= minimo and (maximo is None or m['percentual'] < maximo)
    ]
    if not candidatas:
        return None
    # desempate: maior estouro em R$ (não só percentual)
    return max(candidatas, key=lambda m: (m['percentual'], m['gasto_atual'] - m['limite']))


def _categoria_atipica(gastos_atual, gastos_anterior, categorias_com_meta):
    valores_anterior = {g['categoria']: float(g['valor'] or 0) for g in gastos_anterior}
    candidatas = []

    for g in gastos_atual:
        categoria = g['categoria']
        if categoria in categorias_com_meta:
            continue

        valor_atual = float(g['valor'] or 0)
        valor_anterior = valores_anterior.get(categoria, 0)

        atipico = (
            (valor_anterior > 0 and valor_atual > valor_anterior * FATOR_AUMENTO_CATEGORIA)
            or (valor_anterior == 0 and valor_atual > LIMIAR_CATEGORIA_SEM_META_SEM_HISTORICO)
        )
        if atipico:
            candidatas.append({'categoria': categoria, 'valor_atual': valor_atual, 'valor_anterior': valor_anterior})

    if not candidatas:
        return None
    return max(candidatas, key=lambda c: c['valor_atual'])


def calcular_insight(resumo_despesas, tem_pendencias_mes_anterior, metas, gastos_categoria_atual, gastos_categoria_anterior):
    # 1. meta estourada
    estourada = _maior_percentual(metas, minimo=100)
    if estourada:
        return {
            'nivel': 'perigo',
            'texto': f"Você já passou do limite em \"{estourada['categoria']}\": R$ {estourada['gasto_atual']:.2f} de R$ {estourada['limite']:.2f} planejados este mês.",
            'acao_label': 'Ver limites',
            'acao_url': '/metas',
        }

    # 2. despesas vencidas (meses anteriores)
    if tem_pendencias_mes_anterior and tem_pendencias_mes_anterior > 0:
        return {
            'nivel': 'perigo',
            'texto': f"Você tem {tem_pendencias_mes_anterior} despesa(s) de meses anteriores ainda não paga(s).",
            'acao_label': 'Ver despesas',
            'acao_url': '/despesas?pendentes_antigos=S',
        }

    # 3. meta perto do limite
    proxima = _maior_percentual(metas, minimo=LIMIAR_META_PROXIMA, maximo=100)
    if proxima:
        return {
            'nivel': 'aviso',
            'texto': f"Você já usou {proxima['percentual']:.0f}% do limite de \"{proxima['categoria']}\" este mês (R$ {proxima['gasto_atual']:.2f} de R$ {proxima['limite']:.2f}).",
            'acao_label': 'Ver limites',
            'acao_url': '/metas',
        }

    # 4. despesas pendentes deste mês (ainda não venceram, mas faltam pagar)
    pendentes_e_parciais = resumo_despesas.get('pendentes', 0) + resumo_despesas.get('parciais', 0)
    if pendentes_e_parciais > 0:
        return {
            'nivel': 'info',
            'texto': f"Você tem {pendentes_e_parciais} despesa(s) pendente(s) este mês, totalizando R$ {resumo_despesas.get('valor_pendente', 0):.2f}.",
            'acao_label': 'Ver despesas',
            'acao_url': '/despesas',
        }

    # 5. categoria sem meta com gasto atípico
    categorias_com_meta = {m['categoria'] for m in metas}
    atipica = _categoria_atipica(gastos_categoria_atual, gastos_categoria_anterior, categorias_com_meta)
    if atipica:
        return {
            'nivel': 'sugestao',
            'texto': f"Você já gastou R$ {atipica['valor_atual']:.2f} com \"{atipica['categoria']}\" este mês. Quer criar um limite pra essa categoria?",
            'acao_label': 'Criar limite',
            'acao_url': '/metas',
            'acao_categoria': atipica['categoria'],
        }

    # 6. tudo pago
    if resumo_despesas.get('total', 0) > 0 and pendentes_e_parciais == 0:
        return {
            'nivel': 'sucesso',
            'texto': 'Todas as despesas deste mês estão pagas! 🎉',
            'acao_label': None,
            'acao_url': None,
        }

    return None
