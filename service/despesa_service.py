import sqlite3
import os
from datetime import datetime, timedelta
from .db_service import get_connection

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


    def deletar_despesa(self, id_gasto):
        conn = get_connection
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
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
            conjuge = resultado[0]


        cursor.execute("""
        SELECT categoria, despesa, valor, mes_ano , status, case when tipo_despesa = 'F' then 'FIXA' when tipo_despesa ='V' then 'Variavel' else 'Exceção' end, d.id
        , case when u.pronome = 'Ele/Dele' then 'H' else 'S' end pronome
        FROM despesas d
        inner join usuarios u on d.usuario = u.email 
        WHERE usuario in( %s, %s)
        and ( categoria = %s or %s ='Todas' )
        and ( mes_ano = %s )
        ORDER BY d.id DESC
         """, (usuario,conjuge,categoria,categoria,mes_ano))

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