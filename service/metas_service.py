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
                "SELECT id, categoria, limite, tipo FROM metas WHERE usuario = %s AND tipo = %s ORDER BY categoria",
                (usuario, tipo)
            )
        else:
            cursor.execute(
                "SELECT id, categoria, limite, tipo FROM metas WHERE usuario = %s ORDER BY categoria",
                (usuario,)
            )
        metas = cursor.fetchall()

        resultado = []
        for id_meta, categoria, limite, tipo_meta in metas:
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
                'categoria': categoria,
                'limite': round(limite, 2),
                'gasto_atual': round(gasto_atual, 2),
                'percentual': percentual,
                'tipo': tipo_meta,
                'nivel': _nivel(percentual, tipo_meta),
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


def criar_meta(usuario_nome, categoria, limite, tipo='limite'):
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO metas (usuario, categoria, limite, tipo) VALUES (%s, %s, %s, %s)",
            (usuario, categoria, limite, tipo)
        )
        conn.commit()
        return {'sucesso': True}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        rotulo = 'objetivo' if tipo == 'objetivo' else 'limite'
        return {'sucesso': False, 'erro': f'Você já tem um(a) {rotulo} pra "{categoria}". Edite o existente em vez de criar outro.'}
    except Exception as e:
        conn.rollback()
        print("Erro ao criar meta:", e)
        return {'sucesso': False, 'erro': 'Não foi possível criar.'}
    finally:
        conn.close()


def editar_meta(usuario_nome, id_meta, limite):
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
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
