 // Session Monitor - APBIA
 // Monitora a validade da sessão em tempo real
 // Desconecta automaticamente se:
 // - Login em outro dispositivo
 // - Inatividade > 1 hora

(function() {
    'use strict';
    
    // Configurações
    const CHECK_INTERVAL = 30000; // 30 segundos
    const SESSION_CHECK_URL = '/check-session';
    
    let checkTimer = null;
    let isChecking = false;
    
    
    // Verifica validade da sessão no servidor
    
    async function checkSession() {
        // Evita múltiplas verificações simultâneas
        if (isChecking) {
            return;
        }
        
        isChecking = true;
        
        try {
            const response = await fetch(SESSION_CHECK_URL, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                // Se retornou 401 ou outro erro, sessão inválida
                handleInvalidSession('Sessão expirada');
                return;
            }
            
            const data = await response.json();
            
            if (!data.valid) {
                // Sessão inválida
                const reason = data.reason || 'unknown';
                
                if (reason === 'session_expired') {
                    handleInvalidSession('Sua conta foi acessada de outro dispositivo ou a sessão expirou por inatividade.');
                } else {
                    handleInvalidSession('Sessão expirada. Faça login novamente.');
                }
            }
            
        } catch (error) {
            // Em caso de erro de rede, não desconecta
            console.warn('⚠️ Erro ao verificar sessão:', error);
            // Não faz nada, próxima verificação tentará novamente
        } finally {
            isChecking = false;
        }
    }
    
    function handleInvalidSession(message) {
        // Para o timer
        stopMonitoring();
    
        // ✅ CRÍTICO: Previne loop infinito - não redireciona se já está na página de login
        if (window.location.pathname === '/login') {
            return; // Já está na página de login, não faz nada
        }
    
        // Esconde navbar imediatamente
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.style.display = 'none';
        }
    
        // Limpa TUDO do localStorage e sessionStorage
        try {
            localStorage.clear();
            sessionStorage.clear();
        } catch (e) {
            console.warn('⚠️ Erro ao limpar cache:', e);
        }
    
        // Notificação mais visível
        if (window.APBIA && window.APBIA.showNotification) {
            window.APBIA.showNotification('🔒 ' + message, 'warning');
        } else {
            alert('🔒 SESSÃO EXPIRADA\n\n' + message);
        }
    
        // Aguarda 3 segundos para o usuário ler
        setTimeout(() => {
            window.location.href = '/login?session_expired=1&t=' + Date.now();
        }, 3000);
    }
    
    // Inicia monitoramento
     
    function startMonitoring() {
        // ✅ CRÍTICO: Não inicia se estiver na página de login
        if (window.location.pathname === '/login') {
            return;
        }
    
        if (checkTimer) {
            return; // Já está rodando
        }
    
        // Primeira verificação imediata
        checkSession();
    
        // Verificações periódicas
        checkTimer = setInterval(checkSession, CHECK_INTERVAL);
    }
    
    
    // Para monitoramento
    function stopMonitoring() {
        if (checkTimer) {
            clearInterval(checkTimer);
            checkTimer = null;
        }
    }
    
    
    // Atualiza atividade ao interagir com a página
    function updateActivity() {
        // A cada interação do usuário, atualiza timestamp local
        // O backend já atualiza no banco a cada request
        localStorage.setItem('last_user_activity', Date.now().toString());
    }
    
    // Eventos de atividade do usuário
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    
    activityEvents.forEach(eventName => {
        document.addEventListener(eventName, updateActivity, { passive: true });
    });
    
    // Inicia monitoramento ao carregar a página
    document.addEventListener('DOMContentLoaded', function() {
        // Só monitora se estiver logado (verifica se existe elemento indicador)
        const isLoggedIn = document.body.classList.contains('logged-in') || 
                          document.querySelector('[data-user-id]') !== null;
        
        if (isLoggedIn) {
            startMonitoring();
        }
    });
    
    // Para monitoramento ao sair da página
    window.addEventListener('beforeunload', function() {
        stopMonitoring();
    });
    
    // Expõe funções globalmente para debug
    window.SessionMonitor = {
        start: startMonitoring,
        stop: stopMonitoring,
        checkNow: checkSession
    };
    
})();
