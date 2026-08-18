from datetime import datetime

import psycopg2

from .db_service import get_connection

# Metas de gasto por categoria (fase 1 — "não posso gastar mais que R$X
# com Y por mês"). De propósito, olha só a tabela `gastos` (gasto avulso),
# NUNCA soma junto com `despesas` — despesa_service.criar_gasto_da_despesa
# às vezes lança um gasto a partir de uma despesa paga, então somar as
# duas tabelas contaria a mesma despesa em dobro.


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


def _nivel(percentual):
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


def listar_metas(usuario_nome, isCasal='N'):
    """Metas SEMPRE da conta que está vendo (nunca a do cônjuge — cada
    um define seu próprio limite); só o gasto contado contra esse limite
    passa a somar o cônjuge quando isCasal='S'."""
    usuario = _get_usuario_by_name(usuario_nome)
    hoje = datetime.today().date()
    inicio_mes = hoje.replace(day=1)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        conjuge = _get_conjuge(cursor, usuario, isCasal)

        cursor.execute(
            "SELECT id, categoria, limite FROM metas WHERE usuario = %s ORDER BY categoria",
            (usuario,)
        )
        metas = cursor.fetchall()

        resultado = []
        for id_meta, categoria, limite in metas:
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
                'nivel': _nivel(percentual),
            })

        return resultado
    finally:
        conn.close()


def criar_meta(usuario_nome, categoria, limite):
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO metas (usuario, categoria, limite) VALUES (%s, %s, %s)",
            (usuario, categoria, limite)
        )
        conn.commit()
        return {'sucesso': True}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {'sucesso': False, 'erro': f'Você já tem uma meta pra "{categoria}". Edite a existente em vez de criar outra.'}
    except Exception as e:
        conn.rollback()
        print("Erro ao criar meta:", e)
        return {'sucesso': False, 'erro': 'Não foi possível criar a meta.'}
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
