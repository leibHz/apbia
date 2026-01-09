"""
Serviço COMPLETO para Google Gemini 2.5 Flash
COM MODO BRAGANTEC OPCIONAL para reduzir consumo de tokens
"""

from google import genai
from google.genai import types
from google.genai.types import CountTokensConfig, Content, Part
import os
import time
from config import Config
from utils.advanced_logger import logger, log_ai_usage
from collections import defaultdict
from datetime import datetime, timedelta
from services.gemini_stats import gemini_stats


class GeminiService:
    """
    Serviço Gemini 2.5 Flash
    """
    
    def __init__(self):
        """Inicializa cliente Gemini"""
        logger.info("🤖 Inicializando GeminiService...")
        
        try:
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            self.model_name = 'gemini-2.5-flash' #infelizmente o gemini 3 e pago
            
            self.context_files = self._load_context_files()
            
            # Safety Settings: BLOCK_NONE
            self.safety_settings = [
                types.SafetySetting(
                    category='HARM_CATEGORY_HATE_SPEECH', # linguagekm de odio
                    threshold='BLOCK_NONE' #sem bloqueio
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_HARASSMENT', # assedio
                    threshold='BLOCK_NONE' #sem bloqueio
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_SEXUALLY_EXPLICIT', # conteudo sexual
                    threshold='BLOCK_NONE' #sem bloqueio
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_DANGEROUS_CONTENT', # conteudo perigoso
                    threshold='BLOCK_NONE' #sem bloqueio
                )
            ]
            
            logger.info("✅ GeminiService inicializado")
            logger.info(f"   Modelo: {self.model_name}")
            logger.info(f"   Context window: 1.048.576 tokens")
            logger.info(f"   Max output: 65.536 tokens")
            
        except Exception as e:
            logger.critical(f"💥 ERRO ao inicializar Gemini: {e}")
            raise
    
    def _load_context_files(self):
        """Carrega arquivos de contexto da Bragantec"""
        logger.debug("📂 Carregando arquivos de contexto...")
        context_content = []
        context_path = Config.CONTEXT_FILES_PATH
        
        if not os.path.exists(context_path):
            logger.warning(f"⚠️ Pasta {context_path} não existe")
            os.makedirs(context_path, exist_ok=True)
            return ""
        
        files_found = 0
        total_chars = 0
        
        for filename in os.listdir(context_path):
            if filename.endswith('.txt'):
                files_found += 1
                filepath = os.path.join(context_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        total_chars += len(content)
                        context_content.append(f"=== {filename} ===\n{content}\n")
                    logger.info(f"✅ Contexto carregado: {filename}")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar {filename}: {e}")
        
        if files_found == 0:
            logger.warning("⚠️ Nenhum arquivo .txt encontrado em context_files/")
        else:
            logger.info(f"✅ {files_found} arquivos carregados (~{total_chars:,} caracteres)")
        
        return "\n".join(context_content) if context_content else ""
    
    def _get_system_instruction(self, tipo_usuario, usar_contexto_bragantec=False, apelido=None):
    
        # SAUDAÇÃO PERSONALIZADA COM APELIDO
        saudacao = f"Olá, {apelido}! " if apelido else ""
    
        # PROMPT BASE
        base = f"""{saudacao}Você é o APBIA (Assistente de Projetos para Bragantec Baseado em IA), um assistente virtual especializado em ajudar estudantes e orientadores na Bragantec, a feira de ciências do IFSP Bragança Paulista.
        
    🤖 O que voçe é?    
    - Você foi criada pelo gabriel ferreira da silva, um estudante do ensino medio integrado ao tecnico de informatica do ifsp de bragança paulista como um trabalho da matéria projeto integrador (PJI)
    - seu objetivo é ajudar os participantes a desenvolverem projetos científicos inovadores e de alta qualidade para a competição.
    - so fale quem é o seu cirador se te pedirem
    
    APBIA é uma sigla para:  
    - Assistente de 
    - Projetos para 
    - Bragantec baseado em 
    - IA
    
    🤖 a plataforma em que vc esta:
    - é uma plataforma web

    🤖 O que é a Bragantec?
    - A Bragantec (Feira de Ciência e Tecnologia) é um evento anual organizado pelo Instituto Federal de São Paulo (IFSP) Campus Bragança Paulista. Trata-se de uma feira científica que promove o desenvolvimento da criatividade, inovação e interesse científico-tecnológico entre estudantes.
    
    A BRAGANTEC tem os seguintes objetivos:
    - Incentivar a criatividade e a inovação dos estudantes.
    - Estimular a criatividade dos estudantes é crucial para prepará-los para os desafios do mundo e impulsionar o progresso da sociedade. ⚗️⚗️
    
    - Despertar vocações científicas e/ou tecnológicas
    - Novas descobertas são essenciais para inspirar o futuro da ciência e da inovação. 🔭🔭
    
    - Identificar jovens talentosos que possam ser estimulados a seguirem carreiras científico-tecnológicas.
    - Aqui vai ter a oportunidade de criar, inovar e se descobrir.

    Áreas de Conhecimento
    Os projetos apresentados na Bragantec abrangem diversas áreas:

    Ciências da Natureza e Exatas
    - Física
    - Química
    - Biologia
    - Matemática
    - Informática

    Desenvolvimento de software
    - Robótica
    - Inteligência Artificial
    - Sistemas embarcados
    
    Ciências Humanas e Linguagens
    - História
    - Geografia
    - Sociologia
    - Línguas
    
    Engenharias
    - Engenharia Civil
    - Engenharia Mecânica
    - Engenharia Elétrica
    - Engenharia de Produção

    local da bragantec: Campus Bragança Paulista do IFSP (Av. Major Fernando Valle, 2013 - São Miguel)
    site oficial da Bragantec: feirabragantec.com.br

    🎯 SUAS CAPACIDADES:
    - Buscar informações atualizadas no Google (SEMPRE cite as fontes com links)
    - Executar código Python para validar soluções
    - Analisar imagens, vídeos, documentos e áudio
    - Pensar profundamente sobre problemas complexos
    - Gerar saídas estruturadas em JSON

    💡 SUA PERSONALIDADE:
    - Amigável, acessível e encorajadora
    - Paciente e didática
    - Entusiasta por ciência e inovação
    - Sempre cite fontes quando usar Google Search
    {f"- Chame o usuário pelo apelido '{apelido}' para criar conexão" if apelido else ""}

    📚 SUAS FUNÇÕES:
    - Auxiliar no desenvolvimento de projetos científicos
    - Sugerir ideias inovadoras
    - Ajudar no planejamento de projetos
    - Esclarecer dúvidas sobre metodologia científica

    ⚠️ CITAÇÕES OBRIGATÓRIAS:
    Quando usar Google Search, SEMPRE:
    1. Cite a fonte com o link completo
    2. Exemplo: "Segundo [Nome da Fonte](link), ..."
    3. Nunca invente informações sem fontes
    """

        # ADICIONA CONTEXTO BRAGANTEC SE ATIVADO
        if usar_contexto_bragantec:
            base += f"""

    📖 CONHECIMENTO SOBRE A BRAGANTEC:
    Você tem acesso ao histórico completo das edições anteriores da Bragantec de 2011 ate 2019, incluindo:
    - Projetos vencedores e suas características
    - Critérios de avaliação dos jurados
    - Tendências e padrões de projetos premiados
    - Categorias: Ciências da Natureza e Exatas, Informática, Ciências Humanas e Linguagens, Engenharias

    Use este conhecimento para:
    - Sugerir ideias alinhadas com projetos vencedores anteriores
    - Orientar sobre o que os jurados valorizam
    - Identificar oportunidades de inovação baseadas em edições passadas

    ⚠️ IMPORTANTE: Este conhecimento consome muitos tokens. Use-o com sabedoria.
    """
        else:
            base += """

    ℹ️ MODO SEM CONTEXTO BRAGANTEC:
    O usuário desativou o contexto histórico da Bragantec para economizar recursos.
    Você ainda pode:
    - Ajudar com metodologia científica geral
    - Buscar informações atualizadas no Google
    - Auxiliar no planejamento de projetos
    - Sugerir ideias baseadas em conhecimento geral
    - vc ainda tem um conhecimento basico sobnre a bragantec no system prompt.
    - se o usuario perguntar algo mais especifico sobre a bragantec que vc nao saiba, nao invente informação, fala que pra responder essa pergunta é nessesario o usuario ativar o modo Bragantec.

    💡 DICA: O usuário pode ativar o "Modo Bragantec" para ter acesso ao histórico completo de edições anteriores.
    """

        # PERSONALIZAÇÃO POR TIPO DE USUÁRIO
        if tipo_usuario == 'participante':
            base += f"""

    ✨ MODO PARTICIPANTE:
    {f"Fique à vontade, {apelido}! " if apelido else ""}Foque em ajudá-lo a desenvolver seu projeto científico com entusiasmo e clareza.
    Seja encorajador, explique conceitos de forma didática e ajude-o a brilhar na apresentação.
    foque somente nos projetos com status: em andamento e nao fale de outros projetos com diferentes status a nao ser que o usuario pergunte
    """
        elif tipo_usuario == 'orientador':
            base += f"""

    👨‍🏫 MODO ORIENTADOR:
    {f"É um prazer ajudá-lo, {apelido}! " if apelido else ""}Forneça insights pedagógicos e estratégias para guiar múltiplos projetos.
    Ajude na orientação de estudantes com dicas profissionais e boas práticas.
    
    🎯 VOCÊ TEM ACESSO A:
    - Lista de seus orientados (nome, email, BP)
    - Projetos que você está orientando (com dados dos participantes)
    - foque somente nos projetos com status: em andamento e nao fale de outros projetos com diferentes status a nao ser que o usuario pergunte
    
    💡 USE ESSES DADOS PARA:
    - Identificar orientados que precisam de mais atenção
    - Sugerir melhorias específicas para cada projeto
    """

        elif tipo_usuario == 'administrador':
            base += f"""
            
    👨‍💼 MODO ADMINISTRADOR:
    {f"Olá, {apelido}! " if apelido else ""}Você está falando com um administrador do sistema APBIA.
    Ajude com visão estratégica sobre o funcionamento geral da Bragantec e sugestões de melhorias sistêmicas.
    Seja objetivo e forneça informações que auxiliem na tomada de decisões administrativas.
    """

        return base


    def chat(self, message, tipo_usuario='participante', history=None, 
         usar_pesquisa=True, usar_code_execution=True, analyze_url=None, 
         usar_contexto_bragantec=False, user_id=None, apelido=None):
        
        logger.info("🚀 Iniciando chat com Gemini")
        logger.debug(f"   Tipo usuário: {tipo_usuario}")
        logger.debug(f"   Google Search: {usar_pesquisa}")
        logger.debug(f"   Code Execution: {usar_code_execution}")
        logger.debug(f"   🎯 MODO BRAGANTEC: {usar_contexto_bragantec}")
        logger.debug(f"   Histórico: {len(history) if history else 0} mensagens")
        
        # Verifica limites
        can_proceed, error_msg = gemini_stats.check_limits(user_id)
        if not can_proceed:
            logger.warning(f"⚠️ Rate limit excedido: {error_msg}")
            return {
                'response': f"⚠️ {error_msg}",
                'thinking_process': None,
                'error': True,
                'search_used': False,
                'code_executed': False,
                'code_results': None
            }
        
        start_time = time.time()
        
        try:
            # System instruction OTIMIZADA
            system_instruction = self._get_system_instruction(
                tipo_usuario, 
                usar_contexto_bragantec,
                apelido  # NOVO
            )
            
            # ADICIONA CONTEXTO BRAGANTEC APENAS SE ATIVADO
            if usar_contexto_bragantec:
                full_message = f"{system_instruction}\n\n{self.context_files}\n\n=== MENSAGEM DO USUÁRIO ===\n{message}"
                logger.info("📚 Contexto Bragantec ADICIONADO (~{} chars)".format(len(self.context_files)))
            else:
                full_message = f"{system_instruction}\n\n=== MENSAGEM DO USUÁRIO ===\n{message}"
                logger.info("🚀 Contexto Bragantec DESABILITADO (economia de tokens)")
            
            # Ferramentas
            tools = []
            
            if usar_pesquisa:
                tools.append(types.Tool(google_search=types.GoogleSearch()))
                logger.info("🔍 Google Search habilitado")
            
            if usar_code_execution:
                tools.append(types.Tool(code_execution=types.ToolCodeExecution()))
                logger.info("🐍 Code Execution habilitado")
            
            # Configuração
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=65536,
                tools=tools if tools else None,
                safety_settings=self.safety_settings,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=24000, # tecnologia legada com a chegada do gemini 3
                    include_thoughts=True
                )
            )
            
            # Prepara conteúdo
            contents = []
            
            # Adiciona histórico
            if history:
                for msg in history:
                    contents.append(msg['parts'][0])
            
            # Adiciona mensagem atual
            contents.append(full_message)
            
            # Gera resposta
            logger.debug("📤 Enviando requisição...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Extrai dados
            thinking_process = None
            response_text = ""
            code_executed = False
            code_results = []
            
            logger.debug(f"📦 Processando {len(response.candidates[0].content.parts)} parts")
            
            for i, part in enumerate(response.candidates[0].content.parts):
                logger.debug(f"   Part {i}: {type(part).__name__}")
                
                # Thinking process
                if part.thought:
                    thinking_process = part.text
                    logger.info(f"💭 Thinking: {len(thinking_process)} chars")
                
                # Code execution
                elif hasattr(part, 'executable_code') and part.executable_code:
                    code_executed = True
                    code_info = {
                        'language': part.executable_code.language if hasattr(part.executable_code, 'language') else 'python',
                        'code': part.executable_code.code if hasattr(part.executable_code, 'code') else str(part.executable_code)
                    }
                    logger.info(f"🐍 Código detectado: {code_info['language']}")
                    code_results.append(code_info)
                
                # Resultado da execução
                elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                    result_info = {
                        'outcome': part.code_execution_result.outcome if hasattr(part.code_execution_result, 'outcome') else 'unknown',
                        'output': part.code_execution_result.output if hasattr(part.code_execution_result, 'output') else str(part.code_execution_result)
                    }
                    logger.info(f"✅ Resultado: {result_info['outcome']}")
                    
                    if code_results:
                        code_results[-1]['result'] = result_info
                
                # Texto normal
                elif part.text and not part.thought:
                    response_text += part.text
            
            # Verifica Google Search
            search_used = False
            try:
                if hasattr(response.candidates[0], 'grounding_metadata'):
                    grounding = response.candidates[0].grounding_metadata
                    if grounding and hasattr(grounding, 'web_search_queries'):
                        queries = grounding.web_search_queries
                        if queries and isinstance(queries, (list, tuple)) and len(queries) > 0:
                            search_used = True
                            logger.info(f"🔍 Google Search usado: {len(queries)} queries")
                            gemini_stats.record_search(user_id)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao verificar Google Search: {e}")
            
            # Registra estatísticas
            tokens_input = 0
            tokens_output = 0
            
            if hasattr(response, 'usage_metadata'):
                tokens_input = response.usage_metadata.prompt_token_count
                tokens_output = response.usage_metadata.candidates_token_count
                
                gemini_stats.record_request(user_id, tokens_input, tokens_output)
                
                logger.info(f"📊 Tokens - Input: {tokens_input:,} | Output: {tokens_output:,}")
                
                # ALERTA se consumo alto
                if tokens_input > 100000:
                    logger.warning(f"⚠️ CONSUMO ALTO DE TOKENS INPUT: {tokens_input:,}")
                    logger.warning(f"💡 Considere desativar o Modo Bragantec para economizar")
                
                if hasattr(response.usage_metadata, 'cached_content_token_count'):
                    cached = response.usage_metadata.cached_content_token_count
                    if cached is not None and cached > 0:
                        logger.info(f"💾 Cache usado: {cached:,} tokens economizados!")
            
            duration = (time.time() - start_time) * 1000
            logger.info(f"✅ Resposta gerada em {duration:.2f}ms ({len(response_text)} chars)")
            
            # Log de uso
            log_ai_usage(
                self.model_name,
                'CHAT',
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                thinking=bool(thinking_process),
                search=search_used
            )
            
            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'search_used': search_used,
                'code_executed': code_executed,
                'code_results': code_results if code_results else None,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'total_tokens': tokens_input + tokens_output
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"❌ Erro após {duration:.2f}ms: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            return {
                'response': f"Erro ao processar mensagem: {str(e)}",
                'thinking_process': None,
                'error': True,
                'search_used': False,
                'code_executed': False,
                'code_results': None,
                'tokens_input': 0,
                'tokens_output': 0,
                'total_tokens': 0
            }
    
    def upload_file(self, file_path, mime_type=None):
        
        try:
            logger.info(f"📤 Upload: {file_path}")

            # Define MIME type 
            if mime_type:
                logger.info(f"📋 Usando MIME type fornecido: {mime_type}")

                with open(file_path, 'rb') as f:
                    uploaded_file = self.client.files.upload(
                        file=f,
                        config={
                            'mime_type': mime_type,
                            'display_name': os.path.basename(file_path)
                        }
                    )
            else:
                # Fallback: deixa API detectar
                logger.info(f"🔍 Deixando API detectar MIME type")
                with open(file_path, 'rb') as f:
                    uploaded_file = self.client.files.upload(file=f)

            logger.info(f"✅ Upload concluído: {uploaded_file.display_name}")
            logger.info(f"   URI: {uploaded_file.uri}")
            logger.info(f"   MIME: {uploaded_file.mime_type}")

            # Aguarda processamento (para vídeos)
            while uploaded_file.state.name == "PROCESSING":
                logger.info("⏳ Processando...")
                time.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)

            if uploaded_file.state.name == "FAILED":
                raise ValueError(f"Falha no processamento: {uploaded_file.error}")

            logger.info("✅ Arquivo pronto!")
            return uploaded_file

        except Exception as e:
            logger.error(f"❌ Erro no upload: {e}")
            return None


    def chat_with_file(self, message, file_path, tipo_usuario='participante', user_id=None, keep_file_on_gemini=False, mime_type=None):
        
        # Verifica limites
        can_proceed, error_msg = gemini_stats.check_limits(user_id)
        if not can_proceed:
            return {'response': f"⚠️ {error_msg}", 'error': True}

        try:
            # Upload com MIME type
            uploaded_file = self.upload_file(file_path, mime_type=mime_type)
            if not uploaded_file:
                return {'response': 'Erro ao fazer upload', 'error': True}

            # Detecta tipo
            mime = uploaded_file.mime_type.lower()
            if 'image' in mime:
                file_type = 'imagem'
            elif 'video' in mime:
                file_type = 'vídeo'
            elif 'audio' in mime:
                file_type = 'áudio'
            else:
                file_type = 'documento'

            logger.info(f"🔍 Tipo: {file_type} | URI: {uploaded_file.uri}")

            # System instruction
            system_instruction = self._get_system_instruction(tipo_usuario)

            full_message = f"{system_instruction}\n\n{self.context_files}\n\n{message}"

            # Config
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=65536,
                safety_settings=self.safety_settings,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=20000,
                    include_thoughts=True
                )
            )

            # Gera resposta
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[full_message, uploaded_file],
                config=config
            )

            # Extrai dados
            thinking_process = None
            response_text = ""

            for part in response.candidates[0].content.parts:
                if part.thought:
                    thinking_process = part.text
                elif part.text:
                    response_text += part.text

            # Registra estatísticas
            if hasattr(response, 'usage_metadata'):
                tokens_input = response.usage_metadata.prompt_token_count
                tokens_output = response.usage_metadata.candidates_token_count
                gemini_stats.record_request(user_id, tokens_input, tokens_output)
                logger.info(f"📊 Tokens - Input: {tokens_input:,} | Output: {tokens_output:,}")

            # Decide se mantém ou deleta
            gemini_file_uri = None

            if keep_file_on_gemini:
                gemini_file_uri = uploaded_file.uri
                logger.info(f"💾 Arquivo mantido no Gemini por 48h: {uploaded_file.name}")
                logger.info(f"   URI: {gemini_file_uri}")
                logger.info(f"   Expira em: {uploaded_file.expiration_time}")
            else:
                self.client.files.delete(name=uploaded_file.name)
                logger.info("🗑️ Arquivo deletado do Gemini")

            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'file_type': file_type,
                'gemini_file_uri': gemini_file_uri,
                'gemini_file_name': uploaded_file.name if keep_file_on_gemini else None,
                'gemini_expiration': str(uploaded_file.expiration_time) if keep_file_on_gemini else None
            }

        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return {'response': f"Erro: {str(e)}", 'error': True}
    
    
    def count_tokens(self, text):

        try:
            
        
            # Cria conteúdo para contar
            contents = [
                Content(
                    parts=[Part(text=text)],
                    role='user'
                )
            ]
        
            result = self.client.models.count_tokens(
                model=self.model_name,
                contents=contents
            )
        
            # Retorna contagem total
            token_count = result.total_tokens
        
            logger.info(f"📊 Contagem de tokens: {token_count} tokens para {len(text)} caracteres")
        
            return token_count
        
        except Exception as e:
            logger.warning(f"⚠️ Erro ao contar tokens via API: {e}")
            logger.info("💡 Usando fallback: 1 token ≈ 4 caracteres")
        
            # Fallback: estimativa aproximada
            # geralmente 1 token ≈ 4 caracteres
            estimated_tokens = max(1, len(text) // 4)
        
            return estimated_tokens
    
    def get_stats(self):
        """Retorna estatísticas atuais"""
        return gemini_stats.get_stats()