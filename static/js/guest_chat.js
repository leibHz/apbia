/**
 * Guest Chat - Chat com localStorage para modo anônimo
 * APBIA - Assistente de Projetos para Bragantec
 */

// ========================================
// VARIÁVEIS GLOBAIS
// ========================================
let currentChatId = null;
let guestNickname = null;
let usarPesquisaGoogle = true;
let usarContextoBragantec = false;

// ========================================
// INICIALIZAÇÃO
// ========================================
document.addEventListener('DOMContentLoaded', function () {
    // Verifica consentimento LGPD
    checkLgpdConsent();

    // Carrega preferências
    loadGuestPreferences();

    // Carrega histórico de chats
    loadGuestChats();

    // Inicializa handlers
    initGuestChatHandlers();
});

function checkLgpdConsent() {
    const consent = localStorage.getItem('apbia_lgpd_consent');
    if (!consent) {
        document.getElementById('lgpdModal').style.display = 'flex';
    }
}

function acceptLgpd() {
    localStorage.setItem('apbia_lgpd_consent', 'true');
    document.getElementById('lgpdModal').style.display = 'none';
}

function loadGuestPreferences() {
    // Apelido
    guestNickname = localStorage.getItem('apbia_guest_nickname');

    if (guestNickname) {
        document.getElementById('nicknameSetup').style.display = 'none';
        document.getElementById('welcomeNickname').textContent = guestNickname + '!';
    } else {
        document.getElementById('nicknameSetup').style.display = 'block';
    }

    // Preferências de pesquisa
    const savedSearch = localStorage.getItem('apbia_usar_pesquisa');
    if (savedSearch !== null) {
        usarPesquisaGoogle = savedSearch === 'true';
    }

    const searchToggle = document.getElementById('searchToggle');
    if (searchToggle) {
        searchToggle.checked = usarPesquisaGoogle;
    }

    updateSearchIndicator();
    updateBragantecIndicator();
}

function saveNickname() {
    const input = document.getElementById('guestNickname');
    const nickname = input.value.trim();

    if (!nickname) {
        APBIA.showNotification('Digite um apelido', 'warning');
        return;
    }

    guestNickname = nickname;
    localStorage.setItem('apbia_guest_nickname', nickname);

    document.getElementById('nicknameSetup').style.display = 'none';
    document.getElementById('welcomeNickname').textContent = nickname + '!';

    APBIA.showNotification(`Olá, ${nickname}! A IA vai te chamar assim.`, 'success');
}

// ========================================
// GERENCIAMENTO DE CHATS (localStorage)
// ========================================
function loadGuestChats() {
    const chats = getGuestChats();
    const chatHistory = document.getElementById('chatHistory');
    const emptyMsg = document.getElementById('emptyHistoryMsg');

    if (chats.length === 0) {
        if (emptyMsg) emptyMsg.style.display = 'block';
        return;
    }

    if (emptyMsg) emptyMsg.style.display = 'none';

    // Limpa lista e adiciona chats
    chatHistory.innerHTML = '';

    chats.forEach(chat => {
        const li = document.createElement('li');
        li.className = 'chat-item';
        li.dataset.chatId = chat.id;

        const date = new Date(chat.data_criacao);
        const dateStr = date.toLocaleString('pt-BR', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });

        li.innerHTML = `
            <div class="chat-item-header">
                <div style="flex: 1; min-width: 0;">
                    <h6 class="chat-item-title">${chat.titulo}</h6>
                    <small class="chat-item-date">${dateStr}</small>
                </div>
                <button class="btn-delete-chat" data-chat-id="${chat.id}" title="Deletar">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;

        li.addEventListener('click', function (e) {
            if (!e.target.closest('.btn-delete-chat')) {
                loadGuestChat(chat.id);
            }
        });

        li.querySelector('.btn-delete-chat').addEventListener('click', function (e) {
            e.stopPropagation();
            deleteGuestChat(chat.id);
        });

        chatHistory.appendChild(li);
    });
}

function getGuestChats() {
    const chatsJson = localStorage.getItem('apbia_guest_chats');
    return chatsJson ? JSON.parse(chatsJson) : [];
}

function saveGuestChats(chats) {
    localStorage.setItem('apbia_guest_chats', JSON.stringify(chats));
}

function createGuestChat(titulo) {
    const chats = getGuestChats();

    const newChat = {
        id: 'guest_' + Date.now(),
        titulo: titulo.substring(0, 50),
        data_criacao: new Date().toISOString(),
        bragantec_usado: false
    };

    chats.unshift(newChat);
    saveGuestChats(chats);

    return newChat;
}

function deleteGuestChat(chatId) {
    if (!confirm('Deletar esta conversa?')) return;

    let chats = getGuestChats();
    chats = chats.filter(c => c.id !== chatId);
    saveGuestChats(chats);

    // Remove mensagens
    localStorage.removeItem(`apbia_guest_messages_${chatId}`);
    localStorage.removeItem(`apbia_bragantec_used_${chatId}`);

    if (currentChatId === chatId) {
        currentChatId = null;
        clearChatMessages();
    }

    loadGuestChats();
    APBIA.showNotification('Conversa deletada', 'success');
}

function loadGuestChat(chatId) {
    currentChatId = chatId;

    const messages = getGuestMessages(chatId);

    clearChatMessages();

    messages.forEach(msg => {
        addMessageToChat(msg.role, msg.conteudo, msg.thinking_process);
    });

    // Verifica limite Bragantec
    checkBragantecLimit(chatId);

    // Marca como ativo
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-chat-id="${chatId}"]`)?.classList.add('active');
}

