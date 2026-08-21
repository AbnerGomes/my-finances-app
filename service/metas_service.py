from datetime import datetime

import psycopg2

from .db_service import get_connection

# "Metas" viraram duas coisas na mesma tabela, distinguidas pela coluna
# `tipo`: 'limite' (não posso gastar mais que R$X com Y por mês — estourar
# é ruim) e 'objetivo' (quero guardar/investir R$X numa categoria por mês
# — chegar ou passar de R$X é bom). As duas usam exatamente a mesma conta:
# soma dos GASTOS daquela categoria no mês. De propósito, olha só a
# tabela `gastos` (gasto avulso), NUNCA soma junto com `despesas` —
# despesa_service.criar_gasto_da_despesa às vezes lança um gasto a partir
# de uma despesa paga, então somar as duas tabelas contaria a mesma
# despesa em dobro.


def _get_usuario_by_name(nome):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT usuario FROM autenticacao WHERE nome = %s', (nome,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else nome
    finally:
        conn.close()


def _get_conjuge(cursor, usuario, isCasal):
    if isCasal != 'S':
        return ''

    cursor.execute(
        """SELECT a.usuario AS conjuge FROM casal c
           JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END
           WHERE %s IN (c.conjuge_1, c.conjuge_2)""",
        (usuario, usuario)
    )
    resultado = cursor.fetchone()
    return resultado[0] if resultado else ''


def _nivel(percentual, tipo='limite'):
    if tipo == 'objetivo':
        # objetivo é o oposto de limite: chegar ou passar de 100% é a
        # meta sendo batida, não um estouro — não faz sentido "amarelo de
        # alerta" no meio do caminho, só "em progresso" e "concluído"
        return 'concluido' if percentual >= 100 else 'progresso'

    if percentual >= 100:
        return 'vermelho'
    if percentual >= 80:
        return 'amarelo'
    return 'verde'


# Cor da barra de progresso: em vez de 3-4 faixas fixas, interpola de
# verdade entre "paradas" de cor conforme o percentual, pra dar a
# sensação de transição gradual (o pedido foi literalmente "vai ficando
# mais próximo da cor X conforme..."). Limite: verde -> amarelo -> vermelho
# -> vermelho bem escuro quando estoura de vez. Objetivo: o oposto em
# espírito — laranja fraquinho no começo, esquentando pro verde
# conforme se aproxima do valor final.
_CORES_LIMITE = [
    (0, (34, 197, 94)),     # verde (--dna-green)
    (80, (250, 204, 21)),   # amarelo
    (100, (239, 68, 68)),   # vermelho (--danger)
    (130, (127, 29, 29)),   # vermelho bem escuro — "super vermelho" ao estourar de vez
]

_CORES_OBJETIVO = [
    (0, (253, 186, 116)),   # laranja fraquinho
    (100, (34, 197, 94)),   # verde (--dna-green) ao bater a meta
]


