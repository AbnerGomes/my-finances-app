from .db_service import get_connection


class WhatsappService:
    """Vincula um número de WhatsApp a uma conta já existente do app, pra
    o bot (routes whatsapp_bp + claude_agent_service) saber de quem são
    os dados quando uma mensagem chega."""

    @staticmethod
    def _normalizar(telefone):
        # guarda só dígitos (DDI+DDD+número), sem '+', espaços ou traços —
        # mesmo formato que a Meta manda no campo "from" do webhook.
        # A Meta SEMPRE manda com o código do país (55) na frente; se o
        # usuário digitou só DDD+número (10 ou 11 dígitos) na tela de
        # Configurações, sem o "55", o número nunca bateria com o que
        # chega no webhook — então completa automaticamente aqui.
        digitos = ''.join(ch for ch in telefone if ch.isdigit())
        if len(digitos) in (10, 11) and not digitos.startswith('55'):
            digitos = '55' + digitos
        return digitos

    @staticmethod
    def _variantes(telefone):
        """Celular BR pode aparecer com ou sem o '9' extra (norma pós-2012)
        dependendo de quem manda o número — o WAHA/GOWS, por exemplo, pode
        reportar o remetente sem o 9 mesmo quando o usuário cadastrou com
        o 9 (ou vice-versa). Gera as duas formas possíveis pra busca não
        depender de qual delas foi usada."""
        base = WhatsappService._normalizar(telefone)
        variantes = {base}
        # 55 + DDD(2) + número: com 9 = 13 dígitos, sem 9 = 12 dígitos
        if len(base) == 13 and base[4] == '9':
            variantes.add(base[:4] + base[5:])
        elif len(base) == 12:
            variantes.add(base[:4] + '9' + base[4:])
        return list(variantes)

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
        variantes = self._variantes(telefone)

        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT usuario FROM whatsapp_usuarios WHERE telefone = ANY(%s)", (variantes,))
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
