from .db_service import get_connection


# Controla "não mostrar mais" dos tutoriais/dicas (home, despesas, receitas,
# extrato) por USUÁRIO e por TELA — antes era só localStorage no navegador,
# que não persiste de forma confiável dentro do WebView do app Android
# (a dica voltava a aparecer toda hora). Guardando no banco, uma vez
# marcado "não mostrar mais" fica assim pra sempre, em qualquer aparelho.

def _get_usuario_by_name(nome):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT usuario FROM autenticacao WHERE nome = %s', (nome,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else nome
    finally:
        conn.close()


def tutorial_visto(usuario_nome, tutorial):
    """True se esse usuário já marcou 'não mostrar mais' pra essa tela."""
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM tutoriais_vistos WHERE usuario = %s AND tutorial = %s",
            (usuario, tutorial)
        )
        return cursor.fetchone() is not None
    except Exception as e:
        # tabela indisponível por algum motivo — não deixa isso derrubar
        # a tela inteira, só mostra o tutorial de novo (pior caso: chato,
        # não quebrado)
        print("Erro ao consultar tutorial visto:", e)
        return False
    finally:
        conn.close()


def marcar_tutorial_visto(usuario_nome, tutorial):
    usuario = _get_usuario_by_name(usuario_nome)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO tutoriais_vistos (usuario, tutorial)
               VALUES (%s, %s)
               ON CONFLICT (usuario, tutorial) DO NOTHING""",
            (usuario, tutorial)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("Erro ao marcar tutorial visto:", e)
        return False
    finally:
        conn.close()
