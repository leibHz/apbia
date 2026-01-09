"""
Guest Controller - Modo Anônimo do APBIA
Reutiliza services existentes sem salvar dados no banco
"""

from flask import Blueprint, render_template, request, jsonify, send_file
from services.gemini_service import GeminiService
from services.pdf_service import BragantecPDFGenerator
from config import Config
from utils.advanced_logger import logger
from utils.helpers import generate_chat_title, detect_mime_type, save_uploaded_file
from werkzeug.utils import secure_filename
import os
import uuid
import json
from io import BytesIO
from datetime import datetime

guest_bp = Blueprint('guest', __name__, url_prefix='/guest')

# Inicializa serviços (sem DAO - nada vai pro banco)
gemini = GeminiService()

# Diretório temporário para arquivos guest
GUEST_TEMP_DIR = os.path.join(Config.UPLOAD_FOLDER, 'guest_temp')
os.makedirs(GUEST_TEMP_DIR, exist_ok=True)


# ==========================================
# ROTAS DE PÁGINAS
# ==========================================

@guest_bp.route('/')
def index():
    """Página principal do chat guest"""
    if not Config.IA_STATUS:
        return render_template('guest_chat.html', ia_offline=True)
    
    return render_template('guest_chat.html', ia_offline=False)


@guest_bp.route('/projetos')
def projetos_index():
    """Página de projetos guest (lista do localStorage)"""
    return render_template('guest_projetos/index.html')


@guest_bp.route('/projetos/novo')
def projetos_novo():
    """Página de criar projeto guest"""
    return render_template('guest_projetos/criar.html')


# ==========================================
# API: CHAT
# ==========================================

