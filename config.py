import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações"""
    

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')  
 
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  
    
    # Upload de arquivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Contexto da IA
    CONTEXT_FILES_PATH = 'context_files'
    
    # Sistema
    IA_STATUS = True  # IA ativa por padrão
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações adicionais"""
        # Cria pastas necessárias se não existirem
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.CONTEXT_FILES_PATH, exist_ok=True)
        
        # Log de configurações importantes
        print("\n" + "="*70)
        print("🤖 APBIA - Configurações inicializadas")
        print("="*70)