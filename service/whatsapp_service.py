from .db_service import get_connection


class WhatsappService:
    """Vincula um número de WhatsApp a uma conta já existente do app, pra
    o bot (routes whatsapp_bp + claude_agent_service) saber de quem são
    os dados quando uma mensagem chega."""

    @staticmethod
    def _normalizar(telefone):
        # guarda só dígitos (DDI+DDD+número), sem '+', espaços ou traços —
        # mesmo formato que a Meta manda no campo "from" do webhook
        return ''.join(ch for ch in telefone if ch.isdigit())

    def vincular_telefone(self, telefone, usuario_nome):
        telefone = self._normalizar(telefone)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO whatsapp_usuarios (telefone, usuario)
            VALUES (%s, %s)
            ON CONFLICT (telefone) DO UPDATE SET usuario = EXCLUDED.usuario
        """, (telefone, usuario_nome))
        conn.commit()
        conn.close()

    def desvincular_telefone(self, usuario_nome):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM whatsapp_usuarios WHERE usuario = %s", (usuario_nome,))
        conn.commit()
        conn.close()

    def get_usuario_por_telefone(self, telefone):
        telefone = self._normalizar(telefone)

        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT usuario FROM whatsapp_usuarios WHERE telefone = %s", (telefone,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
        except Exception as e:
            # tabela ainda não criada (ver WHATSAPP_SETUP.md) — não deixa a
            # ausência do recurso de WhatsApp derrubar quem está chamando
            conn.rollback()
            print("whatsapp_usuarios indisponível:", e)
            return None
        finally:
            conn.close()

    def get_telefone_vinculado(self, usuario_nome):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT telefone FROM whatsapp_usuarios WHERE usuario = %s", (usuario_nome,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
        except Exception as e:
            conn.rollback()
            print("whatsapp_usuarios indisponível:", e)
            return None
        finally:
            conn.close()
