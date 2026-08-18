import sqlite3
import os
from datetime import datetime, timedelta
from .db_service import get_connection
from .categorias import combinar_categorias

class DespesaService:

    #def __init__(self):
        #self.db_path = db_path
        #self._create_db()

    def get_usuario_by_name(self,nome):
        conn = get_connection()
        c = conn.cursor()

        c.execute('SELECT usuario from AUTENTICACAO where nome = %s',(nome,))
        usuario = c.fetchall()
        conn.close()

        return usuario[0] if usuario else None 


    # Função para salvar o gasto no banco
    def salvar_despesa(self,despesa, valor, data, categoria,usuario,tipo_despesa):

        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Despesas (despesa, valor, mes_ano, categoria, usuario,tipo_despesa)
            VALUES (%s, %s, %s, %s, %s,%s)
        ''', (despesa, valor, data, categoria,usuario,tipo_despesa))
        conn.commit()
        conn.close()

    def salvar_despesa_replicada(self, despesa, valor, mes_ano_inicial, categoria, usuario, tipo_despesa):
        # despesa Fixa com "replicar pro resto do ano" marcado: cria uma
        # linha pro mês selecionado e mais uma pra cada mês seguinte até
        # dezembro daquele ano, pra não precisar cadastrar mês a mês.
        usuario = self.get_usuario_by_name(usuario)

        ano_str, mes_str = mes_ano_inicial.split('-')
        ano = int(ano_str)
        mes_inicial = int(mes_str)

        conn = get_connection()
        cursor = conn.cursor()

        for mes in range(mes_inicial, 13):
            mes_ano = f"{ano}-{mes:02d}"
            cursor.execute('''
                INSERT INTO Despesas (despesa, valor, mes_ano, categoria, usuario, tipo_despesa)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (despesa, valor, mes_ano, categoria, usuario, tipo_despesa))

        conn.commit()
        conn.close()


    def busca_despesas(self,usuario,mes_ano,categoria,isCasal):
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()

        conjuge=''

        #verifica se é casal e busca o conjuge
        if isCasal == 'S':
            query = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            cursor.execute(query, (usuario,usuario))
            resultado = cursor.fetchone()
            if resultado:
                conjuge = resultado[0]


        cursor.execute("""
        SELECT categoria, despesa, valor, mes_ano , status, case when tipo_despesa = 'F' then 'FIXA' when tipo_despesa ='V' then 'Variavel' else 'Exceção' end, d.id
        , case when u.pronome = 'Ele/Dele' then 'H' else 'S' end pronome
        ,data_pagamento
        , case when d.usuario = %s then true else false end eh_proprio
        FROM despesas d
        inner join usuarios u on d.usuario = u.email
        WHERE usuario in( %s, %s)
        and ( categoria = %s or %s ='Todas' )
        and ( mes_ano = %s )
        ORDER BY d.id DESC
         """, (usuario,usuario,conjuge,categoria,categoria,mes_ano))

        resultados = cursor.fetchall()
        
        conn.close()
        return resultados    


    def atualizar_status(self, id_despesa, novo_status, usuario):
        # só permite alterar o status de uma despesa que pertença ao
        # próprio usuário logado (senão, no modo casal, dava pra alterar
        # a do cônjuge)
        usuario = self.get_usuario_by_name(usuario)

        # NÃO lança mais gasto automaticamente ao marcar como Pago — isso
        # duplicava quando o usuário já tinha lançado o gasto na mão (ver
        # criar_gasto_da_despesa, que só roda se o usuário CONFIRMAR que
        # quer o gasto, perguntado pelo front depois dessa chamada)
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT status, despesa FROM despesas WHERE id = %s AND usuario = %s",
                (id_despesa, usuario)
            )
            atual = cursor.fetchone()
            if not atual:
                return {'sucesso': False}

            status_anterior, despesa_nome = atual

            if status_anterior == novo_status:
                # nada realmente mudou — evita reprocessar (e evita
                # perguntar de novo se quer lançar gasto toda vez que o
                # dropdown dispara "change" pro mesmo valor já salvo)
                return {'sucesso': True, 'virouPago': False}

            if novo_status == "Pago":
                cursor.execute(
                    "UPDATE despesas SET status = %s, data_pagamento = CURRENT_DATE WHERE id = %s AND usuario = %s",
                    (novo_status, id_despesa, usuario)
                )
            else:
                cursor.execute(
                    "UPDATE despesas SET status = %s, data_pagamento = NULL WHERE id = %s AND usuario = %s",
                    (novo_status, id_despesa, usuario)
                )

            sucesso = cursor.rowcount > 0
            conn.commit()

            virou_pago = sucesso and novo_status == "Pago"

            return {
                'sucesso': sucesso,
                'virouPago': virou_pago,
                'despesa': despesa_nome if virou_pago else None,
            }
        except Exception as e:
            conn.rollback()
            print(f"Erro ao atualizar status: {e}")
            return {'sucesso': False}
        finally:
            conn.close()

    def criar_gasto_da_despesa(self, id_despesa, usuario):
        """Lança um gasto correspondente a uma despesa já paga — só roda
        quando o usuário CONFIRMA (pergunta feita no front depois de
        marcar a despesa como Pago), pra não duplicar quando ele já
        tinha lançado o gasto na mão antes."""
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT despesa, valor, categoria, data_pagamento FROM despesas
                   WHERE id = %s AND usuario = %s AND status = 'Pago'""",
                (id_despesa, usuario)
            )
            resultado = cursor.fetchone()
            if not resultado:
                return False

            despesa_nome, valor, categoria, data_pagamento = resultado
            cursor.execute(
                """INSERT INTO gastos (gasto, valor_gasto, data, categoria, usuario)
                   VALUES (%s, %s, %s, %s, %s)""",
                (despesa_nome, valor, data_pagamento or datetime.now().date(), categoria, usuario)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Erro ao criar gasto da despesa: {e}")
            return False
        finally:
            conn.close()


    def editar_despesa(self,despesa,categoria,valor,id,usuario):
        # só permite editar uma despesa que pertença ao próprio usuário
        # logado (senão, no modo casal, dava pra editar a do cônjuge)
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "update despesas set despesa= %s , categoria = %s, valor = %s WHERE id = %s AND usuario = %s",
            (despesa,categoria,valor,id,usuario)
        )
        conn.commit()
        sucesso = cursor.rowcount > 0
        conn.close()
        return sucesso

    def deletar_despesa(self, id_despesa, usuario):
        # só permite excluir uma despesa que pertença ao próprio usuário
        # logado (senão, no modo casal, dava pra excluir a do cônjuge)
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM despesas WHERE id = %s AND usuario = %s", (id_despesa, usuario))
        conn.commit()
        sucesso = cursor.rowcount > 0
        conn.close()
        return sucesso

    def replicar_despesa_mes_seguinte(self, id_despesa, usuario):
        # copia uma despesa existente pro mês seguinte, sempre como
        # Pendente (mesmo que a original já esteja Paga) — pra não
        # precisar digitar de novo uma despesa fixa/recorrente todo mês.
        # Não passa status/data_pagamento no INSERT de propósito: cai no
        # default da tabela (Pendente/sem data), igual toda despesa nova.
        usuario_email = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT despesa, valor, categoria, tipo_despesa, mes_ano FROM despesas WHERE id = %s AND usuario = %s",
            (id_despesa, usuario_email)
        )
        original = cursor.fetchone()

        if not original:
            conn.close()
            return False

        despesa, valor, categoria, tipo_despesa, mes_ano = original
        ano_str, mes_str = mes_ano.split('-')[:2]
        ano, mes = int(ano_str), int(mes_str)

        if mes == 12:
            ano += 1
            mes = 1
        else:
            mes += 1

        mes_ano_seguinte = f"{ano}-{mes:02d}"

        cursor.execute('''
            INSERT INTO Despesas (despesa, valor, mes_ano, categoria, usuario, tipo_despesa)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (despesa, valor, mes_ano_seguinte, categoria, usuario_email, tipo_despesa))

        conn.commit()
        conn.close()
        return True

    def get_categorias_disponiveis(self, usuario, isCasal='N'):
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        c = conn.cursor()

        conjuge = ''

        # no modo Casal, o filtro tem que incluir categorias que só o
        # cônjuge usou — senão o filtro de categoria fica incompleto pra
        # quem tá vendo as despesas combinadas dos dois
        if isCasal == 'S':
            query = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            c.execute(query, (usuario, usuario))
            resultado = c.fetchone()
            if resultado:
                conjuge = resultado[0]

        c.execute("SELECT distinct categoria FROM despesas WHERE usuario IN (%s, %s) ORDER BY categoria", (usuario, conjuge))
        dados = c.fetchall()
        conn.close()

        return [row[0] for row in dados]

    def get_categorias_completas(self, usuario, isCasal='N'):
        """Categorias padrão + as que o usuário (e o cônjuge, no modo
        Casal) já usaram (inclui categorias próprias/customizadas que
        alguém criou digitando um nome novo)."""
        return combinar_categorias(self.get_categorias_disponiveis(usuario, isCasal))

    def tem_conjuge(self,usuario):

        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()

        #verifica se existe conjuge
        query = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
        cursor.execute(query, (usuario,usuario))
        resultado = cursor.fetchone()
        conn.close()  # faltava — essa conexão nunca era devolvida (chamada em quase toda página)

        if resultado is None:
            return False
        else:
            return True

    def tem_pendencias_mes_anterior(self, usuario, isCasal):
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()

        conjuge = None

        if isCasal == 'S':
            query = """
            SELECT a.usuario AS conjuge 
            FROM casal c 
            JOIN autenticacao a 
            ON a.usuario = CASE 
                WHEN c.conjuge_1 = %s THEN c.conjuge_2 
                ELSE c.conjuge_1 
            END 
            WHERE %s IN (c.conjuge_1, c.conjuge_2)
            """
            cursor.execute(query, (usuario, usuario))
            resultado = cursor.fetchone()
            if resultado:
                conjuge = resultado[0]

        # mês atual
        hoje = datetime.today()
        mes_atual = hoje.strftime('%Y-%m')

        cursor.execute("""
            SELECT COUNT(1)
            FROM despesas
            WHERE usuario IN (%s, %s)
            AND status != 'Pago'
            AND mes_ano < %s
        """, (usuario, conjuge, mes_atual))

        total = cursor.fetchone()[0]

        conn.close()

        return total #> 0

    def resumo_mes_atual(self, usuario, isCasal):
        """Resumo das despesas do MÊS ATUAL (pagas/pendentes/parciais e os
        valores) — usado no card novo da home. Mesmo padrão de busca de
        cônjuge de tem_pendencias_mes_anterior, só que olhando o mês
        atual (aquele método olha só meses ANTERIORES, de propósito)."""
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        try:
            cursor = conn.cursor()

            conjuge = ''
            if isCasal == 'S':
                query_conjuge = """
                SELECT a.usuario AS conjuge
                FROM casal c
                JOIN autenticacao a
                ON a.usuario = CASE
                    WHEN c.conjuge_1 = %s THEN c.conjuge_2
                    ELSE c.conjuge_1
                END
                WHERE %s IN (c.conjuge_1, c.conjuge_2)
                """
                cursor.execute(query_conjuge, (usuario, usuario))
                resultado = cursor.fetchone()
                if resultado:
                    conjuge = resultado[0]

            mes_atual = datetime.today().strftime('%Y-%m')

            cursor.execute("""
                SELECT status, COUNT(1), COALESCE(SUM(valor), 0)
                FROM despesas
                WHERE usuario IN (%s, %s) AND mes_ano = %s
                GROUP BY status
            """, (usuario, conjuge, mes_atual))

            por_status = {status: (qtd, float(valor)) for status, qtd, valor in cursor.fetchall()}

            pagas_qtd, valor_pago = por_status.get('Pago', (0, 0.0))
            pendentes_qtd, valor_pendente_puro = por_status.get('Pendente', (0, 0.0))
            parciais_qtd, valor_parcial = por_status.get('Parcial', (0, 0.0))

            total_qtd = pagas_qtd + pendentes_qtd + parciais_qtd

            return {
                'total': total_qtd,
                'pagas': pagas_qtd,
                'pendentes': pendentes_qtd,
                'parciais': parciais_qtd,
                'valor_pago': round(valor_pago, 2),
                # "pendente" pro usuário = tudo que ainda falta pagar,
                # incluindo o que já foi pago parcialmente
                'valor_pendente': round(valor_pendente_puro + valor_parcial, 2),
            }
        except Exception as e:
            print("Erro em resumo_mes_atual:", e)
            return {'total': 0, 'pagas': 0, 'pendentes': 0, 'parciais': 0, 'valor_pago': 0, 'valor_pendente': 0}
        finally:
            conn.close()

    def despesas_pendentes_mes_atual(self, usuario, isCasal, limite=3):
        """Lista (não só conta) as despesas pendentes/parciais do mês
        atual — usada no widget expansível da home, pra mostrar direto
        quais faltam pagar, sem precisar ir até a tela de despesas. Maior
        valor primeiro (mais impactante no orçamento primeiro)."""
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        try:
            cursor = conn.cursor()

            conjuge = ''
            if isCasal == 'S':
                query_conjuge = """
                SELECT a.usuario AS conjuge
                FROM casal c
                JOIN autenticacao a
                ON a.usuario = CASE
                    WHEN c.conjuge_1 = %s THEN c.conjuge_2
                    ELSE c.conjuge_1
                END
                WHERE %s IN (c.conjuge_1, c.conjuge_2)
                """
                cursor.execute(query_conjuge, (usuario, usuario))
                resultado = cursor.fetchone()
                if resultado:
                    conjuge = resultado[0]

            mes_atual = datetime.today().strftime('%Y-%m')

            cursor.execute("""
                SELECT despesa, valor, status
                FROM despesas
                WHERE usuario IN (%s, %s) AND mes_ano = %s AND status != 'Pago'
                ORDER BY valor DESC
                LIMIT %s
            """, (usuario, conjuge, mes_atual, limite))

            return [
                {'despesa': despesa, 'valor': round(float(valor), 2), 'status': status}
                for despesa, valor, status in cursor.fetchall()
            ]
        except Exception as e:
            print("Erro em despesas_pendentes_mes_atual:", e)
            return []
        finally:
            conn.close()

    def buscar_despesa_correspondente(self, usuario, nome_gasto, valor, data_gasto):
        # quando o usuário cadastra um gasto avulso cujo nome e valor batem
        # com uma despesa do mesmo mês ainda não paga, é bem provável que
        # seja o pagamento daquela despesa — só ACHA (não altera nada),
        # quem decide marcar como paga é o usuário, confirmando um aviso
        # no front (evita duplicidade de quando ele já tinha marcado a
        # despesa como paga por conta própria, ver criar_gasto_da_despesa)
        usuario = self.get_usuario_by_name(usuario)
        mes_ano = data_gasto[:7]  # 'YYYY-MM' a partir de 'YYYY-MM-DD'

        try:
            valor_float = float(valor)
        except (TypeError, ValueError):
            return None

        conn = get_connection()
        cursor = conn.cursor()
        # valor é "real" (float de precisão simples) no banco — 123.45
        # vira 123.44999694824219 de verdade, então "valor = %s" direto
        # falha silenciosamente pra boa parte dos centavos. Arredondar os
        # dois lados pra 2 casas antes de comparar contorna isso (o fix
        # de verdade seria migrar a coluna pra numeric(10,2), mas isso é
        # uma migração maior, fora do escopo daqui)
        cursor.execute(
            """SELECT id, despesa FROM despesas
               WHERE usuario = %s
               AND mes_ano = %s
               AND status != 'Pago'
               AND lower(despesa) = lower(%s)
               AND ROUND(valor::numeric, 2) = ROUND(%s::numeric, 2)
               LIMIT 1""",
            (usuario, mes_ano, nome_gasto, valor_float)
        )
        resultado = cursor.fetchone()
        conn.close()

        if not resultado:
            return None

        return {'id': resultado[0], 'despesa': resultado[1]}

    def marcar_despesa_paga_por_id(self, id_despesa, usuario):
        # marca uma despesa como paga SEM lançar gasto nenhum — usado
        # quando o usuário confirma (depois de cadastrar um gasto com o
        # mesmo nome/valor) que quer marcar a despesa correspondente
        # como paga; o gasto que gerou essa pergunta já existe, então
        # não duplica lançando outro
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE despesas SET status = 'Pago', data_pagamento = CURRENT_DATE
               WHERE id = %s AND usuario = %s AND status != 'Pago'""",
            (id_despesa, usuario)
        )
        sucesso = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return sucesso

