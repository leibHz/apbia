"""
Sistema de Debug Avançado para APBIA
Logging detalhado de todas as operações do sistema
"""

import logging
import sys
import json
from datetime import datetime
from functools import wraps
from flask import request, g
import time
import traceback
from colorama import Fore, Back, Style, init
from flask_login import current_user

# Inicializa colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Formatter colorido para melhor visualização no terminal"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }
    
    def format(self, record):
        # Adiciona cor ao nível
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        
        # Adiciona timestamps coloridos
        record.asctime = f"{Fore.BLUE}{self.formatTime(record)}{Style.RESET_ALL}"
        
        return super().format(record)


class APBIALogger:
    """Logger customizado para APBIA"""
    
    def __init__(self, name='APBIA'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove handlers existentes
        self.logger.handlers = []
        
        # Handler para console (colorido)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Formato detalhado
        formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # Handler para arquivo (logs persistentes)
        try:
            file_handler = logging.FileHandler('apbia_debug.log', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"⚠️ Erro ao criar arquivo de log: {e}")
    
    def debug(self, message, **kwargs):
        """Log de debug com dados extras"""
        self._log_('DEBUG', message, **kwargs)
    
    def info(self, message, **kwargs):
        """Log de informação"""
        self._log_('INFO', message, **kwargs)
    
    def warning(self, message, **kwargs):
        """Log de aviso"""
        self._log_('WARNING', message, **kwargs)
    
    def error(self, message, **kwargs):
        """Log de erro"""
        self._log_('ERROR', message, **kwargs)
    
    def critical(self, message, **kwargs):
        """Log crítico"""
        self._log_('CRITICAL', message, **kwargs)
    
    def _log_(self, level, message, **kwargs):
        """Log com contexto adicional"""
        # Adiciona contexto da requisição se disponível
        try:
            if request:
                kwargs['endpoint'] = request.endpoint
                kwargs['method'] = request.method
                kwargs['path'] = request.path
                kwargs['ip'] = request.remote_addr
        except:
            pass
        
        # Formata mensagem com dados extras
        if kwargs:
            extra_info = " | " + " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = message + extra_info
        
        # Faz log
        getattr(self.logger, level.lower())(message)
    
    def log_request(self, endpoint, method, path, user=None):
        """Log específico para requisições HTTP"""
        user_info = f"User: {user}" if user else "User: Anonymous"
        self.info(
            f"📥 REQUEST",
            endpoint=endpoint,
            method=method,
            path=path,
            user=user_info
        )
    
    def log_response(self, endpoint, status_code, duration_ms):
        """Log específico para respostas HTTP"""
        emoji = "✅" if status_code < 400 else "❌"
        self.info(
            f"{emoji} RESPONSE",
            endpoint=endpoint,
            status=status_code,
            duration=f"{duration_ms:.2f}ms"
        )
    
    def log_database(self, operation, table, details=None):
        """Log específico para operações de banco de dados"""
        self.debug(
            f"🗄️ DATABASE {operation}",
            table=table,
            details=details or ""
        )
    
    def log_ai(self, operation, model, tokens=None, thinking=False):
        """Log específico para operações de IA"""
        extra = f"Tokens: {tokens}" if tokens else ""
        if thinking:
            extra += " | Thinking Mode: ON"
        self.info(
            f"🤖 AI {operation}",
            model=model,
            extra=extra
        )
    
    def log_error_traceback(self, error):
        """Log de erro com traceback completo"""
        self.error(
            f"❌ EXCEPTION: {str(error)}\n{traceback.format_exc()}"
        )


# Instância global
logger = APBIALogger()


# ===== DECORATORS PARA AUTO-LOGGING =====

def log_function_call(func):
    """
    Decorator que loga automaticamente entrada e saída de funções
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        
        # Log de entrada
        args_repr = [repr(a) for a in args[:3]]  # Limita a 3 args
        kwargs_repr = {k: repr(v)[:50] for k, v in list(kwargs.items())[:3]}
        
        logger.debug(
            f"🔵 CALL {func_name}",
            args=args_repr,
            kwargs=kwargs_repr
        )
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            # Log de saída (sucesso)
            logger.debug(
                f"✅ RETURN {func_name}",
                duration=f"{duration:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            # Log de erro
            logger.error(
                f"❌ ERROR {func_name}",
                error=str(e),
                duration=f"{duration:.2f}ms"
            )
            logger.log_error_traceback(e)
            
            raise
    
    return wrapper


def log_route(func):
    """
    Decorator para rotas Flask que loga automaticamente requests/responses
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Captura dados da requisição
        g.start_time = time.time()
        
        endpoint = request.endpoint
        method = request.method
        path = request.path
        
        # User info
        user = current_user.nome_completo if hasattr(current_user, 'nome_completo') and current_user.is_authenticated else None
        
        logger.log_request(endpoint, method, path, user)
        
        # Loga body (se POST/PUT)
        if method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.is_json:
                    body = request.json
                    # Remove senhas do log
                    if 'senha' in body:
                        body = {**body, 'senha': '***'}
                    logger.debug(f"📦 BODY", data=str(body)[:200])
            except:
                pass
        
        try:
            # Executa rota
            result = func(*args, **kwargs)
            
            # Calcula duração
            duration_ms = (time.time() - g.start_time) * 1000
            
            # Determina status code
            if isinstance(result, tuple):
                status_code = result[1]
            else:
                status_code = 200
            
            logger.log_response(endpoint, status_code, duration_ms)
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - g.start_time) * 1000
            logger.log_response(endpoint, 500, duration_ms)
            logger.log_error_traceback(e)
            raise
    
    return wrapper

