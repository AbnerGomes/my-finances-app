import sqlite3
import os
from datetime import datetime, timedelta
from .db_service import get_connection

class AdminService:
    def deletar_usuario(self, id_usuario):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        conn.commit()
        conn.close()       

    def atualiza__plano_mensalista(self, usuario, tipo_plano):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("update mensalista  set tipo_plano = %s WHERE usuario = %s", (usuario, tipo_plano))
        conn.commit()
        conn.close()       

    def atualiza__status_mensalista(self, usuario, status):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("update mensalista  set status = %s WHERE usuario = %s", (usuario, status))
        conn.commit()
        conn.close()  

    def valida_mensalista(self,usuario,mes_ano):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("select status from mensalidade where usuario = %s and mes_ano = %s",(usuario,mes_ano))
        
        resultados = cursor.fetchall()
        
        conn.close()
        return resultados
    
    def cadastra_mensalista(usuario,mes_ano,status,tipo_plano):    
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mensalidade (usuario, mes_ano, status, ativo, tipo_plano) \
VALUES (%s, %s, %s, 'S', %s);",(usuario,mes_ano,status,tipo_plano))  
        conn.commit()
        conn.close()    