from supabase import create_client, Client
import json
from config import Config
from models.models import Usuario, Projeto, Chat, TipoIA, ArquivoChat, TipoUsuario
import bcrypt
from utils.advanced_logger import logger, log_database_operation
from utils.helpers import validate_bp, format_bp
from datetime import datetime
class SupabaseDAO:
    # Data Access Object para Supabase
    
    def __init__(self): 
        logger.info("🗄️ Inicializando SupabaseDAO...") # Log de inicialização
        try:
            #cria o cliente supabase usando a api key e a url do banco de dados
            self.supabase: Client = create_client(
                Config.SUPABASE_URL, 
                Config.SUPABASE_KEY
            )
            logger.info(f"✅ Conectado ao Supabase: {Config.SUPABASE_URL}") # Log de conexão
        except Exception as e:
            logger.critical(f"💥 ERRO ao conectar ao Supabase: {e}") # Log de erro
            raise 
    
    def criar_usuario(self, nome_completo, email, senha, tipo_usuario_id, numero_inscricao=None):
        """Cria um novo usuário"""
        logger.info(f"👤 Criando usuário: {email} (Tipo: {tipo_usuario_id})")
        
        # Valida BP se for participante ou orientador
        if tipo_usuario_id in [2, 3]:  # Participante ou Orientador
            if not numero_inscricao:
                raise ValueError("BP é obrigatório para participantes e orientadores")
            
            if not validate_bp(numero_inscricao):
                raise ValueError("BP inválido. Formato correto: BP12345678X")
            
            numero_inscricao = format_bp(numero_inscricao)
        
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # senha.encode('utf-8'): Converte a string da senha para bytes.
        # bcrypt.gensalt(): Gera um salt aleatório para a senha, isso basicamente adicione caracteres extras ao hash e garente que o hash da senha seja unico
        # bcrypt.hashpw(): Gera o hash da senha, hash é basicamente uma forma de cripitografar dados
        data = {
            'nome_completo': nome_completo,
            'email': email,
            'senha_hash': senha_hash,
            'tipo_usuario_id': tipo_usuario_id,
            'numero_inscricao': numero_inscricao
        }
        
        try:
            result = self.supabase.table('usuarios').insert(data).execute() #Envia o comando para o Supabase inserir (insert) os dados (data) na tabela, e ai os executa com execute()
            log_database_operation('INSERT', 'usuarios', data={'email': email}, result='Success') # Log de operação bem sussedida
            logger.info(f"✅ Usuário criado com sucesso: {email}") # Log de operação bem sussedida mostrada no terminal
            return self._row_to_usuario(result.data[0]) if result.data else None
        except Exception as e: # basicamente um if error
            log_database_operation('INSERT', 'usuarios', data={'email': email}, result=f'Error: {e}') # Log de operação mal sussedida
            logger.error(f"❌ Erro ao criar usuário: {e}") # Log de operação mal sussedida mostrada no terminal
            raise # vai lançar uma exeção e avisar o backend que deu erro, sem ele retornaria none e daria erro de tipo (eu acho, na boa isso foi tutorial do youtube em ingles)

    def buscar_usuario_por_id(self, usuario_id):
        """Busca usuário por ID"""
        logger.debug(f"🔍 Buscando usuário ID: {usuario_id}")
        result = self.supabase.table('usuarios').select('*').eq('id', usuario_id).execute() # equivale a SELECT * FROM usuarios WHERE id = usuario_id
        log_database_operation('SELECT', 'usuarios', data={'id': usuario_id}, result='Found' if result.data else 'Not Found') # Log de operação bem sussedida
        return self._row_to_usuario(result.data[0]) if result.data else None
    
    def buscar_usuario_por_email(self, email):
        """Busca usuário por email"""
        result = self.supabase.table('usuarios').select('*').eq('email', email).execute() # equivale a SELECT * FROM usuarios WHERE email = email
        return self._row_to_usuario(result.data[0]) if result.data else None
    
    def buscar_usuario_por_bp(self, numero_inscricao):
        """Busca usuário por número de inscrição (BP)"""
        
        numero_inscricao = format_bp(numero_inscricao)
        result = self.supabase.table('usuarios').select('*').eq('numero_inscricao', numero_inscricao).execute()
        return self._row_to_usuario(result.data[0]) if result.data else None
    
    def listar_usuarios(self):
        """Lista todos os usuários"""
        result = self.supabase.table('usuarios').select('*').execute() # equivale a SELECT * FROM usuarios
        return [self._row_to_usuario(row) for row in result.data] if result.data else []
    
    def atualizar_usuario(self, usuario_id, **kwargs):
        """Atualiza dados do usuário"""
        result = self.supabase.table('usuarios').update(kwargs).eq('id', usuario_id).execute()
        return result.data[0] if result.data else None
    
    def deletar_usuario(self, usuario_id):
        """Deleta usuário"""
        result = self.supabase.table('usuarios').delete().eq('id', usuario_id).execute()
        return bool(result.data)
    
    def verificar_senha(self, senha, senha_hash):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')) # compara a senha digitada com a senha hashada
        #bcrypt.checkpw() compara a senha digitada com a senha hashada
        #.encode('utf-8') transforma a string em bytes
        #senha_hash é a senha que foi salva no banco de dados
        # basicamente, ele vai cripitografar a senha digitada e vai gerar um hash denovo, so que sem o salt, 
        # ai ele vai comparar a senha hash com o hash do banco de dados
        # o salt que adicionamos nao atraplha nisso, o bcrypt é inteligente pra isso
    
    
    def criar_projeto_completo(self, nome, categoria, criador_id, **kwargs): # **kwargs permite que eu passe quantos argumentos eu quiser, sem precisar digitar tudo, 
        # nao é usada em todo codigo pois descobri so agr, teria que atualizar tudo
        """Cria um projeto completo com todos os campos"""
        
        data = { # monta o dicionario com os dados do projeto
            'nome': nome,
            'categoria': categoria,
            'criador_id': criador_id,
            'resumo': kwargs.get('resumo'),
            'palavras_chave': kwargs.get('palavras_chave'),
            'introducao': kwargs.get('introducao'),
            'objetivo_geral': kwargs.get('objetivo_geral'),
            'objetivos_especificos': kwargs.get('objetivos_especificos', []),
            'metodologia': kwargs.get('metodologia'),
            'cronograma': kwargs.get('cronograma'),
            'resultados_esperados': kwargs.get('resultados_esperados'),
            'referencias_bibliograficas': kwargs.get('referencias_bibliograficas'),
            'eh_continuacao': kwargs.get('eh_continuacao', False),
            'projeto_anterior_titulo': kwargs.get('projeto_anterior_titulo'),
            'projeto_anterior_resumo': kwargs.get('projeto_anterior_resumo'),
            'projeto_anterior_inicio': kwargs.get('projeto_anterior_inicio'),
            'projeto_anterior_termino': kwargs.get('projeto_anterior_termino'),
            'status': kwargs.get('status', 'rascunho'),
            'ano_edicao': kwargs.get('ano_edicao', datetime.now().year), #datetime.now().year pega o ano atual
            'gerado_por_ia': kwargs.get('gerado_por_ia', False),
            'prompt_ia_usado': kwargs.get('prompt_ia_usado')
        }
        
        result = self.supabase.table('projetos').insert(data).execute() # equivale a INSERT INTO projetos VALUES (data)
        return self._row_to_projeto(result.data[0]) if result.data else None #manda para a funcao _row_to_projeto que explicarei depois
    
    def atualizar_projeto(self, projeto_id, **kwargs):
        """Atualiza campos de um projeto"""
        # Remove campos None para não sobrescrever
        data = {k: v for k, v in kwargs.items() if v is not None}
        
        # Converte strings vazias para None em campos de data
        if 'projeto_anterior_inicio' in data and data['projeto_anterior_inicio'] == '':
            data['projeto_anterior_inicio'] = None
        #mesma coisa
        if 'projeto_anterior_termino' in data and data['projeto_anterior_termino'] == '':
            data['projeto_anterior_termino'] = None
    
        if data: # se houver informacoes para atualizar
            result = self.supabase.table('projetos').update(data).eq('id', projeto_id).execute() #equivale a UPDATE projetos SET data WHERE id = projeto_id
            return self._row_to_projeto(result.data[0]) if result.data else None # manda pro row_to_projeto
        return None # se nao houver informacoes para atualizar, volta None
    
    def deletar_projeto(self, projeto_id):
        """Deleta um projeto"""
        result = self.supabase.table('projetos').delete().eq('id', projeto_id).execute() #equivale a DELETE FROM projetos WHERE id = projeto_id
        return bool(result.data)
    
    def associar_participante_projeto(self, participante_id, projeto_id):
        """Associa participante a projeto"""
        data = {
            'participante_id': participante_id,
            'projeto_id': projeto_id
        }
        result = self.supabase.table('participantes_projetos').insert(data).execute() #equivale a INSERT INTO participantes_projetos (participante_id, projeto_id) VALUES (participante_id, projeto_id)
        return bool(result.data) #retorna True se deu certo, False se deu errado
    
    def associar_orientador_projeto(self, orientador_id, projeto_id):
        """Associa orientador a projeto"""
        # mesma coisa basicamente
        data = {
            'orientador_id': orientador_id,
            'projeto_id': projeto_id
        }
        result = self.supabase.table('orientadores_projetos').insert(data).execute() #equivale a INSERT INTO orientadores_projetos (orientador_id, projeto_id) VALUES (orientador_id, projeto_id)
        return bool(result.data) #retorna True se deu certo, False se deu errado
        
    def criar_chat(self, usuario_id, tipo_ia_id, titulo):
        """Cria um novo chat"""
        data = { # monta o dicionario com os dados do chat
            'usuario_id': usuario_id,
            'tipo_ia_id': tipo_ia_id,
            'titulo': titulo
        }
        result = self.supabase.table('chats').insert(data).execute() #equivale a INSERT INTO chats (usuario_id, tipo_ia_id, titulo) VALUES (usuario_id, tipo_ia_id, titulo)
        return self._row_to_chat(result.data[0]) if result.data else None #vou explicar o row to no proximo slide
    
    def buscar_chat_por_id(self, chat_id):
        """Busca chat por ID"""
        result = self.supabase.table('chats').select('*').eq('id', chat_id).execute()
        return self._row_to_chat(result.data[0]) if result.data else None
    
    def listar_chats_por_usuario(self, usuario_id):
        """Lista todos os chats de um usuário"""
        result = self.supabase.table('chats').select('*').eq('usuario_id', usuario_id).order('data_criacao', desc=True).execute() #equivale a SELECT * FROM chats WHERE usuario_id = usuario_id ORDER BY data_criacao DESC
        return [self._row_to_chat(row) for row in result.data] if result.data else [] #manda pro row_to_chat em forma de lista/vetor, afinal, pode retornar mais de 1 chat
    
    def deletar_chat(self, chat_id):
        """Deleta um chat (CASCADE deleta mensagens)"""
        logger.info(f"🗑️ Deletando chat ID: {chat_id}")
        
        try:
            # 1. primeiro deleta os arquvios do chat (cascade nao funciona pra arquivos)
            self.deletar_arquivos_por_chat(chat_id)
            
            # 2. dai sim Deleta chat (CASCADE deleta mensagens automaticamente)
            result = self.supabase.table('chats').delete().eq('id', chat_id).execute() #equivale a DELETE FROM chats WHERE id = chat_id (cascade é automatico)
            
            log_database_operation('DELETE', 'chats', data={'id': chat_id}, result='Success') #log de sussesso
            return bool(result.data) #retoirna true se deu certo, false se deu errado
            
        except Exception as e: #caso de erro
            log_database_operation('DELETE', 'chats', data={'id': chat_id}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao deletar chat: {e}")
            return False #retorna false se deu erro

    def criar_arquivo_chat(self, chat_id, nome_arquivo, url_arquivo, tipo_arquivo=None, 
                           tamanho_bytes=None, gemini_file_uri=None):
        """Cria registro de arquivo no banco"""
        logger.info(f"📎 Salvando arquivo no banco: {nome_arquivo}")
        
        data = {
            'chat_id': chat_id,
            'nome_arquivo': nome_arquivo,
            'url_arquivo': url_arquivo,
            'tipo_arquivo': tipo_arquivo,
            'tamanho_bytes': tamanho_bytes
        }
        
        if gemini_file_uri:
            data['gemini_file_uri'] = gemini_file_uri
            
            #adiciona o URI do arquivo gemini se tiver (se ja estiver expirado o arquivo, entao nao tem uri, por isso o if)
        
        try:
            result = self.supabase.table('arquivos_chat').insert(data).execute() #equivale a INSERT INTO arquivos_chat (chat_id, nome_arquivo, url_arquivo, tipo_arquivo, tamanho_bytes, gemini_file_uri) VALUES (chat_id, nome_arquivo, url_arquivo, tipo_arquivo, tamanho_bytes, gemini_file_uri)
            log_database_operation('INSERT', 'arquivos_chat', data={'nome': nome_arquivo}, result='Success') #log de sussesso
            
            if result.data: #se tiver data no resultado
                logger.info(f"✅ Arquivo salvo: ID {result.data[0]['id']}") #log de sussesso
                return result.data[0]['id']
            
            return None #se nao tiver data, retorna None
            
        except Exception as e:
            log_database_operation('INSERT', 'arquivos_chat', data={'nome': nome_arquivo}, result=f'Error: {e}') #log de erro
            logger.error(f"❌ Erro ao salvar arquivo: {e}") #log de erro
            raise #manda pra qm chamou o erro pra qm chamou a função

    def listar_arquivos_por_chat(self, chat_id):
        """Lista todos os arquivos de um chat"""
        logger.debug(f"📁 Buscando arquivos do chat {chat_id}")
    
        try:
            result = self.supabase.table('arquivos_chat')\
                .select('*')\
                .eq('chat_id', chat_id)\
                .order('data_upload', desc=False)\
                .execute() #equivale a SELECT * FROM arquivos_chat WHERE chat_id = chat_id ORDER BY data_upload ASC
        
            if result.data: #se retonar algum dado
                logger.info(f"✅ {len(result.data)} arquivos encontrados")
                return [self._row_to_arquivo_chat(row) for row in result.data] #manda pro row_to_arquivo_chat em forma de lista/vetor pra converter em objeto ArquivoChat
        
            return [] #se nao tiver dados, retorna lista vazia
        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar arquivos: {e}")
            return [] #se der erro, retorna lista vazia
        
    def buscar_arquivo_por_id(self, arquivo_id):
        """Busca arquivo por ID"""
        logger.debug(f"🔍 Buscando arquivo ID: {arquivo_id}")
        
        try:
            result = self.supabase.table('arquivos_chat')\
                .select('*')\
                .eq('id', arquivo_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar arquivo: {e}")
            return None

    def deletar_arquivo(self, arquivo_id):
        """Deleta arquivo do banco"""
        logger.info(f"🗑️ Deletando arquivo ID: {arquivo_id}")
        
        try:
            result = self.supabase.table('arquivos_chat')\
                .delete()\
                .eq('id', arquivo_id)\
                .execute()
            
            log_database_operation('DELETE', 'arquivos_chat', data={'id': arquivo_id}, result='Success')
            return bool(result.data)
            
        except Exception as e:
            log_database_operation('DELETE', 'arquivos_chat', data={'id': arquivo_id}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao deletar arquivo: {e}")
            return False

    def associar_arquivo_mensagem(self, arquivo_id, mensagem_id):
        """Associa arquivo a uma mensagem específica"""
        try:
            result = self.supabase.table('arquivos_chat')\
                .update({'mensagem_id': mensagem_id})\
                .eq('id', arquivo_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível associar arquivo à mensagem: {e}")
            logger.warning("💡 Considere adicionar coluna 'mensagem_id' em 'arquivos_chat'")
            return False

    def deletar_arquivos_por_chat(self, chat_id):
        """Deleta todos os arquivos de um chat"""
        logger.info(f"🗑️ Deletando todos os arquivos do chat {chat_id}")
        
        try:
            result = self.supabase.table('arquivos_chat')\
                .delete()\
                .eq('chat_id', chat_id)\
                .execute() #equivale a DELETE FROM arquivos_chat WHERE chat_id = chat_id
    
            return bool(result.data) #retorna True se der certo, False se der errado
            
        except Exception as e: #se deu erro
            logger.error(f"❌ Erro ao deletar arquivos: {e}")
            return False #retorna False se der erro
    
    def _row_to_usuario(self, row):
        """Converte linha do banco para objeto Usuario"""
        
        # Converte strings de data para datetime
        data_criacao = None
        if row.get('data_criacao'): #se existir data de criacao
            if isinstance(row['data_criacao'], str): #se data for uma string
                try:
                    data_criacao = datetime.fromisoformat(row['data_criacao'].replace('Z', '+00:00')) #converte a string para datetime e substitui z pelo fuso horario 00
                except: # se der erro, data_criacao = None
                    data_criacao = None
            else:
                data_criacao = row['data_criacao'] #se ja for datatime, usa diretamente
        
        data_atualizacao = None # faz a mesma coisa com data de atualização
        if row.get('data_atualizacao'):
            if isinstance(row['data_atualizacao'], str):
                try:
                    data_atualizacao = datetime.fromisoformat(row['data_atualizacao'].replace('Z', '+00:00'))
                except:
                    data_atualizacao = None
            else:
                data_atualizacao = row['data_atualizacao']
        
        return Usuario( # cria o objeto Usuario
            id=row['id'],
            nome_completo=row['nome_completo'],
            email=row['email'],
            senha_hash=row.get('senha_hash'),
            tipo_usuario_id=row['tipo_usuario_id'],
            numero_inscricao=row.get('numero_inscricao'),
            data_criacao=data_criacao,
            data_atualizacao=data_atualizacao,
            apelido=row.get('apelido')
        )
    
    def _row_to_projeto(self, row):
        """Converte linha do banco para objeto Projeto"""

        # string pra datetime
        data_criacao = None
        if row.get('data_criacao'): #se existir data de criacao
            if isinstance(row['data_criacao'], str): #se data for uma string
                try:
                    data_criacao = datetime.fromisoformat(row['data_criacao'].replace('Z', '+00:00')) #converte a string para datetime e substitui z pelo fuso horario 00
                except: # se der erro, data_criacao = None
                    data_criacao = None
            else:
                data_criacao = row['data_criacao']
        
        data_atualizacao = None
        if row.get('data_atualizacao'): #faz a mesma coisa com data de atualizacao
            if isinstance(row['data_atualizacao'], str):
                try:
                    data_atualizacao = datetime.fromisoformat(row['data_atualizacao'].replace('Z', '+00:00'))
                except:
                    data_atualizacao = None
            else:
                data_atualizacao = row['data_atualizacao']
        
        # mesma coisa
        projeto_anterior_inicio = None
        if row.get('projeto_anterior_inicio'):
            if isinstance(row['projeto_anterior_inicio'], str):
                try:
                    projeto_anterior_inicio = datetime.fromisoformat(row['projeto_anterior_inicio']).date()
                except:
                    projeto_anterior_inicio = None
        # tambem igual
        projeto_anterior_termino = None
        if row.get('projeto_anterior_termino'):
            if isinstance(row['projeto_anterior_termino'], str):
                try:
                    projeto_anterior_termino = datetime.fromisoformat(row['projeto_anterior_termino']).date()
                except:
                    projeto_anterior_termino = None

         # cria o objeto Projeto
        return Projeto(
            id=row['id'],
            nome=row['nome'],
            categoria=row['categoria'],
            resumo=row.get('resumo'),
            palavras_chave=row.get('palavras_chave'),
            introducao=row.get('introducao'),
            objetivo_geral=row.get('objetivo_geral'),
            objetivos_especificos=row.get('objetivos_especificos', []),
            metodologia=row.get('metodologia'),
            cronograma=row.get('cronograma'),
            resultados_esperados=row.get('resultados_esperados'),
            referencias_bibliograficas=row.get('referencias_bibliograficas'),
            eh_continuacao=row.get('eh_continuacao', False),
            projeto_anterior_titulo=row.get('projeto_anterior_titulo'),
            projeto_anterior_resumo=row.get('projeto_anterior_resumo'),
            projeto_anterior_inicio=projeto_anterior_inicio,
            projeto_anterior_termino=projeto_anterior_termino,
            status=row.get('status', 'rascunho'),
            ano_edicao=row.get('ano_edicao'),
            data_criacao=data_criacao,
            data_atualizacao=data_atualizacao,
            gerado_por_ia=row.get('gerado_por_ia', False),
            prompt_ia_usado=row.get('prompt_ia_usado'),
            criador_id=row.get('criador_id')
        )
    
    def _row_to_chat(self, row):
        """Converte linha do banco para objeto Chat"""
        
        #converte data igual ja falei antes
        data_criacao = None
        if row.get('data_criacao'):
            if isinstance(row['data_criacao'], str):
                try:
                    data_criacao = datetime.fromisoformat(row['data_criacao'].replace('Z', '+00:00'))
                except:
                    data_criacao = None
            else:
                data_criacao = row['data_criacao']
        
        return Chat(
            id=row['id'],
            usuario_id=row['usuario_id'],
            tipo_ia_id=row['tipo_ia_id'], # tipo_ia é uma ideida descartada, como falei, mais que nn deu tempo de remover
            titulo=row['titulo'],
            data_criacao=data_criacao
        )
    
    def _row_to_arquivo_chat(self, row):
        """Converte linha do banco para objeto ArquivoChat"""
    
        # Converte data_upload igual os outros row_to
        data_upload = None
        if row.get('data_upload'):
            if isinstance(row['data_upload'], str):
                try:
                    data_upload = datetime.fromisoformat(row['data_upload'].replace('Z', '+00:00'))
                except:
                    data_upload = None
            else:
                data_upload = row['data_upload']
    
        # Converte gemini_expiration igual convertemos datas ate aqui
        gemini_expiration = None
        if row.get('gemini_expiration'):
            if isinstance(row['gemini_expiration'], str):
                try:
                    gemini_expiration = datetime.fromisoformat(row['gemini_expiration'].replace('Z', '+00:00'))
                except:
                    gemini_expiration = None
            else:
                gemini_expiration = row['gemini_expiration']
    
        return ArquivoChat( #retorna o objeto ArquivoChat
            id=row['id'],
            chat_id=row['chat_id'],
            nome_arquivo=row['nome_arquivo'],
            url_arquivo=row['url_arquivo'],
            tipo_arquivo=row.get('tipo_arquivo'),
            tamanho_bytes=row.get('tamanho_bytes'),
            data_upload=data_upload,
            mensagem_id=row.get('mensagem_id'),
            gemini_file_uri=row.get('gemini_file_uri'),
            gemini_file_name=row.get('gemini_file_name'),
            gemini_expiration=gemini_expiration
        )
    

    def criar_mensagem(self, chat_id, role, conteudo, thinking_process=None):
        """
        Cria uma nova mensagem no histórico do chat
        """
        logger.debug(f"💬 Salvando mensagem: Chat {chat_id} | Role: {role}")
        data = {
            'chat_id': chat_id, #id do chat
            'role': role, #quem enviou a mensagem (usuario ou IA)
            'conteudo': conteudo # conteudo da mensage
        }
        
        # Adiciona thinking_process (processo de pensamento) se fornecido
        if thinking_process:
            data['thinking_process'] = thinking_process
            
            #entao dentro da data fica:
            # 'thinking_process': thinking_process
            # chat_id: chat_id
            # role: role
            # conteudo: conteudo
        
        try:
            result = self.supabase.table('mensagens').insert(data).execute()  #equivale a INSERT INTO mensagens (chat_id, role, conteudo, thinking_process) VALUES (chat_id, role, conteudo, thinking_process)
            log_database_operation('INSERT', 'mensagens', data={'chat_id': chat_id, 'role': role}, result='Success') #log de sussesso
            logger.info(f"✅ Mensagem salva: Chat {chat_id}") #logs
            return result.data[0] if result.data else None #retorna a mensagem salva SEM SER COMO UMA LISTA/VETOR (o [0] faz isso pra nos)
        except Exception as e:
            log_database_operation('INSERT', 'mensagens', data={'chat_id': chat_id}, result=f'Error: {e}') #log de erro
            logger.error(f"❌ Erro ao salvar mensagem: {e}") #outro log de erro
            raise

    def listar_mensagens_por_chat(self, chat_id, limit=100):
        """Lista mensagens de um chat (ordenadas por data)"""
        result = self.supabase.table('mensagens')\
            .select('*, notas_orientador(id, nota, data_criacao, orientador_id, usuarios(nome_completo))')\
            .eq('chat_id', chat_id)\
            .order('data_envio', desc=False)\
            .limit(limit)\
            .execute() #equivale a SELECT * FROM mensagens WHERE chat_id = chat_id ORDER BY data_envio ASC LIMIT 100
            #essa função é útil para carregar o histórico do chat
        
        return result.data if result.data else [] #retorna a lista de mensagens ou uma lista vazia se nao houver mensagens

    def contar_mensagens_por_chat(self, chat_id):
        """
        Conta quantas mensagens existem em um chat
        """
        result = self.supabase.table('mensagens')\
            .select('id', count='exact')\
            .eq('chat_id', chat_id)\
            .execute()
        
        return result.count if hasattr(result, 'count') else 0

    def deletar_mensagens_por_chat(self, chat_id):
        """
        Deleta todas as mensagens de um chat (chamado automaticamente por CASCADE)
        """
        result = self.supabase.table('mensagens')\
            .delete()\
            .eq('chat_id', chat_id)\
            .execute()
        
        return bool(result.data)

    def obter_ultimas_n_mensagens(self, chat_id, n=10):
        """
        Obtém as últimas N mensagens de um chat
        Útil para contexto limitado
        """
        result = self.supabase.table('mensagens')\
            .select('*')\
            .eq('chat_id', chat_id)\
            .order('data_envio', desc=True)\
            .limit(n)\
            .execute()
        
        # Inverte para ordem cronológica correta
        return list(reversed(result.data)) if result.data else []

    def listar_projetos_por_usuario(self, usuario_id):
        """
        Lista projetos de um usuário (via tabela de associação)
        """
        # Busca IDs dos projetos do usuário
        result = self.supabase.table('participantes_projetos')\
            .select('projeto_id')\
            .eq('participante_id', usuario_id)\
            .execute()
        
        if not result.data:
            return []
        
        projeto_ids = [row['projeto_id'] for row in result.data]
        
        # Busca os projetos completos
        projetos_result = self.supabase.table('projetos')\
            .select('*')\
            .in_('id', projeto_ids)\
            .execute()
        
        return [self._row_to_projeto(row) for row in projetos_result.data] if projetos_result.data else []

    def buscar_projeto_por_id(self, projeto_id):
        """Busca projeto por ID"""
        result = self.supabase.table('projetos')\
            .select('*')\
            .eq('id', projeto_id)\
            .execute() #equivalente a SELECT * FROM projetos WHERE id = projeto_id
        
        return self._row_to_projeto(result.data[0]) if result.data else None # retorna o resultado e manda pro row_to_projeto

    def listar_tipos_usuario(self):
        """Lista todos os tipos de usuário"""

        try:
            result = self.supabase.table('tipos_usuario').select('*').execute() #equivalente a SELECT * FROM tipos_usuario
            
            if result.data:
                return [TipoUsuario(id=row['id'], nome=row['nome']) for row in result.data] #retorna os dados da tabela tipos_usuario
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao buscar tipos de usuário: {e}, USANDO DADOS HARDCODED")
            # Retorna tipos padrão de segurança
            return [
                TipoUsuario(id=1, nome='Administrador'),
                TipoUsuario(id=2, nome='Participante'),
                TipoUsuario(id=3, nome='Orientador')
            ]
    
    def buscar_tipo_usuario_por_id(self, tipo_id):
        """ Busca tipo de usuário por ID """
        tipos = self.listar_tipos_usuario()
        return next((t for t in tipos if t.id == tipo_id), None)

    def atualizar_apelido(self, usuario_id, apelido):
        """Atualiza apelido do usuário"""
        logger.info(f"✏️ Atualizando apelido do usuário {usuario_id}")
        result = self.supabase.table('usuarios')\
            .update({'apelido': apelido})\
            .eq('id', usuario_id)\
            .execute() # equivale a UPDATE usuarios SET apelido = apelido WHERE id = usuario_id
    
        return bool(result.data) # o bool serve para verificar se a operação foi bem sucedida ou nao
        #se foi bem sucedida, retorna True, se nao, retorna False
        # se encontrou um usuario pra atualizar = true senao achou ninguem pra atualizar = false



    def listar_orientados_por_orientador(self, orientador_id):
        """ Lista todos os orientados de um orientador """
        logger.debug(f"📋 Buscando orientados do orientador {orientador_id}")
    
        try:
            # Busca IDs dos orientados via tabela de projetos
            # (assumindo que orientador e participante estão ligados via projetos)
            result = self.supabase.table('orientadores_projetos')\
                .select('projeto_id')\
                .eq('orientador_id', orientador_id)\
                .execute() #equivale a SELECT projeto_id FROM orientadores_projetos WHERE orientador_id = orientador_id
        
            if not result.data: #se nao tiver dados
                return [] #retorna lista vazia
        
            projeto_ids = [row['projeto_id'] for row in result.data] #pega os ids dos projetos
        
            # Busca participantes desses projetos
            participantes_result = self.supabase.table('participantes_projetos')\
                .select('participante_id')\
                .in_('projeto_id', projeto_ids)\
                .execute() #equivale a SELECT participante_id FROM participantes_projetos WHERE projeto_id IN projeto_ids
        
            if not participantes_result.data:
                return [] #retorna lista vazia se nao tiver dados
        
            participante_ids = list(set([row['participante_id'] for row in participantes_result.data])) #pega os ids dos participantes, usando set() para evitar duplicatas, pois um participante pode estar em varios projetos do mesmo orientador
        
            # Busca dados completos dos participantes
            orientados = []
            for participante_id in participante_ids:
                usuario = self.buscar_usuario_por_id(participante_id) #busca o usuario pelo id do participante
                if usuario:
                    # Adiciona chats
                    chats = self.listar_chats_por_usuario(participante_id)
                    orientado_data = usuario.to_dict()  #converte o usuario para dicionario
                    orientado_data['chats'] = [c.to_dict() for c in chats] #adiciona os chats do usuario ao dicionario
                    orientados.append(orientado_data) #adiciona o dicionario do orientado na lista de orientados
        
            logger.info(f"✅ {len(orientados)} orientados encontrados")
            return orientados
        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar orientados: {e}")
            return []


    def verificar_orientador_participante(self, orientador_id, participante_id):
        """ Verifica se um orientador tem permissao de acessar dados de um participante """
        try:
            # Busca projetos do orientador
            result = self.supabase.table('orientadores_projetos')\
                .select('projeto_id')\
                .eq('orientador_id', orientador_id)\
                .execute() #equivale a SELECT projeto_id FROM orientadores_projetos WHERE orientador_id = orientador_id
        
            if not result.data:
                return False # se nao tiver dados, retorna falso
        
            projeto_ids = [row['projeto_id'] for row in result.data] #pega os ids dos projetos
        
            # Verifica se participante está em algum desses projetos
            participante_result = self.supabase.table('participantes_projetos')\
                .select('participante_id')\
                .eq('participante_id', participante_id)\
                .in_('projeto_id', projeto_ids)\
                .execute() #equivale a SELECT participante_id FROM participantes_projetos WHERE participante_id = participante_id AND projeto_id IN projeto_ids
        
            return bool(participante_result.data) #retorna True se tiver dados, False se nao tiver dados
        
        except Exception as e:
            logger.error(f"❌ Erro ao verificar orientador-participante: {e}")
            return False #retorna falso em caso de erro


    def criar_nota_orientador(self, mensagem_id, orientador_id, nota):
        """ Cria nota do orientador em uma mensagem específica """
        logger.info(f"📝 Criando nota do orientador {orientador_id} na mensagem {mensagem_id}")
    
        data = { #cria um dicionario com os dados
            'mensagem_id': mensagem_id,
            'orientador_id': orientador_id,
            'nota': nota
        }
    
        result = self.supabase.table('notas_orientador')\
            .insert(data)\
            .execute() #equivalente a INSERT INTO notas_orientador (mensagem_id, orientador_id, nota) VALUES (mensagem_id, orientador_id, nota)
    
        log_database_operation('INSERT', 'notas_orientador', data, 'Success') #log de operação bem sussedida
        return result.data[0] if result.data else None #retorna o resultado ou None se nao voltar dados


    def listar_notas_por_mensagem(self, mensagem_id):
        """ Lista todas as notas de uma mensagem específica """
        result = self.supabase.table('notas_orientador')\
            .select('*, usuarios(nome_completo)')\
            .eq('mensagem_id', mensagem_id)\
            .order('data_criacao', desc=False)\
            .execute() #equivalente a SELECT * FROM notas_orientador WHERE mensagem_id = mensagem_id ORDER BY data_criacao ASC
    
        return result.data if result.data else [] #retorna a lista de notas ou uma lista vazia se nao tiver dados


    def buscar_nota_por_id(self, nota_id):
        """ Busca nota por ID """
        result = self.supabase.table('notas_orientador')\
            .select('*')\
            .eq('id', nota_id)\
            .execute()
    
        return result.data[0] if result.data else None


    def atualizar_nota_orientador(self, nota_id, nova_nota):
        """ Atualiza texto de uma nota """
        result = self.supabase.table('notas_orientador')\
            .update({
                'nota': nova_nota,
                'data_atualizacao': datetime.now().isoformat()
            })\
            .eq('id', nota_id)\
            .execute()
    
        return bool(result.data)


    def deletar_nota_orientador(self, nota_id):
        """ Deleta nota """
        result = self.supabase.table('notas_orientador')\
            .delete()\
            .eq('id', nota_id)\
            .execute()
    
        return bool(result.data)


    def contar_chats_com_notas(self, orientador_id):
        """ Conta quantos chats têm notas do orientador """
        result = self.supabase.table('notas_orientador')\
            .select('mensagem_id', count='exact')\
            .eq('orientador_id', orientador_id)\
            .execute()
    
        return result.count if hasattr(result, 'count') else 0


    def contar_notas_por_orientado(self, participante_id, orientador_id):
        """ Conta total de notas de um orientador em chats de um orientado """
        # Busca chats do participante
        chats = self.listar_chats_por_usuario(participante_id)
        chat_ids = [c.id for c in chats]
    
        if not chat_ids:
            return 0
    
        # Busca mensagens desses chats
        mensagens_result = self.supabase.table('mensagens')\
            .select('id')\
            .in_('chat_id', chat_ids)\
            .execute()
    
        if not mensagens_result.data:
            return 0
    
        mensagem_ids = [m['id'] for m in mensagens_result.data]
    
        # Conta notas do orientador nessas mensagens
        notas_result = self.supabase.table('notas_orientador')\
            .select('id', count='exact')\
            .eq('orientador_id', orientador_id)\
            .in_('mensagem_id', mensagem_ids)\
            .execute()
    
        return notas_result.count if hasattr(notas_result, 'count') else 0


    def registrar_visualizacao_orientador(self, orientador_id, chat_id):
        """ Registra que orientador visualizou um chat """
        data = {
            'orientador_id': orientador_id,
            'chat_id': chat_id
        }
    
        result = self.supabase.table('visualizacoes_orientador')\
            .insert(data)\
            .execute()
    
        return bool(result.data)


    def buscar_mensagem_por_id(self, mensagem_id):
        """ Busca mensagem por ID """
        result = self.supabase.table('mensagens')\
            .select('*')\
            .eq('id', mensagem_id)\
            .execute() #equivale a SELECT * FROM mensagens WHERE id = mensagem_id
            #usada na hora de adicionar notas
    
        return result.data[0] if result.data else None


    def salvar_ferramenta_usada(self, mensagem_id, ferramentas): 
        """ Salva informações sobre ferramentas usadas na mensagem """
    
        result = self.supabase.table('mensagens')\
            .update({'ferramenta_usada': json.dumps(ferramentas)})\
            .eq('id', mensagem_id)\
            .execute() #equivale a UPDATE mensagens SET ferramenta_usada = ferramentas WHERE id = mensagem_id
            #usada pra salvar o uso das ferramentas
            #json.dumps transforma o dicionario em string pra salvar no banco de dados
    
        return bool(result.data) # true se voltar algo, false se nao voltar nada


    def contar_uso_ferramenta(self, usuario_id, ferramenta):
        """ Conta quantas vezes um usuário usou uma ferramenta específica """
        # Busca chats do usuário
        chats = self.listar_chats_por_usuario(usuario_id)
        chat_ids = [c.id for c in chats]
    
        if not chat_ids:
            return 0
    
        # Busca mensagens com a ferramenta
        mensagens = self.supabase.table('mensagens')\
            .select('ferramenta_usada')\
            .in_('chat_id', chat_ids)\
            .execute()
    
        if not mensagens.data:
            return 0
    
        # Conta uso da ferramenta
        import json
        count = 0
        for msg in mensagens.data:
            if msg.get('ferramenta_usada'):
                try:
                    ferramentas = json.loads(msg['ferramenta_usada']) if isinstance(msg['ferramenta_usada'], str) else msg['ferramenta_usada']
                    if ferramentas.get(ferramenta):
                        count += 1
                except:
                    pass
    
        return count

    def listar_todos_projetos(self):
        """Lista todos os projetos do sistema"""
        logger.debug("📋 Listando todos os projetos")
        result = self.supabase.table('projetos').select('*').execute()
        return [self._row_to_projeto(row) for row in result.data] if result.data else []


    def listar_participantes_por_projeto(self, projeto_id):
        """ Lista participantes associados a um projeto """
        logger.debug(f"👥 Buscando participantes do projeto {projeto_id}")

        try:
            # Busca IDs dos participantes
            result = self.supabase.table('participantes_projetos')\
                .select('participante_id')\
                .eq('projeto_id', projeto_id)\
                .execute()

            if not result.data:
                return []

            participante_ids = [row['participante_id'] for row in result.data]

            # Busca dados completos dos participantes
            participantes = []
            for pid in participante_ids:
                usuario = self.buscar_usuario_por_id(pid)
                if usuario:
                    participantes.append(usuario)

            logger.info(f"✅ {len(participantes)} participantes encontrados")
            return participantes

        except Exception as e:
            logger.error(f"❌ Erro ao buscar participantes: {e}")
            return []

    def buscar_criador_projeto(self, projeto_id):
        """ Busca criador do projeto (primeiro participante) """
        try:
            result = self.supabase.table('participantes_projetos')\
                .select('participante_id')\
                .eq('projeto_id', projeto_id)\
                .order('data_associacao', desc=False)\
                .limit(1)\
                .execute()
            return result.data[0]['participante_id'] if result.data else None
        except:
            return None

    def verificar_acesso_projeto(self, usuario_id, projeto_id):
        """ Verifica se usuário tem acesso ao projeto """
        try:
            # É participante?
            result = self.supabase.table('participantes_projetos')\
                .select('id')\
                .eq('projeto_id', projeto_id)\
                .eq('participante_id', usuario_id)\
                .execute()
            if result.data:
                return True
            # É orientador?
            parts = self.listar_participantes_por_projeto(projeto_id)
            for p in parts:
                if self.verificar_orientador_participante(usuario_id, p.id):
                    return True
            return False
        except:
            return False


    def verificar_orientacao_existe(self, orientador_id, projeto_id):
        """ Verifica se orientação já existe """
        try:
            result = self.supabase.table('orientadores_projetos')\
                .select('*')\
                .eq('orientador_id', orientador_id)\
                .eq('projeto_id', projeto_id)\
                .execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"❌ Erro ao verificar orientação: {e}")
            return False


    def criar_orientacao(self, orientador_id, projeto_id):
        """ Cria associação orientador-projeto """
        logger.info(f"➕ Criando orientação: Orientador {orientador_id} -> Projeto {projeto_id}")

        try:
            data = {
                'orientador_id': orientador_id,
                'projeto_id': projeto_id
            }

            result = self.supabase.table('orientadores_projetos')\
                .insert(data)\
                .execute()

            log_database_operation('INSERT', 'orientadores_projetos', data, 'Success')
            logger.info("✅ Orientação criada")
            return bool(result.data)

        except Exception as e:
            log_database_operation('INSERT', 'orientadores_projetos', {'orientador': orientador_id, 'projeto': projeto_id}, f'Error: {e}')
            logger.error(f"❌ Erro ao criar orientação: {e}")
            raise


    def remover_orientacao(self, orientador_id, projeto_id):
        """ Remove associação orientador-projeto """
        logger.info(f"🗑️ Removendo orientação: Orientador {orientador_id} -> Projeto {projeto_id}")

        try:
            result = self.supabase.table('orientadores_projetos')\
                .delete()\
                .eq('orientador_id', orientador_id)\
                .eq('projeto_id', projeto_id)\
                .execute()

            log_database_operation('DELETE', 'orientadores_projetos', {'orientador': orientador_id, 'projeto': projeto_id}, 'Success')
            logger.info("✅ Orientação removida")
            return bool(result.data)
            
        except Exception as e:
            log_database_operation('DELETE', 'orientadores_projetos', {'orientador': orientador_id, 'projeto': projeto_id}, f'Error: {e}')
            logger.error(f"❌ Erro ao remover orientação: {e}")
            raise


    def listar_orientacoes_completas(self):
        """ Lista todas orientações com dados completos """
        logger.debug("📋 Listando orientações completas")

        try:
            # Busca todas as orientações
            result = self.supabase.table('orientadores_projetos')\
                .select('orientador_id, projeto_id')\
                .execute()

            if not result.data:
                return []

            orientacoes = []

            for row in result.data:
                orientador_id = row['orientador_id']
                projeto_id = row['projeto_id']

                # Busca dados do orientador
                orientador = self.buscar_usuario_por_id(orientador_id)
                if not orientador:
                    continue
                    
                # Busca dados do projeto
                projeto = self.buscar_projeto_por_id(projeto_id)
                if not projeto:
                    continue
                    
                # Busca participantes do projeto
                participantes = self.listar_participantes_por_projeto(projeto_id)
                
            # Para cada participante, cria uma entrada
                if participantes:
                    for participante in participantes:
                        orientacoes.append({
                            'id': f"{orientador_id}-{projeto_id}-{participante.id}",
                            'orientador_id': orientador_id,
                            'orientador_nome': orientador.nome_completo,
                            'orientador_email': orientador.email,
                            'participante_id': participante.id,
                            'participante_nome': participante.nome_completo,
                            'participante_bp': participante.numero_inscricao,
                            'projeto_id': projeto_id,
                            'projeto_nome': projeto.nome,
                            'projeto_categoria': projeto.categoria
                        })
                else:
                    # Projeto sem participantes ainda
                    orientacoes.append({
                        'id': f"{orientador_id}-{projeto_id}",
                        'orientador_id': orientador_id,
                        'orientador_nome': orientador.nome_completo,
                        'orientador_email': orientador.email,
                        'participante_id': None,
                        'participante_nome': '(Sem participantes)',
                        'participante_bp': '-',
                        'projeto_id': projeto_id,
                        'projeto_nome': projeto.nome,
                        'projeto_categoria': projeto.categoria
                    })

            logger.info(f"✅ {len(orientacoes)} orientações encontradas")
            return orientacoes

        except Exception as e:
            logger.error(f"❌ Erro ao listar orientações: {e}")
            return []


    def listar_projetos_por_orientador(self, orientador_id):
        """ Lista projetos de um orientador """
        logger.debug(f"📚 Buscando projetos do orientador {orientador_id}")

        try:
            result = self.supabase.table('orientadores_projetos')\
                .select('projeto_id')\
                .eq('orientador_id', orientador_id)\
                .execute() #equivale a SELECT projeto_id FROM orientadores_projetos WHERE orientador_id = orientador_id

            if not result.data: #se nao tiver dados
                return [] #retorna lista vazia

            projeto_ids = [row['projeto_id'] for row in result.data] #pega os ids dos projetos

            projetos = [] #cria uma lista vazia de projetos
            for pid in projeto_ids: #para cada id de projeto
                projeto = self.buscar_projeto_por_id(pid) #busca o projeto pelo id
                if projeto: #se tiver projeto
                    projetos.append(projeto) #adiciona o projeto na lista

            return projetos #retorna a lista de projetos

        except Exception as e:
            logger.error(f"❌ Erro ao buscar projetos: {e}")
            return [] #retorna lista vazia se der erro

    def atualizar_notas_chat(self, chat_id, notas):
        """ Atualiza as notas do orientador em um chat """
        logger.info(f"📝 Atualizando notas do chat {chat_id}")

        try:
            result = self.supabase.table('chats')\
                .update({'notas_orientador': notas})\
                .eq('id', chat_id)\
                .execute() # equivale a UPDATE chats SET notas_orientador = notas WHERE id = chat_id

            log_database_operation('UPDATE', 'chats', data={'id': chat_id, 'notas_orientador': notas[:50]}, result='Success') #log de operação bem sussedida
            logger.info(f"✅ Notas do chat {chat_id} atualizadas")

            return bool(result.data)

        except Exception as e: #caso de erro
            log_database_operation('UPDATE', 'chats', data={'id': chat_id}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao atualizar notas do chat: {e}")
            raise # manda o erro pro arquivo que chamou essa função
        
    def listar_tipos_ia(self):
        """ Lista todos os tipos de IA """
    
        try:
            result = self.supabase.table('tipos_ia').select('*').execute()
        
            if result.data:
                return [TipoIA(id=row['id'], nome=row['nome']) for row in result.data]

        except Exception as e:
            logger.warning(f"⚠️ Erro ao buscar tipos de IA: {e}")
            return [
                TipoIA(id=1, nome='Assistente Padrão'),
                TipoIA(id=2, nome='Assistente Participante'),
                TipoIA(id=3, nome='Assistente Orientador')
            ]

    def buscar_tipo_ia_por_id(self, tipo_id):
        """ Busca tipo de IA por ID """
        tipos = self.listar_tipos_ia()
        return next((t for t in tipos if t.id == tipo_id), None)
    
    def buscar_tipo_ia_por_nome(self, nome):
        """ Busca tipo de IA por nome (retorna ID) """
        result = self.supabase.table('tipos_ia')\
            .select('id')\
            .eq('nome', nome)\
            .execute()
        
        return result.data[0]['id'] if result.data else None