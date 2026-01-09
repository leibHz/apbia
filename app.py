from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, logout_user
from config import Config
from dao.dao import SupabaseDAO

from utils.advanced_logger import logger, setup_request_logging, log_startup_info
from utils.session_manager import get_session_manager

# Importa blueprints
from controllers.auth_controller import auth_bp
from controllers.chat_controller import chat_bp
from controllers.admin_controller import admin_bp
from controllers.project_controller import project_bp
from controllers.orientador_controller import orientador_bp
from controllers.guest_controller import guest_bp

# Inicializa aplicação
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Configura logging avançado
setup_request_logging(app)

# Inicializa Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# DAO para carregar usuários
dao = SupabaseDAO()

@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário para Flask-Login"""
    try:
        logger.debug(f"🔍 Carregando usuário ID: {user_id}")
        user = dao.buscar_usuario_por_id(int(user_id))
        if user:
            logger.info(f"✅ Usuário carregado: {user.nome_completo} (ID: {user.id})")
        else:
            logger.warning(f"⚠️ Usuário não encontrado: ID {user_id}")
        return user
    except Exception as e:
        logger.error(f"❌ Erro ao carregar usuário ID {user_id}: {str(e)}")
        # Retorna None para não quebrar a requisição
        return None
        
# Registra blueprints
logger.info("📦 Registrando blueprints...")
app.register_blueprint(auth_bp)
logger.debug("✅ auth_bp registrado")

app.register_blueprint(chat_bp, url_prefix='/chat')
logger.debug("✅ chat_bp registrado em /chat")

app.register_blueprint(admin_bp, url_prefix='/admin')
logger.debug("✅ admin_bp registrado em /admin")

app.register_blueprint(project_bp, url_prefix='/projetos')
logger.debug("✅ project_bp registrado em /projetos")

app.register_blueprint(orientador_bp, url_prefix='/orientador')
logger.debug("✅ orientador_bp registrado em /orientador")

app.register_blueprint(guest_bp, url_prefix='/guest')
logger.debug("✅ guest_bp registrado em /guest")

@app.before_request
def check_session_validity():
    """Verifica validade da sessão antes de cada request"""
    
    # PRIMEIRA PRIORIDADE: Ignorar arquivos estáticos ANTES de qualquer processamento, para evitar overhead desnecessário
    # overhead significa "sobrecarga" em português
    if request.endpoint == 'static' or request.path.startswith('/static/'):
        return None
    
    # Ignora rotas públicas
    public_endpoints = ['auth.login', 'auth.logout', 'index']
    
    if request.endpoint in public_endpoints:
        return None
    
    # Ignora endpoints de polling/API que não devem atualizar atividade, senaoo a sessão nunca expira
    polling_endpoints = ['auth.check_session', 'admin.gemini_stats_api', 'admin.stats_api']
    if request.endpoint in polling_endpoints:
        return None
    
    # Verifica se usuário está autenticado
    if current_user.is_authenticated:
        try:
            session_manager = get_session_manager()
            
            # Valida sessão (atualiza atividade para requisições normais)
            if not session_manager.validate_session(current_user.id):
                logout_user()
                session.clear()
                flash('⚠️ Sua conta foi acessada de outro dispositivo ou ficou inativa por muito tempo. Faça login novamente.', 'warning')
                return redirect(url_for('auth.login'))
        except Exception as e:
            logger.error(f"❌ Erro ao validar sessão: {str(e)}")
    
    return None

# rota principal
@app.route('/')
def index():
    """Página inicial"""
    logger.debug("📄 Renderizando página inicial")
    return render_template('index.html')

@app.route('/privacidade')
def privacidade():
    """Página de política de privacidade (LGPD)"""
    return render_template('privacidade.html')

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"❌ 404 - Página não encontrada: {error}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.critical(f"💥 500 - Erro interno do servidor: {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"🚫 403 - Acesso negado: {error}")
    return render_template('errors/403.html'), 403

# Context processor para variáveis globais nos templates
@app.context_processor
def inject_globals():
    return {
        'app_name': 'APBIA',
        'app_version': '1.0.0',
        'ia_status': Config.IA_STATUS
    }

if __name__ == '__main__':
    log_startup_info(app)
    
    logger.info("🌐 Iniciando servidor Flask...")
    logger.info(f"🔗 Acesse: http://localhost:5000")
    logger.info(f"🔗 Acesse (rede local): http://0.0.0.0:5000")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        logger.info("⏹️ Servidor encerrado pelo usuário")
    except Exception as e:
        logger.critical(f"💥 Erro fatal ao iniciar servidor: {e}")
        raise