def _interpolar_cor(percentual, paradas):
    if percentual <= paradas[0][0]:
        cor = paradas[0][1]
    elif percentual >= paradas[-1][0]:
        cor = paradas[-1][1]
    else:
        cor = paradas[-1][1]
        for (p0, c0), (p1, c1) in zip(paradas, paradas[1:]):
            if p0 <= percentual <= p1:
                t = (percentual - p0) / (p1 - p0) if p1 != p0 else 0
                cor = tuple(round(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
                break

    return '#{:02x}{:02x}{:02x}'.format(*cor)


def _cor_barra(percentual, tipo):
    percentual = max(0, percentual)
    if tipo == 'objetivo':
        return _interpolar_cor(min(percentual, 100), _CORES_OBJETIVO)
    return _interpolar_cor(min(percentual, 130), _CORES_LIMITE)


def gasto_categoria_mes_atual(usuario_nome, categoria, isCasal='N'):
    """Quanto já foi gasto (tabela gastos, não despesas) numa categoria,
    do dia 1 do mês atual até hoje. usuario_nome é o valor de
    session['usuario'] (nome, não e-mail) — resolvido aqui dentro."""
    usuario = _get_usuario_by_name(usuario_nome)
    hoje = datetime.today().date()
    inicio_mes = hoje.replace(day=1)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        conjuge = _get_conjuge(cursor, usuario, isCasal)

        cursor.execute(
            """SELECT COALESCE(SUM(valor_gasto), 0) FROM gastos
               WHERE usuario IN (%s, %s) AND categoria = %s AND data BETWEEN %s AND %s""",
            (usuario, conjuge or usuario, categoria, inicio_mes, hoje)
        )
        return float(cursor.fetchone()[0])
    finally:
        conn.close()


def listar_metas(usuario_nome, isCasal='N', tipo=None):
    """Metas SEMPRE da conta que está vendo (nunca a do cônjuge — cada
    um define seu próprio limite/objetivo); só o gasto contado contra
    esse valor passa a somar o cônjuge quando isCasal='S'. `tipo` filtra
    por 'limite'/'objetivo'; None traz os dois tipos juntos (usado pelos
    insights, que precisam saber de todas as categorias já "tomadas")."""
    usuario = _get_usuario_by_name(usuario_nome)
    hoje = datetime.today().date()
    inicio_mes = hoje.replace(day=1)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        conjuge = _get_conjuge(cursor, usuario, isCasal)

        if tipo:
            cursor.execute(
                "SELECT id, nome, categoria, limite, tipo FROM metas WHERE usuario = %s AND tipo = %s ORDER BY nome",
                (usuario, tipo)
            )
        else:
            cursor.execute(
                "SELECT id, nome, categoria, limite, tipo FROM metas WHERE usuario = %s ORDER BY nome",
                (usuario,)
            )
        metas = cursor.fetchall()

        resultado = []
        for id_meta, nome, categoria, limite, tipo_meta in metas:
            cursor.execute(
                """SELECT COALESCE(SUM(valor_gasto), 0) FROM gastos
                   WHERE usuario IN (%s, %s) AND categoria = %s AND data BETWEEN %s AND %s""",
                (usuario, conjuge or usuario, categoria, inicio_mes, hoje)
            )
            gasto_atual = float(cursor.fetchone()[0])
            limite = float(limite)
            percentual = round((gasto_atual / limite) * 100, 1) if limite > 0 else 0

            resultado.append({
                'id': id_meta,
                'nome': nome,
                'categoria': categoria,
                'limite': round(limite, 2),
                'gasto_atual': round(gasto_atual, 2),
                'percentual': percentual,
                'tipo': tipo_meta,
                'nivel': _nivel(percentual, tipo_meta),
                'cor_barra': _cor_barra(percentual, tipo_meta),
            })

        return resultado
    finally:
        conn.close()


def categorias_em_uso(usuario_nome):
    """Categorias que já têm meta (limite OU objetivo, qualquer um dos
    dois) pra essa conta — usado pra tirar da lista de "categorias
    disponíveis pra criar", já que uma categoria só pode ter uma meta."""
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT categoria FROM metas WHERE usuario = %s", (usuario,))
        return {row[0] for row in cursor.fetchall()}
    finally:
        conn.close()


def criar_meta(usuario_nome, categoria, limite, tipo='limite', nome=None):
    usuario = _get_usuario_by_name(usuario_nome)
    # nome é escolhido livremente por quem cria (ex.: "Besteiras" pra
    # categoria Ifood) — a categoria continua sendo só o acumulador dos
    # gastos, nunca o rótulo mostrado. Cai pra categoria só como rede de
    # segurança (nunca deve faltar vindo do form).
    nome = (nome or '').strip() or categoria

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO metas (usuario, nome, categoria, limite, tipo) VALUES (%s, %s, %s, %s, %s)",
            (usuario, nome, categoria, limite, tipo)
        )
        conn.commit()
        return {'sucesso': True}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        rotulo = 'objetivo' if tipo == 'objetivo' else 'limite'
        return {'sucesso': False, 'erro': f'Você já tem um(a) {rotulo} pra categoria "{categoria}". Edite o existente em vez de criar outro.'}
    except Exception as e:
        conn.rollback()
        print("Erro ao criar meta:", e)
        return {'sucesso': False, 'erro': 'Não foi possível criar.'}
    finally:
        conn.close()


def editar_meta(usuario_nome, id_meta, limite, nome=None):
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        if nome and nome.strip():
            cursor.execute(
                "UPDATE metas SET limite = %s, nome = %s, data_atualizacao = NOW() WHERE id = %s AND usuario = %s",
                (limite, nome.strip(), id_meta, usuario)
            )
        else:
            cursor.execute(
                "UPDATE metas SET limite = %s, data_atualizacao = NOW() WHERE id = %s AND usuario = %s",
                (limite, id_meta, usuario)
            )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print("Erro ao editar meta:", e)
        return False
    finally:
        conn.close()


def verificar_transacao(usuario_nome, categoria, valor_novo, isCasal='N'):
    """Chamado ANTES de salvar um gasto, pra avisar se ele vai cruzar um
    limite/objetivo configurado pra essa categoria. Devolve None se não
    há meta pra essa categoria ou se não há nada a avisar; senão devolve
    {'tipo', 'nome', 'valor_meta', 'novo_total'}.

    Limite: avisa toda vez que o total ficar acima dele (cada gasto a
    mais enquanto já estourado piora a situação, vale repetir o aviso).
    Objetivo: avisa só na transação que CRUZA o valor pela primeira vez
    (gasto_atual ainda abaixo, novo_total já bate ou passa) — depois de
    batido uma vez não faz sentido reavisar "você atingiu" a cada gasto
    novo na mesma categoria."""
    usuario = _get_usuario_by_name(usuario_nome)
    hoje = datetime.today().date()
    inicio_mes = hoje.replace(day=1)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nome, limite, tipo FROM metas WHERE usuario = %s AND categoria = %s",
            (usuario, categoria)
        )
        row = cursor.fetchone()
        if not row:
            return None

        nome, limite, tipo = row
        limite = float(limite)
        conjuge = _get_conjuge(cursor, usuario, isCasal)

        cursor.execute(
            """SELECT COALESCE(SUM(valor_gasto), 0) FROM gastos
               WHERE usuario IN (%s, %s) AND categoria = %s AND data BETWEEN %s AND %s""",
            (usuario, conjuge or usuario, categoria, inicio_mes, hoje)
        )
        gasto_atual = float(cursor.fetchone()[0])
        novo_total = gasto_atual + float(valor_novo)

        if tipo == 'objetivo':
            if gasto_atual < limite <= novo_total:
                return {'tipo': 'objetivo', 'nome': nome, 'valor_meta': round(limite, 2), 'novo_total': round(novo_total, 2)}
            return None

        if novo_total > limite:
            return {'tipo': 'limite', 'nome': nome, 'valor_meta': round(limite, 2), 'novo_total': round(novo_total, 2)}
        return None
    finally:
        conn.close()


def excluir_meta(usuario_nome, id_meta):
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM metas WHERE id = %s AND usuario = %s", (id_meta, usuario))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