def setup_request_logging(app):
    """
    Configura middleware para logging automático de todas as requisições
    """
    
    @app.before_request
    def log_request_start():
        """Loga início da requisição"""
        # IGNORAR arquivos estáticos ANTES de acessar current_user (para otimização)
        if request.endpoint == 'static' or request.path.startswith('/static/'):
            g.start_time = time.time()
            return None
    
        g.start_time = time.time()
    
        # User info (só acessa se NÃO for estático)
        user = current_user.nome_completo if hasattr(current_user, 'nome_completo') and current_user.is_authenticated else "Anonymous"
    
        logger.log_request(
            request.endpoint or "Unknown",
            request.method,
            request.path,
            user
        )
    
        # Loga query params se houver
        if request.args:
            logger.debug(f"🔍 QUERY PARAMS", params=dict(request.args))
    
    @app.after_request
    def log_request_end(response):
        """Loga fim da requisição"""
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            logger.log_response(
                request.endpoint or "Unknown",
                response.status_code,
                duration_ms
            )
        
        return response
    
    @app.teardown_request
    def log_request_error(error=None):
        """Loga erros não tratados"""
        if error:
            logger.log_error_traceback(error)
    
    logger.info("✅ Request logging middleware configurado")


def log_startup_info(app):
    """
    Loga informações de inicialização do app
    """
    logger.info("="*70)
    logger.info("🚀 APBIA INICIANDO")
    logger.info("="*70)
    logger.info(f"IA Status: {app.config.get('IA_STATUS', 'Unknown')}")
    logger.info(f"Modelo: {app.config.get('GEMINI_MODEL', 'Unknown')}")
    logger.info(f"Blueprints registrados: {list(app.blueprints.keys())}")
    logger.info("="*70)


def log_database_operation(operation, table, data=None, result=None):
    """
    Log específico para operações de banco
    """
    logger.log_database(
        operation,
        table,
        details=f"Data: {str(data)[:100] if data else ''} | Result: {result}"
    )


def log_ai_usage(model, operation, tokens_input=None, tokens_output=None, thinking=False, search=False):
    """
    Log específico para uso de IA
    """
    details = []
    if tokens_input:
        details.append(f"In: {tokens_input}")
    if tokens_output:
        details.append(f"Out: {tokens_output}")
    if thinking:
        details.append("Thinking: ON")
    if search:
        details.append("Search: USED")
    
    logger.log_ai(
        operation,
        model,
        tokens=" | ".join(details) if details else None,
        thinking=thinking
    )