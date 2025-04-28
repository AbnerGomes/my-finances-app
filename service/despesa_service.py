import sqlite3
import os
from datetime import datetime, timedelta
from .db_service import get_connection

class DespesaService:

    #def __init__(self):
        #self.db_path = db_path
        #self._create_db()

    # Função para salvar o gasto no banco
    def salvar_despesa(self,despesa, valor, data, categoria,usuario,tipo_despesa):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Despesas (despesa, valor, mes_ano, categoria, usuario,tipo_despesa)
            VALUES (%s, %s, %s, %s, %s,%s)
        ''', (despesa, valor, data, categoria,usuario,tipo_despesa))
        conn.commit()
        conn.close()


    # Função para checar login
    # def validar_login(self, usuario, senha):
    #     conn = get_connection()
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT * FROM AUTENTICACAO WHERE usuario=%s AND senha=%s AND ativo=1", (usuario, senha))
    #     resultado = cursor.fetchone()
    #     conn.close()

    #     return resultado is not None


    def deletar_despesa(self, id_gasto):
        conn = get_connection
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
        conn.commit()
        conn.close()


    def busca_despesas(self,usuario,mes_ano,categoria):
        conn = get_connection()
        cursor = conn.cursor()
        print('despesa')
        print(mes_ano)
        cursor.execute("""
        SELECT categoria, despesa, valor, mes_ano , status, case when tipo_despesa = 'F' then 'FIXA' when tipo_despesa ='V' then 'Variavel' else 'Exceção' end, id
        FROM despesas
        WHERE usuario = %s
        and ( categoria = %s or %s ='Todas' )
        and ( mes_ano = %s )
        ORDER BY id DESC
         """, (usuario,categoria,categoria,mes_ano))

        resultados = cursor.fetchall()
        
        conn.close()
        return resultados    


    def atualizar_status(self, id_despesa, novo_status):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE despesas SET status = %s WHERE id = %s", (novo_status, id_despesa)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar status: {e}")
            return False


    def editar_despesa(self,despesa,categoria,valor,id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("update despesas set despesa= %s , categoria = %s, valor = %s WHERE id = %s", (despesa,categoria,valor,id,) )
        conn.commit()
        conn.close()

    def deletar_despesa(self, id_despesa):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM despesas WHERE id = %s", (id_despesa,))
        conn.commit()
        conn.close()        