// ========================================
// MENSAGENS (localStorage)
// ========================================
function getGuestMessages(chatId) {
    const msgJson = localStorage.getItem(`apbia_guest_messages_${chatId}`);
    return msgJson ? JSON.parse(msgJson) : [];
}

function saveGuestMessage(chatId, role, conteudo, thinkingProcess = null) {
    const messages = getGuestMessages(chatId);

    messages.push({
        role: role,
        conteudo: conteudo,
        thinking_process: thinkingProcess,
        timestamp: new Date().toISOString()
    });

    localStorage.setItem(`apbia_guest_messages_${chatId}`, JSON.stringify(messages));
}

// ========================================
// LIMITE BRAGANTEC (1x por chat)
// ========================================
function checkBragantecLimit(chatId) {
    const used = localStorage.getItem(`apbia_bragantec_used_${chatId}`) === 'true';
    const toggle = document.getElementById('bragantecToggle');
    const warning = document.getElementById('bragantecLimitWarning');

    if (used) {
        toggle.disabled = true;
        toggle.checked = false;
        usarContextoBragantec = false;
        if (warning) warning.style.display = 'block';
    } else {
        toggle.disabled = false;
        if (warning) warning.style.display = 'none';
    }

    updateBragantecIndicator();
}

function markBragantecUsed(chatId) {
    localStorage.setItem(`apbia_bragantec_used_${chatId}`, 'true');

    // Atualiza chat na lista
    const chats = getGuestChats();
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
        chat.bragantec_usado = true;
        saveGuestChats(chats);
    }

    checkBragantecLimit(chatId);
    APBIA.showNotification('⚠️ Modo Bragantec usado! Limite: 1x por chat', 'warning');
}

// ========================================
// HANDLERS
// ========================================
function initGuestChatHandlers() {
    // Formulário
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', handleGuestSendMessage);
    }

    // Nova conversa
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function () {
            currentChatId = null;
            clearChatMessages();

            // Reset Bragantec
            const toggle = document.getElementById('bragantecToggle');
            toggle.disabled = false;
            toggle.checked = false;
            usarContextoBragantec = false;
            document.getElementById('bragantecLimitWarning').style.display = 'none';
            updateBragantecIndicator();

            document.querySelectorAll('.chat-item').forEach(i => i.classList.remove('active'));
        });
    }

    // Upload
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleGuestFileUpload);
    }

    // Toggle Search
    const searchToggle = document.getElementById('searchToggle');
    if (searchToggle) {
        searchToggle.addEventListener('change', function () {
            usarPesquisaGoogle = this.checked;
            localStorage.setItem('apbia_usar_pesquisa', usarPesquisaGoogle);
            updateSearchIndicator();
        });
    }

    // Toggle Bragantec
    const bragantecToggle = document.getElementById('bragantecToggle');
    if (bragantecToggle) {
        bragantecToggle.addEventListener('change', function () {
            usarContextoBragantec = this.checked;
            updateBragantecIndicator();

            if (usarContextoBragantec) {
                APBIA.showNotification('⚠️ Modo Bragantec ativo - consome muitos tokens!', 'warning');
            }
        });
    }
}

