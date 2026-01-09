from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response
from flask_login import login_required, current_user
from functools import wraps
from dao.dao import SupabaseDAO
from config import Config
from services.gemini_stats import gemini_stats  
from utils.advanced_logger import logger
from utils.decorators import admin_required
from utils.helpers import validate_bp, format_bp
from datetime import datetime 
import traceback  
import json


admin_bp = Blueprint('admin', __name__, url_prefix='/admin') # Blueprint para rotas administrativas
# prefixo /admin por exemplo /admin/dashboard, /admin/usuarios, etc...
#o __name__ é usado para o flask indenntificar de onde é o blueprint, por exemplo, o nome desse blueprint sera "controllers.admin_controller"
# porem o nome em si é diferente do __name__,
# o nome dessa blueprint é "admin"
dao = SupabaseDAO()


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard administrativo"""
    usuarios = dao.listar_usuarios()
    tipos_usuario = dao.listar_tipos_usuario()
    
    # Estatísticas
    stats = {
        'total_usuarios': len(usuarios),
        'participantes': len([u for u in usuarios if u.tipo_usuario_id == 2]),
        'orientadores': len([u for u in usuarios if u.tipo_usuario_id == 3]),
        'ia_status': Config.IA_STATUS
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         usuarios=usuarios,
                         tipos_usuario=tipos_usuario)


@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    """Lista de usuários"""
    usuarios = dao.listar_usuarios()
    tipos_usuario = dao.listar_tipos_usuario()
    
    return render_template('admin/usuarios.html', 
                         usuarios=usuarios,
                         tipos_usuario=tipos_usuario)


@admin_bp.route('/adicionar-usuario', methods=['POST']) #rota para adicionar usuario, so aceita post (envio de dados)
@admin_required #so pode acessar se estiver logado como admin (é um decorator, explicarei se der tempo)
def adicionar_usuario():
    """Adiciona novo usuário"""
    try:
        
        data = request.json #recebe os dados em json enviados pelo frontend
        
        nome_completo = data.get('nome_completo')  #pega o nome completo
        email = data.get('email') #pega o email
        senha = data.get('senha') #pega a senha
        tipo_usuario_id = data.get('tipo_usuario_id') #pega o tipo de usuario
        numero_inscricao = data.get('numero_inscricao', '').strip() #pega o numero de inscricao (BP)
        
        if not all([nome_completo, email, senha, tipo_usuario_id]): #verifica se todos os campos obrigatórios foram preenchidos
            return jsonify({ #retorna um json com a mensagem de erro
                'error': True, 
                'message': 'Todos os campos obrigatórios devem ser preenchidos'
            }), 400 #retorna um status code 400 (bad request)
        
        tipo_usuario_id = int(tipo_usuario_id) #converte o ID do tipo de usuario para int
        
        # Valida BP para participantes e orientadores
        if tipo_usuario_id in [2, 3]: #se o tipo de usuario for 2 (participante) ou 3 (orientador)
            if not numero_inscricao: #se nao tiver BP
                return jsonify({ #retorna um json com a mensagem de erro
                    'error': True,
                    'message': 'BP é obrigatório para participantes e orientadores'
                }), 400
            
            if not validate_bp(numero_inscricao): #valida o BP no helpers.py (explicarei se der tempo)
                return jsonify({
                    'error': True,
                    'message': 'BP inválido. Formato correto: BP12345678X (ex: BP123456A)'
                }), 400 #retorna um status code 400 (bad request)
            
            numero_inscricao = format_bp(numero_inscricao) #formata o BP no helpers.py
        else:
            numero_inscricao = format_bp(numero_inscricao) if numero_inscricao else None #formata o BP no helpers.py se for admin e se tiver BP
        
        # Verifica se email já existe
        if dao.buscar_usuario_por_email(email): #verifica se o email ja existe
            return jsonify({
                'error': True,
                'message': 'Email já cadastrado'
            }), 400
        
        # Verifica BP se fornecido
        if numero_inscricao and dao.buscar_usuario_por_bp(numero_inscricao): #verifica se o BP ja existe
            return jsonify({
                'error': True,
                'message': 'BP já cadastrado'
            }), 400
        
        # Cria usuário
        usuario = dao.criar_usuario(
            nome_completo=nome_completo,
            email=email,
            senha=senha,
            tipo_usuario_id=tipo_usuario_id,
            numero_inscricao=numero_inscricao
        )
        
        return jsonify({ #retorna um json com a mensagem de sucesso
            'success': True,
            'message': 'Usuário criado com sucesso',
            'usuario': usuario.to_dict() #retorna o usuario criado em formato de dicionario
        })
        
    except ValueError as ve: #retorna um erro de valor, como valores invalidos.
        #sem ele ao inves de retornar erro 400, ele retorna 500, oq nao é certo
        return jsonify({ 
            'error': True,
            'message': str(ve)
        }), 400
    except Exception as e: # captura qualquer outro erro que possa ocorrer
        return jsonify({
            'error': True,
            'message': f'Erro ao criar usuário: {str(e)}'
        }), 500


@admin_bp.route('/editar-usuario/<int:usuario_id>', methods=['PUT'])
@admin_required
def editar_usuario(usuario_id):
    """Edita dados do usuário"""
    try:
        data = request.json
        
        # Campos editáveis
        campos_permitidos = ['nome_completo', 'email', 'tipo_usuario_id', 'numero_inscricao']
        dados_atualizacao = {k: v for k, v in data.items() if k in campos_permitidos}
        
        if not dados_atualizacao:
            return jsonify({
                'error': True,
                'message': 'Nenhum campo para atualizar'
            }), 400
        
        dao.atualizar_usuario(usuario_id, **dados_atualizacao)
        
        return jsonify({
            'success': True,
            'message': 'Usuário atualizado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao atualizar usuário: {str(e)}'
        }), 500


@admin_bp.route('/deletar-usuario/<int:usuario_id>', methods=['DELETE'])
@admin_required
def deletar_usuario(usuario_id):
    """Deleta usuário"""
    try:
        # Não permite deletar a si mesmo
        if usuario_id == current_user.id:
            return jsonify({
                'error': True,
                'message': 'Você não pode deletar sua própria conta'
            }), 400
        
        dao.deletar_usuario(usuario_id)
        
        return jsonify({
            'success': True,
            'message': 'Usuário deletado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao deletar usuário: {str(e)}'
        }), 500


@admin_bp.route('/toggle-ia', methods=['POST']) #rota para ligar/desligar a IA, so aceita post (envio de dados)
@admin_required #so pode acessar se estiver logado como admin (é um decorator, explicarei se der tempo)
def toggle_ia():
    """Liga/desliga a IA"""
    try:
        Config.IA_STATUS = not Config.IA_STATUS  #  o not inverte o valor, se for True vira False e vice versa, ele pega o valor de config.py
        # nos invertemos o valor por que é como se fosse um interruptor, se for ligado e desligado.
        # ( o config.py, esse nao da tempo de explicar mas basicamente é onde todas as variveis de ambiente e algumas variaveis de configuração estao)
        status = "ativada" if Config.IA_STATUS else "desativada"  # se for True, status = "ativada", se for False, status = "desativada"
        
        return jsonify({ #retorna um json com a mensagem de sucesso
            'success': True,
            'message': f'IA {status} com sucesso',
            'ia_status': Config.IA_STATUS
        })
        
    except Exception as e:
        return jsonify({ #retorna um json com a mensagem de erro
            'error': True,
            'message': f'Erro ao alterar status da IA: {str(e)}'
        }), 500


@admin_bp.route('/configuracoes')
@admin_required
def configuracoes():
    """Página de configurações"""
    import os
    
    # Lista arquivos de contexto
    context_files = []
    context_path = Config.CONTEXT_FILES_PATH
    
    if os.path.exists(context_path):
        for filename in os.listdir(context_path):
            if filename.endswith('.txt'):
                filepath = os.path.join(context_path, filename)
                size = os.path.getsize(filepath)
                context_files.append({
                    'name': filename,
                    'size': f"{size / 1024:.2f} KB"
                })
    
    return render_template('admin/configuracoes.html', 
                         ia_status=Config.IA_STATUS,
                         context_files=context_files)


@admin_bp.route('/gemini-stats')
@admin_required
def gemini_stats_page():
    """
    Página de estatísticas do Gemini API
    """
    return render_template('admin/gemini_stats.html')


@admin_bp.route('/gemini-stats-export')
@admin_required
def gemini_stats_export():
    """
    Exporta estatísticas em JSON
    """
    try:
        # Obtém dados das estatísticas
        global_stats = gemini_stats.get_global_stats()
        all_users_stats = gemini_stats.get_all_users_stats()
        limits_info = gemini_stats.get_limits_info()
        
        # Monta estrutura JSON
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'global': global_stats,
            'limits': limits_info,
            'users': all_users_stats,
            'total_users': len(all_users_stats)
        }
        
        # Converte para JSON string
        json_string = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Gera nome do arquivo
        filename = f'gemini_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # Retorna Response
        return Response(
            json_string,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'application/json; charset=utf-8',
                'Cache-Control': 'no-cache'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar estatísticas: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': True,
            'message': f'Erro ao exportar: {str(e)}'
        }), 500


@admin_bp.route('/gemini-stats-user/<int:user_id>')
@admin_required
def gemini_stats_user(user_id):
    """
    Estatísticas de um usuário específico
    """
    try:
        user_stats = gemini_stats.get_user_stats(user_id)
        
        if user_stats is None:
            return jsonify({
                'error': True,
                'message': 'Usuário não encontrado ou sem estatísticas'
            }), 404
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'stats': user_stats
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500


@admin_bp.route('/gemini-stats-all-users')
@admin_required
def gemini_stats_all_users():
    """
    Estatísticas de todos os usuários
    """
    try:
        all_stats = gemini_stats.get_all_users_stats()
        
        return jsonify({
            'success': True,
            'users': all_stats,
            'total_users': len(all_stats)
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

@admin_bp.route('/gemini-stats-reset/<int:user_id>', methods=['POST'])
@admin_required
def gemini_stats_reset_user(user_id):
    """
    Reseta estatísticas de um usuário
    """
    try:
        gemini_stats.reset_user(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Estatísticas do usuário {user_id} resetadas'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao resetar estatísticas: {str(e)}'
        }), 500


# Importar datetime
from datetime import datetime

# ===== ADICIONAR ESTAS ROTAS NO FINAL DO admin_controller.py =====

@admin_bp.route('/orientacoes')
@admin_required
def orientacoes():
    """
    Página de gerenciamento de orientações
    """
    try:
        # Lista todos orientadores
        usuarios = dao.listar_usuarios()
        orientadores = [u for u in usuarios if u.is_orientador()]
        participantes = [u for u in usuarios if u.is_participante()]
        
        # Lista todos projetos
        projetos = dao.listar_todos_projetos()
        
        # Lista orientações ativas
        orientacoes = dao.listar_orientacoes_completas()
        
        return render_template('admin/orientacoes.html',
                             orientadores=orientadores,
                             participantes=participantes,
                             projetos=projetos,
                             orientacoes=orientacoes)
        
    except Exception as e:
        logger.error(f"Erro ao carregar orientações: {e}")
        flash('Erro ao carregar dados', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/projeto/<int:projeto_id>/participantes')
@admin_required
def projeto_participantes(projeto_id):
    """
    Retorna participantes de um projeto (JSON)
    """
    try:
        participantes = dao.listar_participantes_por_projeto(projeto_id)
        
        return jsonify({
            'success': True,
            'participantes': [p.to_dict() for p in participantes]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar participantes: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@admin_bp.route('/orientacoes/criar', methods=['POST'])
@admin_required
def criar_orientacao():
    """
    Cria associação orientador-projeto
    """
    try:
        data = request.json
        projeto_id = data.get('projeto_id')
        orientador_id = data.get('orientador_id')
        
        if not projeto_id or not orientador_id:
            return jsonify({
                'error': True,
                'message': 'Projeto e orientador são obrigatórios'
            }), 400
        
        # Verifica se já existe
        if dao.verificar_orientacao_existe(orientador_id, projeto_id):
            return jsonify({
                'error': True,
                'message': 'Esta orientação já existe'
            }), 400
        
        # Cria associação
        dao.criar_orientacao(orientador_id, projeto_id)
        
        logger.info(f"✅ Orientação criada: Orientador {orientador_id} -> Projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Orientação criada com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar orientação: {e}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@admin_bp.route('/orientacoes/remover', methods=['DELETE'])
@admin_required
def remover_orientacao():
    """
    Remove associação orientador-projeto
    """
    try:
        data = request.json
        orientador_id = data.get('orientador_id')
        projeto_id = data.get('projeto_id')
        
        if not orientador_id or not projeto_id:
            return jsonify({
                'error': True,
                'message': 'Dados inválidos'
            }), 400
        
        dao.remover_orientacao(orientador_id, projeto_id)
        
        logger.info(f"🗑️ Orientação removida: Orientador {orientador_id} -> Projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Orientação removida!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover orientação: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500
        
@admin_bp.route('/stats-api')
@admin_required
def stats_api():
    """
    API que retorna estatísticas do sistema em tempo real
    """
    try:
        # Conta conversas totais
        chats_result = dao.supabase.table('chats').select('id', count='exact').execute()
        total_chats = chats_result.count if hasattr(chats_result, 'count') else len(chats_result.data)
        
        # Conta mensagens totais
        msgs_result = dao.supabase.table('mensagens').select('id', count='exact').execute()
        total_mensagens = msgs_result.count if hasattr(msgs_result, 'count') else len(msgs_result.data)
        
        # Conta usuários ativos (com chats)
        usuarios_com_chats = dao.supabase.table('chats').select('usuario_id').execute()
        usuarios_unicos = len(set(row['usuario_id'] for row in usuarios_com_chats.data)) if usuarios_com_chats.data else 0
        
        # Conta projetos
        projetos_result = dao.supabase.table('projetos').select('id', count='exact').execute()
        total_projetos = projetos_result.count if hasattr(projetos_result, 'count') else len(projetos_result.data)
        
        # Estatísticas Gemini (últimas 24h)
        gemini_global = gemini_stats.get_global_stats()
        
        return jsonify({
            'success': True,
            'conversas': total_chats,
            'mensagens': total_mensagens,
            'usuarios_ativos': usuarios_unicos,
            'projetos': total_projetos,
            'gemini_requests_24h': gemini_global.get('requests_24h', 0),
            'gemini_tokens_24h': gemini_global.get('tokens_24h', 0),
            'gemini_unique_users': gemini_global.get('unique_users_24h', 0),
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': True,
            'message': str(e)
        }), 500



@admin_bp.route('/test-gemini')
@admin_required
def test_gemini():
    """
    Testa conexão com Gemini API
    """
    try:
        from services.gemini_service import GeminiService
        
        logger.info("🧪 Testando conexão com Gemini...")
        
        gemini = GeminiService()
        
        # Envia mensagem de teste simples
        response = gemini.chat(
            "Teste de conexão. Responda apenas: OK",
            tipo_usuario='participante',
            usar_contexto_bragantec=False,
            usar_pesquisa=False,
            usar_code_execution=False
        )
        
        if response.get('error'):
            logger.error(f"❌ Teste falhou: {response.get('response')}")
            return jsonify({
                'success': False,
                'message': response.get('response', 'Erro desconhecido')
            }), 500
        
        logger.info(f"✅ Teste bem-sucedido: {response.get('response')}")
        
        return jsonify({
            'success': True,
            'message': 'Gemini funcionando corretamente! ✓',
            'response': response.get('response', ''),
            'model': 'gemini-2.5-flash'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar Gemini: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500


@admin_bp.route('/test-db')
@admin_required
def test_db():
    """
    Testa conexão com banco de dados
    """
    try:
        # Tenta fazer uma query simples
        result = dao.supabase.table('usuarios').select('id').limit(1).execute()
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Banco de dados funcionando',
                'rows': len(result.data) if result.data else 0
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhum resultado retornado'
            })
        
    except Exception as e:
        logger.error(f"Erro ao testar DB: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500

@admin_bp.route('/gemini-stats-api')
@admin_required
def gemini_stats_api():
    """
    API JSON para estatísticas do Gemini em tempo real
    """
    try:
        from services.gemini_stats import gemini_stats
        
        logger.info("📊 Buscando estatísticas do Gemini...")
        
        # Pega estatísticas globais (agora com campos agregados)
        global_stats = gemini_stats.get_global_stats()
        logger.debug(f"✅ Global stats: requests_minute={global_stats.get('requests_minute', 0)}, requests_today={global_stats.get('requests_today', 0)}")
        
        # Pega informações de limites
        limits_info = gemini_stats.get_limits_info()
        
        # Calcula uso atual vs limites
        rpm_current = global_stats.get('requests_minute', 0)
        rpm_limit = limits_info['limits']['rpm']
        rpm_percent = int((rpm_current / rpm_limit) * 100) if rpm_limit > 0 else 0
        rpm_remaining = max(0, rpm_limit - rpm_current)
        
        tpm_current = global_stats.get('tokens_minute', 0)
        tpm_limit = limits_info['limits']['tpm']
        tpm_percent = int((tpm_current / tpm_limit) * 100) if tpm_limit > 0 else 0
        tpm_remaining = max(0, tpm_limit - tpm_current)
        
        rpd_current = global_stats.get('requests_today', 0)
        rpd_limit = limits_info['limits']['rpd']
        rpd_percent = int((rpd_current / rpd_limit) * 100) if rpd_limit > 0 else 0
        rpd_remaining = max(0, rpd_limit - rpd_current)
        
        search_current = global_stats.get('searches_today', 0)
        search_limit = limits_info['limits']['google_search_rpd']
        search_percent = int((search_current / search_limit) * 100) if search_limit > 0 else 0
        search_remaining = max(0, search_limit - search_current)
        
        logger.info(f"✅ Estatísticas calculadas - RPM: {rpm_current}/{rpm_limit}, RPD: {rpd_current}/{rpd_limit}")
        
        return jsonify({
            'success': True,
            'global': {
                # RPM
                'requests_minute': rpm_current,
                'rpm_limit': rpm_limit,
                'rpm_percent': rpm_percent,
                'rpm_remaining': rpm_remaining,
                
                # TPM
                'tokens_minute': tpm_current,
                'tpm_limit': tpm_limit,
                'tpm_percent': tpm_percent,
                'tpm_remaining': tpm_remaining,
                
                # RPD
                'requests_today': rpd_current,
                'rpd_limit': rpd_limit,
                'rpd_percent': rpd_percent,
                'rpd_remaining': rpd_remaining,
                
                # Search
                'searches_today': search_current,
                'search_limit': search_limit,
                'search_percent': search_percent,
                'search_remaining': search_remaining,
                
                # Outros
                'unique_users_24h': global_stats.get('unique_users_24h', 0),
                'requests_24h': global_stats.get('requests_24h', 0),
                'tokens_24h': global_stats.get('tokens_24h', 0),
            },
            'limits': limits_info
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas Gemini: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': True,
            'message': str(e)
        }), 500

@admin_bp.route('/participantes-projetos')
@admin_required
def participantes_projetos():
    """
    Página para gerenciar participantes dos projetos
    """
    try:
        # Lista todos os projetos
        projetos = dao.listar_todos_projetos()
        
        # Lista todos os participantes
        usuarios = dao.listar_usuarios()
        participantes = [u for u in usuarios if u.is_participante()]
        
        # Para cada projeto, busca seus participantes
        projetos_com_participantes = []
        for projeto in projetos:
            participantes_do_projeto = dao.listar_participantes_por_projeto(projeto.id)
            projetos_com_participantes.append({
                'projeto': projeto,
                'participantes': participantes_do_projeto
            })
        
        return render_template('admin/participantes_projetos.html',
                             projetos=projetos,
                             participantes=participantes,
                             projetos_com_participantes=projetos_com_participantes)
        
    except Exception as e:
        logger.error(f"Erro ao carregar participantes_projetos: {e}")
        flash('Erro ao carregar dados', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/adicionar-participante-projeto', methods=['POST'])
@admin_required
def adicionar_participante_projeto():
    """
    Adiciona participante a um projeto
    """
    try:
        data = request.json
        projeto_id = data.get('projeto_id')
        participante_id = data.get('participante_id')
        
        if not projeto_id or not participante_id:
            return jsonify({
                'error': True,
                'message': 'Projeto e participante são obrigatórios'
            }), 400
        
        # Verifica se já existe
        result = dao.supabase.table('participantes_projetos')\
            .select('*')\
            .eq('projeto_id', projeto_id)\
            .eq('participante_id', participante_id)\
            .execute()
        
        if result.data:
            return jsonify({
                'error': True,
                'message': 'Participante já está neste projeto'
            }), 400
        
        # Adiciona
        dao.associar_participante_projeto(participante_id, projeto_id)
        
        logger.info(f"✅ Participante {participante_id} adicionado ao projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Participante adicionado ao projeto!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar participante: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@admin_bp.route('/remover-participante-projeto', methods=['DELETE'])
@admin_required
def remover_participante_projeto():
    """
    Remove participante de um projeto
    """
    try:
        data = request.json
        projeto_id = data.get('projeto_id')
        participante_id = data.get('participante_id')
        
        if not projeto_id or not participante_id:
            return jsonify({
                'error': True,
                'message': 'Dados inválidos'
            }), 400
        
        # Remove
        dao.supabase.table('participantes_projetos')\
            .delete()\
            .eq('projeto_id', projeto_id)\
            .eq('participante_id', participante_id)\
            .execute()
        
        logger.info(f"🗑️ Participante {participante_id} removido do projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Participante removido!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover participante: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500