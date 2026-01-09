from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from dao.dao import SupabaseDAO
from utils.advanced_logger import logger
from utils.decorators import orientador_required
from datetime import datetime

orientador_bp = Blueprint('orientador', __name__, url_prefix='/orientador')
# prefixo /orientador por exemplo /orientador/dashboard, /orientador/orientado/<id>, etc...
# o __name__ será controllers.orientador_controller
# o nome sera "orientador"
dao = SupabaseDAO()


@orientador_bp.route('/dashboard')
@orientador_required
def dashboard():
    """Dashboard do orientador com seus orientados"""
    logger.info(f"📊 Orientador {current_user.nome_completo} acessando dashboard")
    
    # Busca orientados
    orientados = dao.listar_orientados_por_orientador(current_user.id)
    
    # Estatísticas
    stats = {
        'total_orientados': len(orientados),
        'total_chats': sum(len(o.get('chats', [])) for o in orientados),
        'chats_com_notas': dao.contar_chats_com_notas(current_user.id),
    }
    
    return render_template('orientador/dashboard.html', 
                         orientados=orientados,
                         stats=stats)


@orientador_bp.route('/orientado/<int:participante_id>')
@orientador_required
def visualizar_orientado(participante_id):
    """Visualiza detalhes e chats de um orientado específico"""
    
    # Verifica se é realmente seu orientado
    if not dao.verificar_orientador_participante(current_user.id, participante_id):
        flash('Este não é seu orientado.', 'error')
        return redirect(url_for('orientador.dashboard'))
    
    # Busca dados do orientado
    orientado = dao.buscar_usuario_por_id(participante_id)
    if not orientado:
        flash('Orientado não encontrado.', 'error')
        return redirect(url_for('orientador.dashboard'))
    
    # Busca chats do orientado
    chats = dao.listar_chats_por_usuario(participante_id)
    
    # Busca projetos do orientado
    projetos = dao.listar_projetos_por_usuario(participante_id)
    
    return render_template('orientador/visualizar_orientado.html',
                         orientado=orientado,
                         chats=chats,
                         projetos=projetos)


@orientador_bp.route('/chat/<int:chat_id>')
@orientador_required
def visualizar_chat(chat_id):
    """
    Visualiza histórico completo de um chat
    COM informações sobre ferramentas usadas
    """
    
    # Busca chat
    chat = dao.buscar_chat_por_id(chat_id)
    if not chat:
        flash('Chat não encontrado.', 'error')
        return redirect(url_for('orientador.dashboard'))
    
    # Verifica se é orientado
    if not dao.verificar_orientador_participante(current_user.id, chat.usuario_id):
        flash('Acesso negado. Este não é seu orientado.', 'error')
        return redirect(url_for('orientador.dashboard'))
    
    # Busca mensagens COM metadados de ferramentas
    mensagens = dao.listar_mensagens_por_chat(chat_id)
    
    # Busca arquivos do chat
    arquivos = dao.listar_arquivos_por_chat(chat_id)
    
    # Enriquece mensagens com:
    # - Notas do orientador
    # - Ferramentas usadas
    # - Arquivos anexados
    for msg in mensagens:
        msg_id = msg.get('id')
        
        # Busca notas desta mensagem
        msg['notas'] = dao.listar_notas_por_mensagem(msg_id)
        
        # Identifica ferramentas usadas (salvas na coluna ferramenta_usada)
        ferramenta_usada = msg.get('ferramenta_usada')
        if ferramenta_usada:
            # Parse do JSON se necessário
            import json
            try:
                msg['ferramentas'] = json.loads(ferramenta_usada) if isinstance(ferramenta_usada, str) else ferramenta_usada
            except:
                msg['ferramentas'] = {'raw': ferramenta_usada}
        
        # Busca arquivo anexado
        arquivo = next((arq for arq in arquivos if arq.get('mensagem_id') == msg_id), None)
        if arquivo:
            msg['arquivo'] = arquivo
    
    # Busca dados do orientado
    orientado = dao.buscar_usuario_por_id(chat.usuario_id)
    
    # registra visualização COM chat_id
    dao.registrar_visualizacao_orientador(current_user.id, chat_id)
    
    return render_template('orientador/visualizar_chat.html',
                         chat=chat,
                         mensagens=mensagens,
                         orientado=orientado)