// ========================================
// ENVIAR MENSAGEM
// ========================================

// Função para obter projetos do localStorage
function getGuestProjects() {
    const projectsJson = localStorage.getItem('apbia_guest_projects');
    return projectsJson ? JSON.parse(projectsJson) : [];
}

async function handleGuestSendMessage(e) {
    e.preventDefault();

    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Adiciona mensagem do usuário
    addMessageToChat('user', message);
    input.value = '';

    // Cria chat se necessário
    if (!currentChatId) {
        const titulo = message.substring(0, 50);
        const chat = createGuestChat(titulo);
        currentChatId = chat.id;
        loadGuestChats();
    }

    // Salva mensagem do usuário
    saveGuestMessage(currentChatId, 'user', message);

    // Prepara histórico para API
    const history = getGuestMessages(currentChatId).slice(0, -1).map(m => ({
        role: m.role,
        parts: [m.conteudo]
    }));

    // ✅ Obtém projetos do localStorage para contexto
    const projetos = getGuestProjects();

    showThinking(true);

    try {
        const response = await fetch('/guest/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                apelido: guestNickname,
                usar_pesquisa: usarPesquisaGoogle,
                usar_code_execution: true,
                usar_contexto_bragantec: usarContextoBragantec,
                history: history,
                projetos: projetos  // ✅ Envia projetos para contexto da IA
            })
        });

        const data = await response.json();

        showThinking(false);

        if (data.error) {
            showError(data.message || 'Erro ao processar mensagem');
            return;
        }

        if (data.success) {
            // Salva resposta
            saveGuestMessage(currentChatId, 'model', data.response, data.thinking_process);

            // Exibe resposta
            addMessageToChat('assistant', data.response, data.thinking_process, data.search_used, data.code_results);

            // Marca Bragantec como usado se foi ativo
            if (usarContextoBragantec) {
                markBragantecUsed(currentChatId);
            }
        }

    } catch (error) {
        showThinking(false);
        console.error('❌ Erro:', error);
        showError('Erro ao conectar com o servidor');
    }
}

