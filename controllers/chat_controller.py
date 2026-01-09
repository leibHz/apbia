from flask import Blueprint, render_template, request, jsonify, session, send_file
from flask_login import login_required, current_user
from dao.dao import SupabaseDAO
from services.gemini_service import GeminiService
from config import Config
from werkzeug.utils import secure_filename
import os
import uuid
import mimetypes
from datetime import datetime
from utils.rate_limiter import rate_limiter
from utils.advanced_logger import logger
from utils.helpers import generate_chat_title, detect_mime_type, save_uploaded_file, get_file_extension

chat_bp = Blueprint('chat', __name__)
# sem prefixo, rotas como /chat/, /chat/send, etc.
# o __name__ desse blueprint sera "controllers.chat_controller"
# o nome sera "chat"

dao = SupabaseDAO()
gemini = GeminiService()

# Diretório para arquivos permanentes
CHAT_FILES_DIR = os.path.join(Config.UPLOAD_FOLDER, 'chat_files')
os.makedirs(CHAT_FILES_DIR, exist_ok=True)

@chat_bp.route('/')
@login_required
def index():
    """Página principal do chat"""
    if not Config.IA_STATUS:
        return render_template('chat.html', ia_offline=True)
    
    chats = dao.listar_chats_por_usuario(current_user.id)
    
    tipo_usuario = 'participante' if current_user.is_participante() else \
                   'orientador' if current_user.is_orientador() else None
    
    return render_template('chat.html', 
                         chats=chats, 
                         tipo_usuario=tipo_usuario,
                         ia_offline=False)


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Endpoint para enviar mensagens"""
    if not Config.IA_STATUS:
        return jsonify({
            'error': True,
            'message': 'IA está temporariamente offline.'
        }), 503

    # Verifica rate limit
    can_proceed, error_msg = rate_limiter.check_limit(current_user.id)

    if not can_proceed:
        return jsonify({
            'error': True,
            'message': error_msg
        }), 429

    data = request.json
    message = data.get('message', '')
    chat_id = data.get('chat_id')
    usar_pesquisa = data.get('usar_pesquisa', True)
    usar_code_execution = data.get('usar_code_execution', True)
    analyze_url = data.get('url')
    usar_contexto_bragantec = data.get('usar_contexto_bragantec', False)

    if not message:
        return jsonify({'error': True, 'message': 'Mensagem vazia'}), 400

    try:
        tipo_usuario = None
        # Tipo de usuário
        if current_user.is_participante():
            tipo_usuario = 'participante'
        elif current_user.is_orientador():
            tipo_usuario = 'orientador'
        elif current_user.is_admin(): 
            tipo_usuario = 'administrador'

        # Cria chat se não existir
        if not chat_id:
            tipo_ia_id = 2 if current_user.is_participante() else \
                        3 if current_user.is_orientador() else 1

            titulo = generate_chat_title(message)

            chat = dao.criar_chat(current_user.id, tipo_ia_id, titulo)
            chat_id = chat.id

        # Contexto de projetos
        projetos = dao.listar_projetos_por_usuario(current_user.id)
        contexto_projetos = ""

        if projetos:
            contexto_projetos = "\n\n=== SEUS PROJETOS ===\n"
            for projeto in projetos:
                contexto_projetos += f"""
                Projeto: {projeto.nome}
                Categoria: {projeto.categoria}
                Status: {projeto.status}
                Resumo: {projeto.resumo or 'Não informado'}
                ---
                """

        elif current_user.is_orientador():
            # Busca orientados
            orientados = dao.listar_orientados_por_orientador(current_user.id)
            
            if orientados:
                contexto_projetos = "\n\n=== SEUS ORIENTADOS ===\n"
                for orientado in orientados:
                    contexto_projetos += f"""
                    Orientado: {orientado.get('nome_completo')}
                    Email: {orientado.get('email')}
                    BP: {orientado.get('numero_inscricao', 'Não informado')}
                    """

            projetos_orientador = dao.listar_projetos_por_orientador(current_user.id)

            if projetos_orientador:
                contexto_projetos += "\n\n=== PROJETOS QUE VOCÊ ESTÁ ORIENTANDO ===\n"
                for projeto in projetos_orientador:
                    # Busca participantes do projeto
                    participantes = dao.listar_participantes_por_projeto(projeto.id)
                    participantes_nomes = [p.nome_completo for p in participantes]
                    
                    contexto_projetos += f"""
                    Projeto: {projeto.nome}
                    Categoria: {projeto.categoria}
                    Status: {projeto.status}
                    Participantes: {', '.join(participantes_nomes) if participantes_nomes else 'Nenhum'}
                    Resumo: {projeto.resumo or 'Não informado'}
                    ---
