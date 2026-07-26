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

        try:
            conn = get_connection()
            cursor = conn.cursor()

            if novo_status == "Pago":
                # marcar como paga também lança um gasto correspondente
                # (mesma categoria/valor), pra já entrar no extrato do mês
                cursor.execute(
                    """UPDATE despesas SET status = %s, data_pagamento = CURRENT_DATE
                       WHERE id = %s AND usuario = %s
                       RETURNING despesa, valor, categoria""",
                    (novo_status, id_despesa, usuario)
                )
                resultado = cursor.fetchone()
                sucesso = resultado is not None

                if sucesso:
                    despesa_nome, valor, categoria = resultado
                    cursor.execute(
                        """INSERT INTO gastos (gasto, valor_gasto, data, categoria, usuario)
                           VALUES (%s, %s, CURRENT_DATE, %s, %s)""",
                        (despesa_nome, valor, categoria, usuario)
                    )
            else:
                cursor.execute(
                    "UPDATE despesas SET status = %s, data_pagamento = NULL WHERE id = %s AND usuario = %s",
                    (novo_status, id_despesa, usuario)
                )
                sucesso = cursor.rowcount > 0

            conn.commit()
            return sucesso
        except Exception as e:
            conn.rollback()
            print(f"Erro ao atualizar status: {e}")
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

        c.execute("SELECT distinct categoria FROM despesas WHERE usuario IN (%s, %s)", (usuario, conjuge))
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

    def marcar_pago_se_corresponder(self, usuario, nome_gasto, valor, data_gasto):
        # quando o usuário cadastra um gasto avulso cujo nome e valor batem
        # com uma despesa do mesmo mês, entende que é o pagamento daquela
        # despesa e marca ela como Paga automaticamente
        usuario = self.get_usuario_by_name(usuario)
        mes_ano = data_gasto[:7]  # 'YYYY-MM' a partir de 'YYYY-MM-DD'

        try:
            valor_float = float(valor)
        except (TypeError, ValueError):
            return False

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE despesas
               SET status = 'Pago', data_pagamento = %s
               WHERE usuario = %s
               AND mes_ano = %s
               AND status != 'Pago'
               AND lower(despesa) = lower(%s)
               AND valor = %s""",
            (data_gasto, usuario, mes_ano, nome_gasto, valor_float)
        )
        sucesso = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return sucesso

