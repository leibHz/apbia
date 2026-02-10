"""
Rate Limiter para FREE tier do Gemini
10 RPM, 250k TPM, 250 RPD
"""

from collections import defaultdict
from time import time
from threading import Lock
from flask import jsonify

class RateLimiter:
    """
    Rate Limiter thread-safe para Gemini FREE tier
    
    Limites:
    - RPM: 10 requests/minuto
    - TPM: 250k tokens/minuto
    - RPD: 250 requests/dia
    """
    
    def __init__(self):
        # Adiciona lock para operações thread-safe
        self._lock = Lock()
        
        self.requests = defaultdict(list)  # {user_id: [timestamps]}
        self.daily_requests = defaultdict(int)  # {user_id: count}
        self.last_reset = {}  # {user_id: timestamp}
        
        # Limites FREE tier
        self.RPM = 10
        self.RPD = 250
    
    def check_limit(self, user_id):
        """
        Verifica se usuário pode fazer request (thread-safe)
        """
        # Lock para garantir atomicidade
        with self._lock:
            now = time()
            
            # Reset diário (meia-noite Pacific Time = 86400s)
            if user_id not in self.last_reset or (now - self.last_reset[user_id]) > 86400:
                self.daily_requests[user_id] = 0
                self.last_reset[user_id] = now
            
            # Remove requests antigas (> 1 minuto = 60s)
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < 60
            ]
            
            # Verifica RPM (requests por minuto)
            if len(self.requests[user_id]) >= self.RPM:
                return False, f"⚠️ Limite de {self.RPM} requests/minuto excedido. Aguarde 1 minuto."
            
            # Verifica RPD (requests por dia)
            if self.daily_requests[user_id] >= self.RPD:
                return False, f"⚠️ Limite diário de {self.RPD} requests excedido. Volte amanhã."
            
            # Adiciona request ANTES de retornar
            # Isso previne race conditions
            self.requests[user_id].append(now)
            self.daily_requests[user_id] += 1
            
            return True, ""
    
    def get_user_stats(self, user_id):
        """
        Retorna estatísticas de uso do usuário
        """
        with self._lock:
            now = time()
            
            # Limpa requests antigos
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < 60
            ]
            
            rpm_usado = len(self.requests[user_id])
            rpd_usado = self.daily_requests.get(user_id, 0)
            
            return {
                'rpm_usado': rpm_usado,
                'rpm_limite': self.RPM,
                'rpm_restante': max(0, self.RPM - rpm_usado),
                'rpm_percentual': int((rpm_usado / self.RPM) * 100),
                
                'rpd_usado': rpd_usado,
                'rpd_limite': self.RPD,
                'rpd_restante': max(0, self.RPD - rpd_usado),
                'rpd_percentual': int((rpd_usado / self.RPD) * 100),
            }
    
    def reset_user(self, user_id):
        """
        Reseta limites de um usuário (apenas para admin/debug)
        """
        with self._lock:
            if user_id in self.requests:
                del self.requests[user_id]
            if user_id in self.daily_requests:
                del self.daily_requests[user_id]
            if user_id in self.last_reset:
                del self.last_reset[user_id]
    
    def get_all_stats(self):
        """
        Retorna estatísticas globais
        """
        with self._lock:
            now = time()
            
            # Limpa requests antigos de todos os usuários
            for user_id in list(self.requests.keys()):
                self.requests[user_id] = [
                    req_time for req_time in self.requests[user_id]
                    if now - req_time < 60
                ]
            
            total_rpm = sum(len(reqs) for reqs in self.requests.values())
            total_rpd = sum(self.daily_requests.values())
            total_usuarios = len(self.daily_requests)
            
            return {
                'total_rpm': total_rpm,
                'total_rpd': total_rpd,
                'total_usuarios_ativos': total_usuarios,
                'limite_rpm': self.RPM,
                'limite_rpd': self.RPD,
            }

#Instância global
rate_limiter = RateLimiter()