"""
        

        # Carrega histórico
        mensagens_db = dao.obter_ultimas_n_mensagens(chat_id, n=20)
        arquivos_db = dao.listar_arquivos_por_chat(chat_id)

        history = []
        
        # Monta histórico
        for msg in mensagens_db:
            history.append({
                'role': msg['role'],
                'parts': [msg['conteudo']]
            })

        # Mensagem com contexto
        message_com_contexto = f"{contexto_projetos}\n\n{message}"
        
        apelido = current_user.apelido if hasattr(current_user, 'apelido') else None

        # Chama Gemini COM MODO BRAGANTEC
        response = gemini.chat(
            message_com_contexto,
            tipo_usuario=tipo_usuario,
            history=history,
            usar_pesquisa=usar_pesquisa,
            usar_code_execution=usar_code_execution,
            analyze_url=analyze_url,
            usar_contexto_bragantec=usar_contexto_bragantec,
            user_id=current_user.id,
            apelido=apelido
        )

        # Extrai contagem de tokens
        tokens_input = response.get('tokens_input', 0)
        tokens_output = response.get('tokens_output', 0)

        # Log de consumo
        if tokens_input or tokens_output:
            logger.info(f"📊 Tokens - Input: {tokens_input:,} | Output: {tokens_output:,}")
            
            if tokens_input > 100000:
                logger.warning(f"⚠️ ALTO CONSUMO DE INPUT: {tokens_input:,} tokens!")

        if response.get('error'):
            return jsonify({
                'error': True,
                'message': response['response']
            }), 500

        # Salva mensagem do usuário
        dao.criar_mensagem(chat_id, 'user', message)

        # Salva resposta da IA
        msg_assistant_id = dao.criar_mensagem(
            chat_id,
            'model',
            response['response'],
            thinking_process=response.get('thinking_process')
        )

        # Salva informações sobre ferramentas usadas
        if msg_assistant_id:
            ferramentas_usadas = {
                'google_search': response.get('search_used', False),
                'contexto_bragantec': usar_contexto_bragantec,
                'code_execution': response.get('code_executed', False),
                'url_context': bool(analyze_url)
            }
            
            dao.salvar_ferramenta_usada(msg_assistant_id['id'], ferramentas_usadas)

        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'chat_id': chat_id,
            'search_used': response.get('search_used', False),
            'code_executed': response.get('code_executed', False),
            'code_results': response.get('code_results'),
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'total_tokens': tokens_input + tokens_output
        })

    except Exception as e:
        import traceback
        print(f"❌ Erro: {traceback.format_exc()}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/upload-file', methods=['POST'])
@login_required
def upload_file():
    """
    Upload com MIME type manual + mensagem customizável
    """
    if not Config.IA_STATUS:
        return jsonify({'error': True, 'message': 'IA offline'}), 503
    
    if 'file' not in request.files:
        return jsonify({'error': True, 'message': 'Nenhum arquivo'}), 400
    
    file = request.files['file']
    message = request.form.get('message', 'Analise este arquivo')
    chat_id = request.form.get('chat_id')
    
    if file.filename == '':
        return jsonify({'error': True, 'message': 'Arquivo inválido'}), 400
    
    # Validação de tamanho
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > Config.MAX_CONTENT_LENGTH:
            return jsonify({
                'error': True,
                'message': f'Arquivo muito grande. Máximo: {Config.MAX_CONTENT_LENGTH/(1024*1024):.0f}MB'
            }), 400
    
    try:
        # 1. Salva arquivo TEMPORÁRIO
        temp_filename = secure_filename(file.filename)
        temp_path = os.path.join(Config.UPLOAD_FOLDER, f"temp_{uuid.uuid4()}_{temp_filename}")
        file.save(temp_path)
        
        mime_type = detect_mime_type(temp_filename, file.content_type)
        logger.info(f"📋 MIME type detectado: {mime_type}")
        
        tipo_usuario = 'participante' if current_user.is_participante() else \
                       'orientador' if current_user.is_orientador() else \
                       'administrador' if current_user.is_admin() else None
        
        # Processa arquivo com Gemini 
        logger.info(f"📁 Processando arquivo: {temp_filename}")
        
        response = gemini.chat_with_file(
            message, 
            temp_path, 
            tipo_usuario,
            user_id=current_user.id,
            keep_file_on_gemini=True,
            mime_type=mime_type 
        )
        
        gemini_file_uri = response.get('gemini_file_uri')
        
        # 3. Salva arquivo PERMANENTEMENTE
        file.seek(0)
        CHAT_FILES_DIR = os.path.join(Config.UPLOAD_FOLDER, 'chat_files')
        file_info = save_uploaded_file(file, CHAT_FILES_DIR, current_user.id, subfolder=chat_id or 0)
        
        # 4. Remove arquivo temporário
        try:
            os.remove(temp_path)
        except:
            pass
        
        # 5. Salva no banco
        if chat_id:
            arquivo_id = dao.criar_arquivo_chat(
                chat_id=int(chat_id),
                nome_arquivo=file_info['filename'],
                url_arquivo=file_info['filepath'],
                tipo_arquivo=file_info['mime_type'],
                tamanho_bytes=file_info['size'],
                gemini_file_uri=gemini_file_uri
            )
            
            # 6. Salva mensagens
            msg_user = dao.criar_mensagem(
                chat_id, 
                'user', 
                f'📎 {message} (arquivo: {file_info["filename"]})'
            )
            
            msg_assistant = dao.criar_mensagem(
                chat_id, 
                'model', 
                response['response'],
                thinking_process=response.get('thinking_process')
            )
            
            # 7. Associa arquivo à mensagem
            dao.associar_arquivo_mensagem(arquivo_id, msg_user['id'])
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'file_type': response.get('file_type'),
            'file_info': {
                'name': file_info['filename'],
                'size': file_info['size'],
                'type': file_info['mime_type'],
                'url': f"/chat/file/{arquivo_id}" if chat_id else None
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Erro: {traceback.format_exc()}")
        
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


@chat_bp.route('/file/<int:arquivo_id>')
@login_required
def serve_file(arquivo_id):
    """Serve arquivo salvo do chat"""
    try:
        arquivo = dao.buscar_arquivo_por_id(arquivo_id)
        
        if not arquivo:
            return jsonify({'error': True, 'message': 'Arquivo não encontrado'}), 404
        
        # Verifica permissão
        chat = dao.buscar_chat_por_id(arquivo['chat_id'])
        if chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Acesso negado'}), 403
        
        file_path = os.path.join(Config.UPLOAD_FOLDER, arquivo['url_arquivo'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': True, 'message': 'Arquivo físico não encontrado'}), 404
        
        return send_file(
            file_path,
            mimetype=arquivo['tipo_arquivo'],
            as_attachment=False,
            download_name=arquivo['nome_arquivo']
        )
        
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500


@chat_bp.route('/load-history/<int:chat_id>', methods=['GET'])
@login_required
def load_history(chat_id):
    """Carrega histórico"""
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        mensagens = dao.listar_mensagens_por_chat(chat_id)
        arquivos = dao.listar_arquivos_por_chat(chat_id)
        
        # Busca notas gerais do chat
        chat_completo = dao.supabase.table('chats')\
            .select('notas_orientador')\
            .eq('id', chat_id)\
            .execute()
        
        notas_gerais_chat = chat_completo.data[0]['notas_orientador'] if chat_completo.data else None
        
        # Enriquece mensagens com arquivos      
        for msg in mensagens:
            # Busca notas desta mensagem e formata para o frontend
            notas_raw = msg.get('notas_orientador', [])
            msg['notas'] = []
            
            # Formata cada nota para o formato esperado pelo JavaScript
            if notas_raw:
                for nota in notas_raw:
                    msg['notas'].append({
                        'nota': nota.get('nota'),
                        'data_criacao': nota.get('data_criacao'),
                        'orientador_nome': nota.get('usuarios', {}).get('nome_completo', 'Orientador') if nota.get('usuarios') else 'Orientador'
                    })
            
            msg_id = msg.get('id')
            
            # Adiciona arquivo se houver
            arquivo = next(
                (arq for arq in arquivos if arq.get('mensagem_id') == msg_id),
                None
            )
            
            if arquivo:
                msg['arquivo'] = {
                    'id': arquivo['id'],
                    'nome': arquivo['nome_arquivo'],
                    'tipo': arquivo['tipo_arquivo'],
                    'tamanho': arquivo['tamanho_bytes'],
                    'url': f"/chat/file/{arquivo['id']}"
                }
        
        # Retorna também as notas gerais do chat
        return jsonify({
            'success': True,
            'mensagens': mensagens,
            'arquivos': arquivos,
            'chat': chat.to_dict(),
            'notas_gerais': notas_gerais_chat
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar histórico: {e}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500

@chat_bp.route('/new-chat', methods=['POST'])
@login_required
def new_chat():
    """Cria um novo chat"""
    data = request.json # pega o json enviado pelo frontend
    titulo = data.get('titulo', 'Nova conversa') # pega o titulo do json e se nao houver titulo, coloca 'Nova conversa'
    
    try: 
        tipo_ia_id = 2 if current_user.is_participante() else \
                     3 if current_user.is_orientador() else 1 # define o tipo de IA, sendo 1 tipo personalizado pra cada tipo de usuario
        
        chat = dao.criar_chat(current_user.id, tipo_ia_id, titulo) # cria o chat
        
        return jsonify({
            'success': True,
            'chat': chat.to_dict() # retorna o chat criado em forma de dicionario
        })
        
    except Exception as e: # se houver erro
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/delete-chat/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Deleta chat E seus arquivos"""
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        # 1. Busca arquivos
        arquivos = dao.listar_arquivos_por_chat(chat_id)
        
        # 2. Deleta físicos
        for arquivo in arquivos:
            file_path = os.path.join(Config.UPLOAD_FOLDER, arquivo['url_arquivo'])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao deletar arquivo: {e}")
        
        # 3. Deleta chat (CASCADE)
        dao.deletar_chat(chat_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/count-tokens', methods=['POST'])
@login_required
def count_tokens():
    """Conta tokens de uma mensagem"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'tokens': 0})
    
    try:
        tokens = gemini.count_tokens(text)
        return jsonify({
            'success': True,
            'tokens': tokens,
            'within_limit': tokens <= 1000000
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500