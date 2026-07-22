import sqlite3
import os
from datetime import datetime, timedelta
from .db_service import get_connection

class GastoService:

    def __init__(self):
        #self.db_path = db_path
        #self._create_db()
        pass

    # def _conectar(self):
    #     return sqlite3.connect(self.db_path)

    # def _create_db(self):
    #     print("ok")
        # os.makedirs('instance', exist_ok=True)  # Garante que a pasta instance existe
        # conn = get_connection()
        # cursor = conn.cursor()
        # cursor.execute('''
        #     CREATE TABLE IF NOT EXISTS Gastos (
        #     id SERIAL PRIMARY KEY,
        #     Gasto TEXT NOT NULL,
        #     valor_gasto REAL NOT NULL,
        #     data DATE NOT NULL,
        #     categoria TEXT NOT NULL,
        #     usuario TEXT
        #     )
        # ''')
        # conn.commit()
        # conn.close()

    def get_usuario_by_name(self,nome):
        conn = get_connection()
        c = conn.cursor()

        c.execute('SELECT usuario from AUTENTICACAO where nome = %s',(nome,))
        usuario = c.fetchall()
        conn.close()

        return usuario[0] if usuario else None 

    def get_id_usuario_by_name(self,nome):
        conn = get_connection()
        c = conn.cursor()

        c.execute('SELECT id from usuarios where nome = %s',(nome,))
        usuario = c.fetchall()
        conn.close()

        return usuario[0] if usuario else None 


    #função para verificar se exitem dados para o donut
    def verifica_dados_bd(self,usuario):

        usuario = self.get_usuario_by_name(usuario)
        
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
                ('Ifood', 0),
                ('Saúde', 0),
                ('Mobilidade', 0),
                ('Entretenimento', 0),
                ('Moradia', 0),
                ('Outros', 0),
                ('Dívidas', 0),
                ('Educação', 0),
                ('Pets', 0),
                ('Investimentos', 0)
            ]

        return dados

    # Função para salvar o gasto no banco
    def salvar_gasto(self,gasto, valor, data, categoria,usuario):
        try:
            usuario = self.get_usuario_by_name(usuario)

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



    def filtrarGastosMensais(self,usuario,isCasal): 

        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()

        hoje = datetime.now().date()
        ano_atual =  datetime(datetime.now().year, 1, 1)

        conjuge =''

        #verifica se é casal e busca o conjuge
        if isCasal == 'S':
            query = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            cursor.execute(query, (usuario,usuario))
            resultado = cursor.fetchone()
            if resultado:
                conjuge = resultado[0]

        query = """
            WITH meses AS (
                -- Gera uma série de meses desde janeiro até o mês atual
                SELECT to_char(data_serie, 'MON/YYYY') AS mes_ano,
                    date_trunc('month', data_serie) AS data_inicio
                FROM generate_series(
                    date_trunc('year', CURRENT_DATE),        -- Primeiro dia de janeiro do ano atual
                    date_trunc('month', CURRENT_DATE),       -- Mês atual
                    interval '1 month'
                ) AS data_serie
            ),
            gastos_agrupados AS (
                -- Soma os valores dos gastos por mês
                SELECT
                    to_char(data, 'MON/YYYY') AS mes_ano,
                    date_trunc('month', data) AS data_inicio,
                    SUM(valor_gasto) AS valor
                FROM Gastos
                WHERE usuario IN (%s, %s)
                AND data BETWEEN %s AND %s
                GROUP BY 1, 2
            )
            -- Junta a série de meses com os gastos
            SELECT
                m.mes_ano,
                COALESCE(g.valor, 0) AS valor  -- Caso não haja gasto, retorna 0
            FROM meses m
            LEFT JOIN gastos_agrupados g ON m.data_inicio = g.data_inicio
            ORDER BY m.data_inicio ASC;
        """
        cursor.execute(query, (usuario, conjuge,ano_atual,hoje))
    
        dados = cursor.fetchall()
        conn.close()

        return [{'mes_ano': row[0], 'valor': row[1]} for row in dados]

    def filtrarGastos(self,periodo,usuario,isCasal):
        try: 
            if periodo is None:
                periodo='mesatual'

            usuario = self.get_usuario_by_name(usuario)

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
                if resultado:
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

            dados = cursor.fetchall()
            conn.close()

            return [{'categoria': row[0], 'valor': row[1]} for row in dados]
        except Exception as e:
            #aqui vem um tratamento para exibir uma mensagem quando nao houver dados para exibir naquele periodo
            return ""

    def extrato_gastos(self,usuario,data_inicial,data_fim,categoria,isCasal):

        usuario = self.get_usuario_by_name(usuario)
        
        conn = get_connection()
        cursor = conn.cursor()

        conjuge =''

        #verifica se é casal e busca o conjuge
        if isCasal == 'S':
            query = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            cursor.execute(query, (usuario,usuario))
            resultado = cursor.fetchone()
            if resultado:
                conjuge = resultado[0]

        cursor.execute("""
        SELECT categoria, gasto, valor_gasto, TO_CHAR(data, 'DD/MM/YYYY') AS data_formatada , g.id, case when u.pronome = 'Ele/Dele' then 'H' else 'S' end pronome
        , case when g.usuario = %s then true else false end eh_proprio
        FROM gastos g
        inner join usuarios u on g.usuario = u.email
        WHERE g.usuario in( %s ,%s)
        and ( categoria = %s or %s ='Todas' )
        and ( data >= %s )
        and ( data <= %s )
        ORDER BY data DESC
         """, (usuario,usuario,conjuge,categoria,categoria,data_inicial,data_fim))

        resultados = cursor.fetchall()
        
        conn.close()
        return resultados

    # Função para checar login
    def validar_login(self, usuario, senha):

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM AUTENTICACAO WHERE usuario=%s AND senha=%s AND ativo=1", (usuario, senha))
        resultado = cursor.fetchone()
        dados = resultado[0] if resultado else None
        conn.close()

        return dados

    def cadastrar_usuario(self, nome, email, telefone, senha, pronome):
        # cadastro público (tela de login -> "Criar conta"). Cria a conta
        # em AUTENTICACAO (login) e em usuarios (email/nome/pronome, usado
        # em todo o resto do app pros JOINs e pro Modo Casal).
        email = email.strip().lower()

        conn = get_connection()
        c = conn.cursor()

        try:
            c.execute("SELECT 1 FROM AUTENTICACAO WHERE usuario = %s", (email,))
            if c.fetchone():
                conn.close()
                return False

            c.execute(
                "INSERT INTO AUTENTICACAO (usuario, senha, ativo, nome, telefone) VALUES (%s, %s, 1, %s, %s)",
                (email, senha, nome, telefone)
            )
            c.execute(
                "INSERT INTO usuarios (email, nome, pronome) VALUES (%s, %s, %s)",
                (email, nome, pronome)
            )

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def cadastrar_conjuge(self, usuario_atual, nome, email, telefone, senha, pronome):
        # session['usuario'] guarda o NOME (não o email/usuario de login — ver
        # validar_login), então precisamos converter antes de usar como
        # conjuge_1, já que casal.conjuge_1 referencia autenticacao.usuario (email).
        usuario_atual = self.get_usuario_by_name(usuario_atual)
        email = email.strip().lower()

        conn = get_connection()
        c = conn.cursor()

        try:
            # Verifica se já existe conta com esse email
            c.execute("SELECT 1 FROM AUTENTICACAO WHERE usuario = %s", (email,))
            if c.fetchone():
                conn.close()
                return False

            c.execute(
                "INSERT INTO AUTENTICACAO (usuario, senha, ativo, nome, telefone) VALUES (%s, %s, 1, %s, %s)",
                (email, senha, nome, telefone)
            )
            c.execute(
                "INSERT INTO usuarios (email, nome, pronome) VALUES (%s, %s, %s)",
                (email, nome, pronome)
            )
            c.execute(
                "INSERT INTO casal (conjuge_1, conjuge_2) VALUES (%s, %s)",
                (usuario_atual, email)
            )

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_categorias_disponiveis(self,usuario):

        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        c = conn.cursor()
                
        # Verifica se o usuário já existe
        c.execute("SELECT distinct categoria FROM gastos WHERE usuario = %s", (usuario,))
        
        dados = c.fetchall()   
        conn.close()

        # transforma [('Alimentação',), ('Saúde',)] em ['Alimentação', 'Saúde']
        return [row[0] for row in dados]     


    def editar_gasto(self,gasto,categoria,valor,data,id,usuario):
        # só permite editar um gasto que pertença ao próprio usuário logado
        # (senão, no modo casal, dava pra editar o gasto do cônjuge)
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "update gastos set gasto= %s , categoria = %s, valor_gasto = %s, data = %s WHERE id = %s AND usuario = %s",
            (gasto,categoria,valor,data,id,usuario)
        )
        conn.commit()
        sucesso = cursor.rowcount > 0
        conn.close()
        return sucesso


    def deletar_gasto(self, id_gasto, usuario):
        # mesma proteção: só deleta se o gasto for do próprio usuário
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gastos WHERE id = %s AND usuario = %s", (id_gasto, usuario))
        conn.commit()
        sucesso = cursor.rowcount > 0
        conn.close()
        return sucesso

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

    # ============================================================
    # Teste grátis de 7 dias + assinatura (usado no /index pra decidir
    # se mostra o modal de bloqueio levando pra tela de planos)
    # ============================================================
    def dias_de_conta(self, usuario):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT data_cadastro FROM autenticacao WHERE nome = %s", (usuario,))
        resultado = cursor.fetchone()
        conn.close()

        if not resultado or not resultado[0]:
            return 0

        return (datetime.now().date() - resultado[0]).days

    def tem_assinatura_ativa(self, usuario):
        # Por enquanto não existe pagamento de verdade integrado — qualquer
        # linha 'pago' já registrada na tabela mensalidade (em qualquer mês,
        # por email ou por nome — há registros antigos nos dois formatos)
        # conta como assinatura ativa "pra sempre", até o pagamento real
        # ser conectado.
        usuario_email = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM mensalidade WHERE status = 'pago' AND (usuario = %s OR usuario = %s) LIMIT 1",
            (usuario, usuario_email)
        )
        resultado = cursor.fetchone()
        conn.close()

        return resultado is not None

    def precisa_assinar(self, usuario):
        if self.dias_de_conta(usuario) <= 7:
            return False

        return not self.tem_assinatura_ativa(usuario)

    def get_receitas_mes(self,usuario, mes_ano,categorias):
        conn = get_connection()
        cursor = conn.cursor()        

        query = """SELECT  origem, sum(valor), mes_referencia 
        FROM receitas r inner join usuarios u on r.id_usuario = u.id 
        WHERE %s IN (u.nome )
        and mes_referencia = %s
        and (origem in (%s) or %s = 'Todas')
        group by origem, mes_referencia"""


        cursor.execute(query, (usuario,mes_ano,'Todas','Todas'))
        
        resultado = cursor.fetchall()
        conn.close()

        return  resultado

    def listar_receitas(self, usuario, mes_ano, isCasal='N'):
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()

        conjuge = ''

        #verifica se é casal e busca o conjuge
        if isCasal == 'S':
            query_conjuge = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            cursor.execute(query_conjuge, (usuario, usuario))
            resultado_conjuge = cursor.fetchone()
            if resultado_conjuge:
                conjuge = resultado_conjuge[0]

        query = """
        SELECT r.id, origem, valor, data_receita
        , case when u.pronome = 'Ele/Dele' then 'H' else 'S' end pronome
        , case when u.email = %s then true else false end eh_proprio
        FROM receitas r
        INNER JOIN usuarios u ON r.id_usuario = u.id
        WHERE u.email IN (%s, %s)
        AND DATE_TRUNC('month', data_receita) = DATE_TRUNC('month', %s::date)
        ORDER BY id DESC
        """

        cursor.execute(query, (usuario, usuario, conjuge, mes_ano))
        resultado = cursor.fetchall()
        conn.close()

        return resultado
        
    def salvar_receita(self, usuario, mes,origem,valor):

        try:
            id_usuario = self.get_id_usuario_by_name(usuario)

            conn = get_connection()
            c = conn.cursor()
                    
            # Insere nova receita
            c.execute("INSERT INTO RECEITAS (id_usuario, data_receita, origem, valor) VALUES (%s, %s, %s, %s)", (id_usuario, mes,origem,valor))
            conn.commit()
            conn.close()

            return True
        except Exception as e:
            return False         

    def deletar_receita(self, usuario, id_receita):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            query = """
            DELETE FROM receitas
            WHERE id = %s
            AND id_usuario = (
                SELECT id FROM usuarios WHERE nome = %s
            )
            """

            cursor.execute(query, (id_receita, usuario))
            conn.commit()

            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            print("Erro ao deletar receita:", e)
            return False

        finally:
            conn.close()

    def editar_receita(self, usuario, id_receita, origem, valor, data_receita):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            query = """
            UPDATE receitas
            SET origem = %s,
                valor = %s,
                data_receita = %s
            WHERE id = %s
            AND id_usuario = (
                SELECT id FROM usuarios WHERE nome = %s
            )
            """

            cursor.execute(query, (origem, valor, data_receita, id_receita, usuario))
            conn.commit()

            return True

        except Exception as e:
            conn.rollback()
            print("Erro ao editar receita:", e)
            return False

        finally:
            conn.close()

    def get_total_receitas_mes(self, usuario, periodo, isCasal='N'):

        usuario = self.get_usuario_by_name(usuario)

        if periodo is None:
                periodo='mesatual'

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

        conn = get_connection()
        cursor = conn.cursor()

        conjuge = ''

        #verifica se é casal e busca o conjuge
        if isCasal == 'S':
            query_conjuge = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            cursor.execute(query_conjuge, (usuario, usuario))
            resultado_conjuge = cursor.fetchone()
            if resultado_conjuge:
                conjuge = resultado_conjuge[0]

        query = """
            SELECT SUM(r.valor)
            FROM receitas r
            INNER JOIN usuarios u ON r.id_usuario = u.id
            WHERE u.email IN (%s, %s) and r.data_receita >= %s and r.data_receita <= %s
        """
        cursor.execute(query, (usuario, conjuge, inicio, fim))
        total = cursor.fetchone()[0]

        conn.close()
        return total

    def get_total_gastos_mes(self, usuario, periodo, isCasal='N'):

        usuario = self.get_usuario_by_name(usuario)

        if periodo is None:
                periodo='mesatual'

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

        conn = get_connection()
        cursor = conn.cursor()

        conjuge = ''

        #verifica se é casal e busca o conjuge
        if isCasal == 'S':
            query_conjuge = "SELECT a.usuario AS conjuge FROM casal c JOIN autenticacao a ON a.usuario = CASE WHEN c.conjuge_1 = %s THEN c.conjuge_2 ELSE c.conjuge_1 END WHERE %s IN (c.conjuge_1, c.conjuge_2);"
            cursor.execute(query_conjuge, (usuario, usuario))
            resultado_conjuge = cursor.fetchone()
            if resultado_conjuge:
                conjuge = resultado_conjuge[0]

        query = """
            SELECT SUM(valor_gasto)
            FROM gastos
            WHERE usuario IN (%s, %s) AND data BETWEEN %s AND %s
        """
        cursor.execute(query, (usuario, conjuge, inicio, fim))
        total = cursor.fetchone()[0]

        conn.close()
        return total

    def buscar_acoes_rapidas(self, usuario):
        usuario = self.get_usuario_by_name(usuario)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT gasto,
            valor,
            categoria,
            qtd
        FROM (
            SELECT g.gasto,
                g.valor_gasto AS valor,
                g.categoria,
                COUNT(*) AS qtd,
                ROW_NUMBER() OVER (
                    PARTITION BY g.gasto
                    ORDER BY COUNT(*) DESC
                ) AS rn
            FROM gastos g
            WHERE usuario = %s
            GROUP BY g.gasto, g.valor_gasto, g.categoria
        ) t
        WHERE rn = 1
        ORDER BY qtd DESC
        LIMIT 5;
        """, (usuario,))

        resultados = cursor.fetchall()
        conn.close()

        return resultados    