@orientador_bp.route('/adicionar-nota', methods=['POST'])
@orientador_required
def adicionar_nota():
    """
    Adiciona nota do orientador em uma resposta da IA
    """
    try:
        data = request.json
        mensagem_id = data.get('mensagem_id')
        nota = data.get('nota', '').strip()
        
        if not mensagem_id or not nota:
            return jsonify({
                'error': True,
                'message': 'Mensagem e nota são obrigatórios'
            }), 400
        
        # Verifica se a mensagem existe
        mensagem = dao.buscar_mensagem_por_id(mensagem_id)
        if not mensagem:
            return jsonify({
                'error': True,
                'message': 'Mensagem não encontrada'
            }), 404
        
        # Verifica se o chat pertence a um orientado
        chat = dao.buscar_chat_por_id(mensagem['chat_id'])
        if not dao.verificar_orientador_participante(current_user.id, chat.usuario_id):
            return jsonify({
                'error': True,
                'message': 'Acesso negado'
            }), 403
        
        # Cria nota
        nota_obj = dao.criar_nota_orientador(
            mensagem_id=mensagem_id,
            orientador_id=current_user.id,
            nota=nota
        )
        
        logger.info(f"📝 Orientador {current_user.nome_completo} adicionou nota na mensagem {mensagem_id}")
        
        return jsonify({
            'success': True,
            'message': 'Nota adicionada com sucesso',
            'nota': {
                'id': nota_obj['id'],
                'nota': nota_obj['nota'],
                'data_criacao': nota_obj['data_criacao'],
                'orientador': current_user.nome_completo
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar nota: {e}")
        return jsonify({
            'error': True,
            'message': f'Erro ao adicionar nota: {str(e)}'
        }), 500


@orientador_bp.route('/editar-nota/<int:nota_id>', methods=['PUT'])
@orientador_required
def editar_nota(nota_id):
    """Edita nota existente"""
    try:
        data = request.json
        nova_nota = data.get('nota', '').strip()
        
        if not nova_nota:
            return jsonify({'error': True, 'message': 'Nota não pode ser vazia'}), 400
        
        # Busca nota
        nota = dao.buscar_nota_por_id(nota_id)
        if not nota:
            return jsonify({'error': True, 'message': 'Nota não encontrada'}), 404
        
        # Verifica se é o dono da nota
        if nota['orientador_id'] != current_user.id:
            return jsonify({'error': True, 'message': 'Acesso negado'}), 403
        
        # Atualiza
        dao.atualizar_nota_orientador(nota_id, nova_nota)
        
        return jsonify({
            'success': True,
            'message': 'Nota atualizada'
        })
        
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500


@orientador_bp.route('/deletar-nota/<int:nota_id>', methods=['DELETE'])
@orientador_required
def deletar_nota(nota_id):
    """Deleta nota"""
    try:
        # Busca nota
        nota = dao.buscar_nota_por_id(nota_id)
        if not nota:
            return jsonify({'error': True, 'message': 'Nota não encontrada'}), 404
        
        # Verifica se é o dono
        if nota['orientador_id'] != current_user.id:
            return jsonify({'error': True, 'message': 'Acesso negado'}), 403
        
        # Deleta
        dao.deletar_nota_orientador(nota_id)
        
        return jsonify({'success': True, 'message': 'Nota deletada'})
        
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500


@orientador_bp.route('/chat/<int:chat_id>/notas', methods=['POST'])
@orientador_required
def salvar_notas_chat(chat_id):
    """
    Salva notas do orientador para um chat específico
    """
    try:
        data = request.json
        notas = data.get('notas', '').strip()
        
        # Busca chat
        chat = dao.buscar_chat_por_id(chat_id)
        if not chat:
            return jsonify({
                'error': True,
                'message': 'Chat não encontrado'
            }), 404
        
        # Verifica se o chat pertence a um orientado
        if not dao.verificar_orientador_participante(current_user.id, chat.usuario_id):
            return jsonify({
                'error': True,
                'message': 'Acesso negado'
            }), 403
        
        # Atualiza as notas do chat
        dao.atualizar_notas_chat(chat_id, notas)
        
        logger.info(f"📝 Orientador {current_user.nome_completo} atualizou notas do chat {chat_id}")
        
        return jsonify({
            'success': True,
            'message': 'Notas salvas com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar notas do chat: {e}")
        return jsonify({
            'error': True,
            'message': f'Erro ao salvar notas: {str(e)}'
        }), 500


@orientador_bp.route('/relatorio/<int:participante_id>')
@orientador_required
def gerar_relatorio(participante_id):
    """
    Gera relatório completo de acompanhamento do orientado
    """
    
    # Verifica se é seu orientado
    if not dao.verificar_orientador_participante(current_user.id, participante_id):
        flash('Acesso negado.', 'error')
        return redirect(url_for('orientador.dashboard'))
    
    # Busca dados completos
    orientado = dao.buscar_usuario_por_id(participante_id)
    chats = dao.listar_chats_por_usuario(participante_id)
    projetos = dao.listar_projetos_por_usuario(participante_id)
    
    # Estatísticas de uso
    stats = {
        'total_conversas': len(chats),
        'total_mensagens': sum(dao.contar_mensagens_por_chat(c.id) for c in chats),
        'total_projetos': len(projetos),
        'uso_google_search': dao.contar_uso_ferramenta(participante_id, 'google_search'),
        'uso_modo_bragantec': dao.contar_uso_ferramenta(participante_id, 'contexto_bragantec'),
        'total_notas_orientador': dao.contar_notas_por_orientado(participante_id, current_user.id)
    }
    
    # Busca observações do orientador (se houver)
    try:
        obs_result = dao.supabase.table('observacoes_orientador')\
            .select('observacoes')\
            .eq('orientador_id', current_user.id)\
            .eq('participante_id', participante_id)\
            .execute()
        
        observacoes = obs_result.data[0]['observacoes'] if obs_result.data else ''
    except:
        observacoes = ''
    
    return render_template('orientador/relatorio.html',
                         orientado=orientado,
                         chats=chats,
                         projetos=projetos,
                         stats=stats,
                         observacoes=observacoes,
                         data_geracao=datetime.now())


@orientador_bp.route('/salvar-observacoes', methods=['POST'])
@orientador_required
def salvar_observacoes():
    """
    Salva observações do orientador sobre um orientado
    """
    try:
        data = request.json
        participante_id = data.get('participante_id')
        observacoes = data.get('observacoes', '').strip()
        
        if not participante_id:
            return jsonify({
                'error': True,
                'message': 'Participante não especificado'
            }), 400
        
        # Verifica se é orientado
        if not dao.verificar_orientador_participante(current_user.id, participante_id):
            return jsonify({
                'error': True,
                'message': 'Acesso negado'
            }), 403
        
        # Verifica se já existe registro
        result = dao.supabase.table('observacoes_orientador')\
            .select('*')\
            .eq('orientador_id', current_user.id)\
            .eq('participante_id', participante_id)\
            .execute()
        
        if result.data:
            # Atualiza
            dao.supabase.table('observacoes_orientador')\
                .update({'observacoes': observacoes})\
                .eq('orientador_id', current_user.id)\
                .eq('participante_id', participante_id)\
                .execute()
        else:
            # Cria novo
            dao.supabase.table('observacoes_orientador')\
                .insert({
                    'orientador_id': current_user.id,
                    'participante_id': participante_id,
                    'observacoes': observacoes
                })\
                .execute()
        
        logger.info(f"📝 Observações salvas: Orientador {current_user.id} -> Participante {participante_id}")
        
        return jsonify({
            'success': True,
            'message': 'Observações salvas com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar observações: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500