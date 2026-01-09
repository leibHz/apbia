"""
Sistema de Sessão Única para APBIA
Impede que a mesma conta seja acessada simultaneamente de múltiplos dispositivos
"""

import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user, logout_user
from utils.advanced_logger import logger
from utils.decorators import require_valid_session #só por precaução

class SessionManager:
    """Gerencia sessões únicas por usuário"""
    
    def __init__(self, dao):
        self.dao = dao
        self.session_timeout = timedelta(hours=1)  # Timeout de 1 hora
    
    def generate_session_token(self):
        """Gera token único de sessão"""
        return secrets.token_urlsafe(32)
    
    def create_session(self, user_id):
        """
        Cria nova sessão para usuário
        Invalida sessões anteriores
        """
        token = self.generate_session_token()
        now = datetime.now(timezone.utc)  # UTC timezone
        
        logger.info(f"🔑 Criando nova sessão para User {user_id}")
        
        # Atualiza token na tabela de usuários
        self.dao.supabase.table('usuarios').update({
            'session_token': token,
            'session_created_at': now.isoformat(),
            'last_activity': now.isoformat()
        }).eq('id', user_id).execute()
        
        # Armazena token na sessão Flask
        session['session_token'] = token
        session.permanent = True
        
        logger.info(f"✅ Sessão criada com sucesso - Token: {token[:10]}...")
        
        return token
    
    def validate_session(self, user_id, update_activity=True):
        """
        Valida se sessão atual é a única ativa e verifica inatividade
        """
        if not user_id:
            logger.warning("⚠️ validate_session: user_id é None")
            return False
    
        # Busca token atual da sessão Flask
        current_token = session.get('session_token')
    
        if not current_token:
            logger.warning(f"⚠️ User {user_id}: Sem session_token na sessão Flask")
            return False
    
        logger.debug(f"🔍 Validando sessão - User {user_id} | Token Flask: {current_token[:10]}...")
    
        # Busca dados do banco
        result = self.dao.supabase.table('usuarios')\
            .select('session_token, session_created_at, last_activity')\
            .eq('id', user_id)\
            .execute()
    
        if not result.data:
            logger.error(f"❌ User {user_id} não encontrado no banco")
            return False
    
        user_data = result.data[0]
        stored_token = user_data.get('session_token')
        session_created = user_data.get('session_created_at')
        last_activity = user_data.get('last_activity')
    
        logger.debug(f"📊 Dados do banco - Token DB: {stored_token[:10] if stored_token else 'None'}... | Created: {session_created} | Last Activity: {last_activity}")
    
        # Verifica se tokens coincidem (detecta login em outro dispositivo)
        if current_token != stored_token:
            logger.warning(f"🚫 SESSÃO INVÁLIDA - User {user_id}: Token não coincide (outro dispositivo fez login)")
            logger.debug(f"   Token Flask: {current_token[:15]}...")
            logger.debug(f"   Token DB:    {stored_token[:15] if stored_token else 'None'}...")
            return False
    
        # Verifica inatividade de 1 hora
        if last_activity:
            try:
                last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                now_utc = datetime.now(timezone.utc)
                inactivity_duration = now_utc - last_activity_dt
            
                logger.debug(f"⏱️  Inatividade: {inactivity_duration.total_seconds() / 60:.1f} minutos")
            
                if inactivity_duration > self.session_timeout:
                    logger.warning(f"💤 SESSÃO EXPIRADA - User {user_id}: Inatividade > 1 hora ({inactivity_duration.total_seconds() / 3600:.2f}h)")
                    return False
            except Exception as e:
                logger.error(f"❌ Erro ao verificar inatividade - User {user_id}: {e}")
    
        # Só atualiza se não for polling
        if update_activity:
            self.update_activity(user_id)
            logger.debug(f"✅ Sessão válida - User {user_id} | Atividade atualizada")
        else:
            logger.debug(f"✅ Sessão válida - User {user_id} | Atividade NÃO atualizada (polling)")
    
        return True
    
    def update_activity(self, user_id):
        """Atualiza timestamp de última atividade"""
        now = datetime.now(timezone.utc)  # UTC timezone
        self.dao.supabase.table('usuarios').update({
            'last_activity': now.isoformat()
        }).eq('id', user_id).execute()
        logger.debug(f"🔄 Atividade atualizada - User {user_id}: {now.isoformat()}")
    
    def invalidate_session(self, user_id):
        """Invalida sessão de um usuário"""
        logger.info(f"🗑️  Invalidando sessão - User {user_id}")
        self.dao.supabase.table('usuarios').update({
            'session_token': None,
            'session_created_at': None
        }).eq('id', user_id).execute()
        
        if 'session_token' in session:
            session.pop('session_token')
        
        logger.info(f"✅ Sessão invalidada - User {user_id}")

# Instância global
_session_manager = None

def get_session_manager():
    """Retorna instância global do SessionManager"""
    global _session_manager
    if _session_manager is None:
        from dao.dao import SupabaseDAO
        dao = SupabaseDAO()
        _session_manager = SessionManager(dao)
    return _session_manager