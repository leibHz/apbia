"""
Funções auxiliares para o APBIA
"""

import os
import re
import uuid
import time
import mimetypes
from threading import Lock
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config


def allowed_file(filename):
    """
    Verifica se o arquivo tem extensão permitida
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """
    Retorna a extensão do arquivo
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def format_file_size(bytes):
    """
    Formata tamanho de arquivo para leitura humana
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0


def sanitize_filename(filename):
    """
    Sanitiza nome de arquivo removendo caracteres perigosos
    """
    # Remove caracteres especiais
    filename = secure_filename(filename)
    
    # Adiciona timestamp para evitar conflitos
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{name}_{timestamp}{ext}"


def validate_bp(bp):
    """
    Valida número de inscrição (BP)
    Formato: BP12345678X onde:
    - Sempre começa com 'BP'
    - 1-8 dígitos numéricos
    - Letra opcional no final (A-Z)
    """
    if not bp:
        return False
    
    # Converte para maiúscula e remove espaços
    bp = str(bp).strip().upper()
    
    # Padrão: BP + 1-8 dígitos + letra opcional
    pattern = r'^BP\d{1,8}[A-Z]?$'
    
    return re.match(pattern, bp) is not None


def format_bp(bp):
    """
    Formata BP para o padrão correto (maiúsculo)
    """
    if not bp:
        return None
    
    return str(bp).strip().upper()

def generate_chat_title(first_message, max_length=50):
    """
    Gera título para chat baseado na primeira mensagem
    """
    # Trunca e limpa
    title = first_message.strip()
    title = re.sub(r'\s+', ' ', title)  # Remove espaços múltiplos
    
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0] + '...'
    
    return title or 'Nova conversa'

def detect_mime_type(filename, content_type=None):
    """
    Detecta MIME type de forma robusta
    """
    
    # 1. Tenta usar content_type do request
    if content_type and content_type != 'application/octet-stream':
        return content_type
    
    # 2. Tenta detectar pela extensão
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    
    # 3. Fallback baseado em extensão
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    fallback_types = {
        # Imagens
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        
        # Documentos
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain',
        
        # Vídeos
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'wmv': 'video/x-ms-wmv',
        'flv': 'video/x-flv',
        'webm': 'video/webm',
        
        # Áudio
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        
        # Código
        'py': 'text/x-python',
        'js': 'text/javascript',
        'html': 'text/html',
        'css': 'text/css',
        'json': 'application/json',
        'xml': 'application/xml',
        
        # Compactados
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        'tar': 'application/x-tar',
        'gz': 'application/gzip',
    }
    
    # 4. Retorna tipo baseado em extensão ou genérico
    return fallback_types.get(ext, 'application/octet-stream')
def save_uploaded_file(file, base_dir, user_id, subfolder=None):
    """
    Salva arquivo com nome único e proteção contra race conditions
    """
    
    # Lock global para evitar race conditions
    if not hasattr(save_uploaded_file, 'lock'):
        save_uploaded_file.lock = Lock()
    
    with save_uploaded_file.lock:
        # Monta estrutura de diretórios
        user_dir = os.path.join(base_dir, str(user_id))
        
        if subfolder:
            final_dir = os.path.join(user_dir, str(subfolder))
        else:
            final_dir = user_dir
            
        os.makedirs(final_dir, exist_ok=True)
        
        # Nome único COM timestamp + contador
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time() * 1000)  # Milissegundos
        
        counter = 0
        while True:
            suffix = f"_{counter}" if counter > 0 else ""
            unique_filename = f"{unique_id}_{timestamp}{suffix}_{original_filename}"
            full_path = os.path.join(final_dir, unique_filename)
            
            if not os.path.exists(full_path):
                break
            counter += 1
        
        file.save(full_path)
        
        # Caminho relativo (para salvar no banco)
        if subfolder:
            relative_path = os.path.join(os.path.basename(base_dir), str(user_id), str(subfolder), unique_filename)
        else:
            relative_path = os.path.join(os.path.basename(base_dir), str(user_id), unique_filename)
        
        # Tamanho do arquivo
        file_size = os.path.getsize(full_path)
        
        # MIME type
        mime_type = detect_mime_type(original_filename, file.content_type)
        
        return {
            'filepath': relative_path,
            'filename': original_filename,
            'mime_type': mime_type,
            'size': file_size
        }