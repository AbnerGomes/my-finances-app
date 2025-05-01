import sqlite3
import os
from datetime import datetime, timedelta
from .db_service import get_connection

class GastoService:

    def __init__(self):
        #self.db_path = db_path
        self._create_db()

    # def _conectar(self):
    #     return sqlite3.connect(self.db_path)

    def _create_db(self):
        print("ok")
        os.makedirs('instance', exist_ok=True)  # Garante que a pasta instance existe
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Gastos (
            id SERIAL PRIMARY KEY,
            Gasto TEXT NOT NULL,
            valor_gasto REAL NOT NULL,
            data DATE NOT NULL,
            categoria TEXT NOT NULL,
            usuario TEXT
            )
        ''')
        conn.commit()
        conn.close()


    #função para verificar se exitem dados para o donut
    def verifica_dados_bd(self,usuario):
        # Verificar se há dados no banco
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT categoria, SUM(valor_gasto) FROM Gastos where usuario = %s GROUP BY categoria',(usuario,))
        dados = c.fetchall()
        conn.close()

        # Se não houver dados, retorna uma lista com valores padrão
        if not dados:
            dados = [
                ('Alimentação', 0),
                ('Saúde', 0),
                ('Mobilidade', 0),
                ('Entretenimento', 0),
                ('Moradia',0),
                ('Outros',0),
                ('Dívidas',0),
                ('Educação',0)
            ]

        return dados

    # Função para salvar o gasto no banco
    def salvar_gasto(self,gasto, valor, data, categoria,usuario):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Gastos (Gasto, valor_gasto, data, categoria, usuario)
                VALUES (%s, %s, %s, %s, %s)
            ''', (gasto, valor, data, categoria,usuario))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False    


    def filtrarGastos(self,periodo,usuario,isCasal):
        try: 
            if periodo is None:
                periodo='mesatual'

            conn = get_connection()
            cursor = conn.cursor()

            hoje = datetime.now().date()
            inicio = fim = None

            if periodo == 'ontem':
                inicio = fim = hoje - timedelta(days=1)

            elif periodo == 'hoje':
                inicio = fim = hoje

            elif periodo == 'semanaatual':
                domingo_semana_atual = hoje - timedelta(days=hoje.weekday() + 1) if hoje.weekday() != 6 else hoje
                inicio = domingo_semana_atual
                fim = hoje

            elif periodo == 'semanapassada':
                # Domingo da semana passada (domingo anterior ao domingo da semana atual)
                domingo_semana_atual = hoje - timedelta(days=hoje.weekday() + 1) if hoje.weekday() != 6 else hoje
                domingo_passado = domingo_semana_atual - timedelta(days=7)
                sabado_passado = domingo_passado + timedelta(days=6)
                inicio = domingo_passado
                fim = sabado_passado

            elif periodo == 'mesatual':
                inicio = hoje.replace(day=1)
                fim = hoje

            elif periodo == 'mesanterior':
                primeiro_dia_mes_atual = hoje.replace(day=1)
                ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
                inicio = ultimo_dia_mes_anterior.replace(day=1)
                fim = ultimo_dia_mes_anterior
            
            conjuge =''

            #verifica se é casal e busca o conjuge
            if isCasal == 'S':
                query = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
                cursor.execute(query, (usuario,usuario))
                resultado = cursor.fetchone()
                conjuge = resultado[0]

            if inicio and fim:
                query = """
                    SELECT categoria, SUM(valor_gasto) valor
                    FROM Gastos
                    WHERE usuario IN (%s, %s) AND data BETWEEN %s AND %s
                    GROUP BY categoria
                """

                cursor.execute(query, (usuario,conjuge,inicio, fim))
            else:
                query = """
                    SELECT categoria, SUM(valor_gasto) valor
                    FROM Gastos
                    WHERE usuario IN (%s, %s)
                    GROUP BY categoria
                """
                cursor.execute(query, (usuario, conjuge))

            print(query)
            print(usuario)
            print(conjuge)
            print(inicio)
            print(fim)

            dados = cursor.fetchall()
            conn.close()

            return [{'categoria': row[0], 'valor': row[1]} for row in dados]
        except Exception as e:
            #aqui vem um tratamento para exibir uma mensagem quando nao houver dados para exibir naquele periodo
            return ""

    def extrato_gastos(self,usuario,data_inicial,data_fim,categoria,isCasal):
        conn = get_connection()
        cursor = conn.cursor()

        conjuge =''

        #verifica se é casal e busca o conjuge
        if isCasal == 'S':
            query = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            cursor.execute(query, (usuario,usuario))
            resultado = cursor.fetchone()
            conjuge = resultado[0]

        cursor.execute("""
        SELECT categoria, gasto, valor_gasto, TO_CHAR(data, 'DD/MM/YYYY') AS data_formatada , id
        FROM gastos
        WHERE usuario in( %s ,%s)
        and ( categoria = %s or %s ='Todas' )
        and ( data >= %s )
        and ( data <= %s )
        ORDER BY data DESC
         """, (usuario,conjuge,categoria,categoria,data_inicial,data_fim))

        resultados = cursor.fetchall()
        
        conn.close()
        return resultados

    # Função para checar login
    def validar_login(self, usuario, senha):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM AUTENTICACAO WHERE usuario=%s AND senha=%s AND ativo=1", (usuario, senha))
        resultado = cursor.fetchone()
        conn.close()

        return resultado is not None

    def valida_usuario_existente(self, usuario, senha):
        conn = get_connection()
        c = conn.cursor()
                
        # Verifica se o usuário já existe
        c.execute("SELECT * FROM AUTENTICACAO WHERE usuario = %s", (usuario,))
        
        dados = c.fetchone()
        if not dados:
            # Insere novo usuário
            c.execute("INSERT INTO AUTENTICACAO (usuario, senha, ativo) VALUES (%s, %s, 1)", (usuario, senha))
            conn.commit()
            conn.close()
        return dados   is not None  


    def get_categorias_disponiveis(self,usuario):
        conn = get_connection()
        c = conn.cursor()
                
        # Verifica se o usuário já existe
        c.execute("SELECT distinct categoria FROM gastos WHERE usuario = %s", (usuario,))
        
        dados = c.fetchone()

        return dados   is not None      


    def editar_gasto(self,gasto,categoria,valor,data,id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("update gastos set gasto= %s , categoria = %s, valor_gasto = %s, data = %s WHERE id = %s", (gasto,categoria,valor,data,id,) )
        conn.commit()
        conn.close()


    def deletar_gasto(self, id_gasto):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gastos WHERE id = %s", (id_gasto,))
        conn.commit()
        conn.close()