@guest_bp.route('/send', methods=['POST'])
def send_message():
    """
    Envia mensagem para IA (guest mode)
    - Não salva no banco
    - Frontend guarda no localStorage
    - REUTILIZA lógica de contexto do chat_controller
    """
    if not Config.IA_STATUS:
        return jsonify({
            'error': True,
            'message': 'IA está temporariamente offline.'
        }), 503
    
    data = request.json
    message = data.get('message', '')
    apelido = data.get('apelido')
    usar_pesquisa = data.get('usar_pesquisa', True)
    usar_code_execution = data.get('usar_code_execution', True)
    usar_contexto_bragantec = data.get('usar_contexto_bragantec', False)
    history = data.get('history', [])
    projetos = data.get('projetos', [])  # Projetos do localStorage
    
    if not message:
        return jsonify({'error': True, 'message': 'Mensagem vazia'}), 400
    
    try:
        logger.info(f"🔓 Guest chat - Apelido: {apelido or 'Anônimo'}")
        logger.debug(f"   Bragantec: {usar_contexto_bragantec}")
        logger.debug(f"   Projetos do localStorage: {len(projetos)}")
        
        # ✅ REUTILIZA lógica de contexto do chat_controller
        contexto_projetos = ""
        if projetos:
            contexto_projetos = """
📁 **CONTEXTO: PROJETOS DO USUÁRIO**
Os projetos abaixo pertencem ao usuário. Use estas informações para ajudá-lo melhor:
"""
            for projeto in projetos:
                contexto_projetos += f"""
                    Projeto: {projeto.get('nome', 'Sem nome')}
                    Categoria: {projeto.get('categoria', 'Não informado')}
                    Status: {projeto.get('status', 'Em andamento')}
                    Resumo: {projeto.get('resumo', 'Não informado')}
                    ---
"""
        
        # Mensagem com contexto de projetos
        message_com_contexto = f"{contexto_projetos}\n\n{message}" if contexto_projetos else message
        
        # Chama Gemini (user_id=None pula estatísticas)
        response = gemini.chat(
            message_com_contexto,
            tipo_usuario='participante',  # Guest tem mesmas features de participante
            history=history,
            usar_pesquisa=usar_pesquisa,
            usar_code_execution=usar_code_execution,
            usar_contexto_bragantec=usar_contexto_bragantec,
            user_id=None,  # Importante: não registra estatísticas
            apelido=apelido
        )
        
        if response.get('error'):
            return jsonify({
                'error': True,
                'message': response['response']
            }), 500
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'search_used': response.get('search_used', False),
            'code_executed': response.get('code_executed', False),
            'code_results': response.get('code_results'),
            'tokens_input': response.get('tokens_input', 0),
            'tokens_output': response.get('tokens_output', 0)
        })
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro guest chat: {traceback.format_exc()}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@guest_bp.route('/upload-file', methods=['POST'])
def upload_file():
    """
    Upload de arquivo para análise (guest mode)
    - Arquivo temporário, não persiste
    """
    if not Config.IA_STATUS:
        return jsonify({'error': True, 'message': 'IA offline'}), 503
    
    if 'file' not in request.files:
        return jsonify({'error': True, 'message': 'Nenhum arquivo'}), 400
    
    file = request.files['file']
    message = request.form.get('message', 'Analise este arquivo')
    apelido = request.form.get('apelido')
    
    if file.filename == '':
        return jsonify({'error': True, 'message': 'Arquivo inválido'}), 400
    
    try:
        # Salva temporariamente
        temp_filename = secure_filename(file.filename)
        temp_path = os.path.join(GUEST_TEMP_DIR, f"guest_{uuid.uuid4()}_{temp_filename}")
        file.save(temp_path)
        
        mime_type = detect_mime_type(temp_filename, file.content_type)
        logger.info(f"📁 Guest upload: {temp_filename} ({mime_type})")
        
        # Processa com Gemini
        response = gemini.chat_with_file(
            message,
            temp_path,
            'participante',
            user_id=None,
            keep_file_on_gemini=False,  # Não mantém no Gemini
            mime_type=mime_type
        )
        
        # Remove arquivo temporário
        try:
            os.remove(temp_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'file_info': {
                'name': temp_filename,
                'type': mime_type
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro guest upload: {traceback.format_exc()}")
        
        # Limpa temporário
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


# ==========================================
# API: PROJETOS
# ==========================================

@guest_bp.route('/projetos/gerar-ideias', methods=['POST'])
def gerar_ideias():
    """
    Gera ideias de projetos com IA (guest mode)
    Reutiliza lógica do project_controller
    """
    logger.info("💡 Guest - Gerando ideias de projetos")
    
    try:
        # Prompt idêntico ao project_controller
        prompt = """
        🎯 **MISSÃO CRÍTICA: CRIAR PROJETOS VENCEDORES PARA A BRAGANTEC 2025**

        Você tem acesso ao histórico COMPLETO das edições anteriores da Bragantec (feira de ciências do IFSP Bragança Paulista), incluindo cadernos de resumos com TODOS os projetos vencedores.

        **ANÁLISE OBRIGATÓRIA ANTES DE CRIAR:**
        
        1. **ESTUDE OS PROJETOS VENCEDORES** nos arquivos de contexto que você possui
        2. **IDENTIFIQUE PADRÕES DE SUCESSO:**
           - Que temas/abordagens venceram mais?
           - Quais características os projetos premiados têm em comum?
           - Que nível de complexidade/inovação foi valorizado?
           - Quais problemas reais foram abordados?
           - Que metodologias foram bem avaliadas?
        
        3. **ENTENDA OS CRITÉRIOS DE AVALIAÇÃO:**
           - **Inovação e criatividade** (30 pontos)
           - **Relevância científica/social** (25 pontos)
           - **Fundamentação teórica** (20 pontos)
           - **Viabilidade de execução** (15 pontos)
           - **Impacto potencial** (10 pontos)

        ---

        **AGORA CRIE 4 IDEIAS DE PROJETOS (UMA POR CATEGORIA):**

        Com base na sua análise dos projetos vencedores das edições anteriores da Bragantec, crie UMA ideia de projeto para CADA uma das 4 categorias:

        1. **Ciências da Natureza e Exatas**
        2. **Informática**
        3. **Ciências Humanas e Linguagens**
        4. **Engenharias**

        **PARA CADA CATEGORIA, FORNEÇA:**

        - **titulo**: Título atrativo, direto e científico (máx 80 caracteres)
        - **resumo**: Resumo executivo COMPLETO E PROFISSIONAL (200-250 palavras)
        - **palavras_chave**: Exatamente 3 palavras-chave técnicas/científicas separadas por vírgula
        - **inspiracao_vencedores**: Características de projetos vencedores que inspiraram esta ideia
        - **diferenciais_competitivos**: O que torna este projeto um VENCEDOR POTENCIAL
        - **viabilidade_tecnica**: Nível de dificuldade e recursos necessários

        **FORMATO DE SAÍDA (JSON ESTRITO):**

        ```json
        {
          "Ciências da Natureza e Exatas": {
            "titulo": "...",
            "resumo": "...",
            "palavras_chave": "palavra1, palavra2, palavra3",
            "inspiracao_vencedores": "...",
            "diferenciais_competitivos": "...",
            "viabilidade_tecnica": "..."
          },
          "Informática": { ... },
          "Ciências Humanas e Linguagens": { ... },
          "Engenharias": { ... }
        }
        ```

        **NÃO ADICIONE TEXTO EXPLICATIVO. RETORNE APENAS O JSON.**
        """
        
        response = gemini.chat(
            prompt,
            tipo_usuario='participante',
            usar_contexto_bragantec=True,
            usar_pesquisa=True,
            usar_code_execution=False,
            user_id=None  # Guest mode
        )
        
        if response.get('error'):
            return jsonify({
                'error': True,
                'message': 'Erro ao gerar ideias com IA'
            }), 500
        
        # Parse JSON da resposta
        ideias_text = response['response']
        
        try:
            if '```json' in ideias_text:
                ideias_text = ideias_text.split('```json')[1].split('```')[0].strip()
            elif '```' in ideias_text:
                ideias_text = ideias_text.split('```')[1].split('```')[0].strip()
            
            ideias = json.loads(ideias_text)
            
            return jsonify({
                'success': True,
                'ideias': ideias,
                'formato': 'json',
                'metadata': {
                    'analise_vencedores': True,
                    'modo_bragantec': True,
                    'guest_mode': True
                }
            })
            
        except (json.JSONDecodeError, ValueError):
            return jsonify({
                'success': True,
                'ideias': ideias_text,
                'formato': 'texto',
                'aviso': 'A IA não retornou JSON estruturado.'
            })
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro guest gerar ideias: {traceback.format_exc()}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@guest_bp.route('/projetos/autocompletar', methods=['POST'])
def autocompletar():
    """
    Autocompleta campos do projeto com IA (guest mode)
    Reutiliza lógica do project_controller
    """
    logger.info("🤖 Guest - Autocompletando projeto")
    
    try:
        data = request.json
        campos = data.get('campos', [])
        projeto_parcial = data.get('projeto', {})
        
        if not campos:
            return jsonify({'error': True, 'message': 'Nenhum campo selecionado'}), 400
        
        nome = projeto_parcial.get('nome', 'Não informado')
        categoria = projeto_parcial.get('categoria', 'Não informado')
        resumo = projeto_parcial.get('resumo', 'Não informado')
        palavras_chave = projeto_parcial.get('palavras_chave', 'Não informado')
        
        campos_str = ', '.join(campos)
        
        prompt = f"""
        Você é um especialista em projetos científicos para a Bragantec (feira de ciências do IFSP).

        Com base nas informações parciais do projeto abaixo, complete APENAS os seguintes campos: {campos_str}

        **INFORMAÇÕES DO PROJETO:**
        - Título: {nome}
        - Categoria: {categoria}
        - Resumo: {resumo}
        - Palavras-chave: {palavras_chave}

        **INSTRUÇÕES:**
        1. Gere conteúdo profissional, acadêmico e adequado para feira de ciências
        2. Use linguagem científica mas acessível para estudantes de ensino médio
        3. Retorne APENAS um JSON válido no formato:

        {{
          "introducao": "texto da introdução (se solicitado)...",
          "objetivo_geral": "texto do objetivo geral (se solicitado)...",
          "metodologia": "texto da metodologia (se solicitado)...",
          "resultados_esperados": "texto dos resultados (se solicitado)..."
        }}

        **IMPORTANTE**: Inclua APENAS os campos solicitados: {campos_str}
        """
        
        response = gemini.chat(
            prompt,
            tipo_usuario='participante',
            user_id=None
        )
        
        if response.get('error'):
            return jsonify({'error': True, 'message': 'Erro ao autocompletar'}), 500
        
        try:
            conteudo_text = response['response']
            
            if '```json' in conteudo_text:
                conteudo_text = conteudo_text.split('```json')[1].split('```')[0].strip()
            elif '```' in conteudo_text:
                conteudo_text = conteudo_text.split('```')[1].split('```')[0].strip()
            
            conteudo = json.loads(conteudo_text)
            
            return jsonify({
                'success': True,
                'conteudo': conteudo,
                'formato': 'json'
            })
            
        except json.JSONDecodeError:
            return jsonify({
                'success': True,
                'conteudo': {'texto': response['response']},
                'formato': 'texto'
            })
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro guest autocompletar: {traceback.format_exc()}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@guest_bp.route('/projetos/gerar-pdf', methods=['POST'])
def gerar_pdf():
    """
    Gera PDF do projeto (guest mode)
    Recebe dados do projeto via JSON do localStorage
    """
    logger.info("📄 Guest - Gerando PDF do projeto")
    
    try:
        data = request.json
        projeto_data = data.get('projeto', {})
        apelido = data.get('apelido', 'Anônimo')
        
        if not projeto_data.get('nome'):
            return jsonify({'error': True, 'message': 'Nome do projeto é obrigatório'}), 400
        
        # Cria objeto mock de Projeto com atributos necessários
        class ProjetoMock:
            def __init__(self, data):
                self.nome = data.get('nome', '')
                self.categoria = data.get('categoria', '')
                self.resumo = data.get('resumo', '')
                self.palavras_chave = data.get('palavras_chave', '')
                self.introducao = data.get('introducao', '')
                self.objetivo_geral = data.get('objetivo_geral', '')
                self.objetivos_especificos = data.get('objetivos_especificos', [])
                self.metodologia = data.get('metodologia', '')
                self.cronograma = data.get('cronograma', [])
                self.resultados_esperados = data.get('resultados_esperados', '')
                self.referencias_bibliograficas = data.get('referencias_bibliograficas', '')
                self.eh_continuacao = data.get('eh_continuacao', False)
                self.projeto_anterior_titulo = data.get('projeto_anterior_titulo', '')
                self.projeto_anterior_resumo = data.get('projeto_anterior_resumo', '')
                self.projeto_anterior_inicio = data.get('projeto_anterior_inicio')
                self.projeto_anterior_termino = data.get('projeto_anterior_termino')
                self.gerado_por_ia = data.get('gerado_por_ia', False)
        
        # Cria objeto mock de Participante
        class ParticipanteMock:
            def __init__(self, apelido):
                self.nome_completo = apelido or 'Usuário Anônimo'
                self.apelido = apelido
        
        projeto = ProjetoMock(projeto_data)
        participante = ParticipanteMock(apelido)
        
        # Usa BragantecPDFGenerator existente
        pdf_generator = BragantecPDFGenerator(projeto, participante)
        pdf_buffer = pdf_generator.gerar()
        
        # Nome do arquivo
        filename = f"Plano_Pesquisa_{projeto.nome.replace(' ', '_')}_Guest.pdf"
        
        logger.info(f"✅ PDF guest gerado: {filename}")
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro guest PDF: {traceback.format_exc()}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500
