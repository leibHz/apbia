"""
Decorators para controle de acesso e utilitários
"""

from functools import wraps
from flask import redirect, url_for, flash, request, jsonify, abort, session
from flask_login import current_user, logout_user
from collections import defaultdict
from time import time



def login_required_json(f):
    """
    Decorator para rotas JSON que requerem autenticação
    Retorna JSON ao invés de redirecionar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': True, 'message': 'Autenticação necessária'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator que permite acesso apenas para administradores
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin():
            flash('Acesso negado. Apenas administradores.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def participante_required(f):
    """
    Decorator que permite acesso apenas para participantes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_participante():
            flash('Acesso apenas para participantes.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function



def orientador_required(f):
    """
    Decorator que permite acesso apenas para orientadores
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_orientador():
            flash('Acesso apenas para orientadores.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def check_ia_status(f):
    """
    Decorator que verifica se a IA está ativa antes de processar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from config import Config
        
        if not Config.IA_STATUS:
            if request.is_json:
                return jsonify({
                    'error': True,
                    'message': 'IA está temporariamente offline. Contate o administrador.'
                }), 503
            else:
                flash('A IA está temporariamente desativada.', 'warning')
                return redirect(url_for('chat.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(max_calls=10, period=60):
    """
    Decorator simples de rate limiting
    """
    
    calls = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return f(*args, **kwargs)
            
            user_id = current_user.id
            now = time()
            
            # Remove chamadas antigas
            calls[user_id] = [call_time for call_time in calls[user_id] 
                             if now - call_time < period]
            
            # Verifica limite
            if len(calls[user_id]) >= max_calls:
                if request.is_json:
                    return jsonify({
                        'error': True,
                        'message': 'Muitas requisições. Aguarde um momento.'
                    }), 429
                else:
                    flash('Muitas requisições. Por favor, aguarde.', 'warning')
                    return redirect(request.referrer or url_for('index'))
            
            # Adiciona nova chamada
            calls[user_id].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_valid_session(f):
    """
    Decorator que verifica validade da sessão
    Faz logout automático se sessão inválida
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # Importa aqui para evitar circular import
        from dao.dao import SupabaseDAO
        from utils.session_manager import SessionManager
        dao = SupabaseDAO()
        session_manager = SessionManager(dao)
        
        # Valida sessão
        if not session_manager.validate_session(current_user.id):
            logout_user()
            session.clear()
            flash('⚠️ Sua conta foi acessada de outro dispositivo ou ficou inativa por mais de 1 hora.', 'warning')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def bloquear_orientador_criar_projeto(f):
    """
    Impede que orientadores acessem rotas de criação de projetos
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_orientador():
            # Se for JSON request
            if request.is_json:
                return jsonify({
                    'error': True,
                    'message': 'Orientadores não podem criar projetos. Você pode apenas editar projetos dos seus orientados.'
                }), 403
            # Se for página web
            else:
                abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function