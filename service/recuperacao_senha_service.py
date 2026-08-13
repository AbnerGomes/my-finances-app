import random
from datetime import datetime, timedelta

from .db_service import get_connection

VALIDADE_MINUTOS = 15


def email_existe(email):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM autenticacao WHERE usuario = %s", (email,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def gerar_codigo(email):
    """Gera um código numérico de 6 dígitos e grava no banco associado
    ao e-mail. Não invalida códigos anteriores — verificar_codigo só
    aceita o mais recente ainda válido/não usado, então pedir um código
    novo automaticamente "aposenta" o anterior na prática."""
    codigo = f"{random.randint(0, 999999):06d}"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO codigos_recuperacao_senha (usuario, codigo) VALUES (%s, %s)",
            (email, codigo)
        )
        conn.commit()
        return codigo
    finally:
        conn.close()


def verificar_codigo(email, codigo):
    """Devolve o id do código se for válido (não usado, dentro da
    validade, e o mais recente pedido pra esse e-mail) — None caso
    contrário."""
    if not email or not codigo:
        return None

    cutoff = datetime.now() - timedelta(minutes=VALIDADE_MINUTOS)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id FROM codigos_recuperacao_senha
               WHERE usuario = %s AND codigo = %s AND usado = FALSE AND criado_em >= %s
               ORDER BY id DESC LIMIT 1""",
            (email, codigo, cutoff)
        )
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
    finally:
        conn.close()


def marcar_codigo_usado(id_codigo):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE codigos_recuperacao_senha SET usado = TRUE WHERE id = %s", (id_codigo,))
        conn.commit()
    finally:
        conn.close()


def redefinir_senha(email, nova_senha):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE autenticacao SET senha = %s WHERE usuario = %s", (nova_senha, email))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