// ========================================
// UPLOAD DE ARQUIVO
// ========================================
async function handleGuestFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const maxSize = 16 * 1024 * 1024;
    if (file.size > maxSize) {
        APBIA.showNotification('Arquivo muito grande! Máximo: 16MB', 'error');
        e.target.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', 'Analise este arquivo');
    formData.append('apelido', guestNickname || '');

    showThinking(true);

    try {
        const response = await fetch('/guest/upload-file', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        showThinking(false);

        if (data.success) {
            // Cria chat se necessário
            if (!currentChatId) {
                const chat = createGuestChat(`Análise: ${file.name}`);
                currentChatId = chat.id;
                loadGuestChats();
            }

            addMessageToChat('user', `📎 Analise este arquivo: ${file.name}`);
            saveGuestMessage(currentChatId, 'user', `📎 Analise este arquivo: ${file.name}`);

            addMessageToChat('assistant', data.response, data.thinking_process);
            saveGuestMessage(currentChatId, 'model', data.response, data.thinking_process);

            APBIA.showNotification('Arquivo processado!', 'success');
        } else {
            showError(data.message);
        }

    } catch (error) {
        showThinking(false);
        showError('Erro ao enviar arquivo');
    }

    e.target.value = '';
}

// ========================================
// UI HELPERS
// ========================================
function addMessageToChat(role, content, thinking = null, searchUsed = false, codeResults = null) {
    const messagesContainer = document.getElementById('chatMessages');

    // Remove welcome
    const welcome = document.getElementById('welcomeMessage');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} fade-in`;

    // Thinking process
    if (role === 'assistant' && thinking) {
        const thinkingBadge = document.createElement('div');
        thinkingBadge.className = 'alert alert-light border mb-2';
        thinkingBadge.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-brain text-primary me-2"></i>
                <strong>Processo de Pensamento:</strong>
                <button class="btn btn-sm btn-outline-primary ms-auto toggle-thinking">
                    <i class="fas fa-chevron-down"></i> Ver
                </button>
            </div>
            <div class="thinking-content" style="display: none; font-size: 0.9em; color: #666;">
                ${formatContent(thinking)}
            </div>
        `;

        messageDiv.appendChild(thinkingBadge);

        thinkingBadge.querySelector('.toggle-thinking').addEventListener('click', function () {
            const content = thinkingBadge.querySelector('.thinking-content');
            if (content.style.display === 'none') {
                content.style.display = 'block';
                this.innerHTML = '<i class="fas fa-chevron-up"></i> Ocultar';
            } else {
                content.style.display = 'none';
                this.innerHTML = '<i class="fas fa-chevron-down"></i> Ver';
            }
        });
    }

    // Conteúdo
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatContent(content);
    messageDiv.appendChild(contentDiv);

    // Badge search
    if (role === 'assistant' && searchUsed) {
        const badge = document.createElement('div');
        badge.className = 'mt-2';
        badge.innerHTML = '<small class="badge bg-success"><i class="fas fa-search"></i> Consultou Google</small>';
        messageDiv.appendChild(badge);
    }

    // Timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    messageDiv.appendChild(timestamp);

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatContent(content) {
    const div = document.createElement('div');
    div.textContent = content;
    let html = div.innerHTML;
    html = html.replace(/\n/g, '<br>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    return html;
}

function clearChatMessages() {
    const container = document.getElementById('chatMessages');
    const nickname = guestNickname ? guestNickname + '!' : '';

    container.innerHTML = `
        <div class="welcome-message" id="welcomeMessage">
            <i class="fas fa-robot"></i>
            <h4>Olá! <span id="welcomeNickname">${nickname}</span></h4>
            <p>Como posso ajudar você hoje com seu projeto da Bragantec?</p>
        </div>
    `;
}

function showThinking(show) {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) indicator.style.display = show ? 'block' : 'none';
}

function showError(message) {
    APBIA.showNotification(message, 'error');
}

function updateSearchIndicator() {
    const indicator = document.getElementById('searchStatusIndicator');
    if (indicator) {
        indicator.innerHTML = usarPesquisaGoogle
            ? '<i class="fas fa-search text-success"></i> Pesquisa ativa'
            : '<i class="fas fa-search text-muted"></i> Pesquisa desativada';
    }
}

function updateBragantecIndicator() {
    const indicator = document.getElementById('bragantecStatusIndicator');
    if (indicator) {
        indicator.innerHTML = usarContextoBragantec
            ? '<i class="fas fa-book text-warning"></i> Modo Bragantec ativo ⚠️'
            : '<i class="fas fa-book text-muted"></i> Modo Bragantec desativado';
    }
}

// ========================================
// LIMPAR DADOS
// ========================================
function clearAllGuestData() {
    if (!confirm('⚠️ Limpar TODOS os dados?\n\nIsso vai apagar:\n- Histórico de conversas\n- Projetos salvos\n- Preferências\n\nEsta ação não pode ser desfeita.')) {
        return;
    }

    // Remove tudo do guest
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key.startsWith('apbia_guest') || key.startsWith('apbia_bragantec')) {
            keysToRemove.push(key);
        }
    }

    keysToRemove.forEach(key => localStorage.removeItem(key));

    // Mantém consentimento LGPD
    // localStorage.removeItem('apbia_lgpd_consent'); // Comentado para manter

    APBIA.showNotification('Todos os dados foram apagados', 'success');

    // Recarrega página
    setTimeout(() => location.reload(), 1000);
}
