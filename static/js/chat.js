let currentChatId = null;
let usarPesquisaGoogle = true; // Google Search ativado por padrão
let usarContextoBragantec = false; // Modo Bragantec desativado por padrão

// Inicialização
document.addEventListener('DOMContentLoaded', function () {
    initializeChatHandlers();
    loadSearchPreference();
    loadBragantecPreference();
});

function initializeChatHandlers() {
    // Formulário de envio
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', handleSendMessage);
    }

    // Botão de nova conversa
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }

    // Botão de upload
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    // Upload de arquivo
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }

    // Toggle Google Search
    const searchToggle = document.getElementById('searchToggle');
    if (searchToggle) {
        searchToggle.checked = usarPesquisaGoogle;
        searchToggle.addEventListener('change', function () {
            usarPesquisaGoogle = this.checked;
            localStorage.setItem('apbia_usar_pesquisa', usarPesquisaGoogle);

            updateSearchIndicator();

            const msg = usarPesquisaGoogle ?
                'Google Search ativado - IA pode buscar informações atualizadas' :
                'Google Search desativado - IA usará apenas conhecimento base';
            APBIA.showNotification(msg, 'info');
        });
    }

    // Toggle Modo Bragantec
    const bragantecToggle = document.getElementById('bragantecToggle');
    if (bragantecToggle) {
        bragantecToggle.checked = usarContextoBragantec;
        bragantecToggle.addEventListener('change', function () {
            usarContextoBragantec = this.checked;
            localStorage.setItem('apbia_usar_bragantec', usarContextoBragantec);

            updateBragantecIndicator();

            const msg = usarContextoBragantec ?
                '⚠️ Modo Bragantec ATIVADO - Consome muitos tokens!' :
                '✅ Modo Bragantec desativado - Economia de tokens';
            APBIA.showNotification(msg, usarContextoBragantec ? 'warning' : 'success');
        });
    }

    // Itens do histórico
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', function (e) {
            if (!e.target.classList.contains('delete-chat') &&
                !e.target.closest('.btn-delete-chat')) {
                loadChat(this.dataset.chatId);
            }
        });
    });

    // Botões de deletar chat
    document.querySelectorAll('.btn-delete-chat').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            deleteChat(this.dataset.chatId);
        });
    });
}

function loadSearchPreference() {
    const saved = localStorage.getItem('apbia_usar_pesquisa');
    if (saved !== null) {
        usarPesquisaGoogle = saved === 'true';
        const toggle = document.getElementById('searchToggle');
        if (toggle) {
            toggle.checked = usarPesquisaGoogle;
        }
    }
    updateSearchIndicator();
}

function loadBragantecPreference() {
    const saved = localStorage.getItem('apbia_usar_bragantec');
    if (saved !== null) {
        usarContextoBragantec = saved === 'true';
        const toggle = document.getElementById('bragantecToggle');
        if (toggle) {
            toggle.checked = usarContextoBragantec;
        }
    }
    updateBragantecIndicator();
}

function updateSearchIndicator() {
    const indicator = document.getElementById('searchStatusIndicator');
    if (indicator) {
        if (usarPesquisaGoogle) {
            indicator.innerHTML = '<i class="fas fa-search text-success"></i> Pesquisa ativa';
        } else {
            indicator.innerHTML = '<i class="fas fa-search text-muted"></i> Pesquisa desativada';
        }
    }
}

function updateBragantecIndicator() {
    const indicator = document.getElementById('bragantecStatusIndicator');
    if (indicator) {
        if (usarContextoBragantec) {
            indicator.innerHTML = '<i class="fas fa-book text-warning"></i> Modo Bragantec ativo ⚠️';
        } else {
            indicator.innerHTML = '<i class="fas fa-book text-muted"></i> Modo Bragantec desativado';
        }
    }
}

async function handleSendMessage(e) {
    e.preventDefault();

    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Adiciona mensagem do usuário
    addMessageToChat('user', message);

    // Limpa input
    input.value = '';

    // Mostra indicador de pensamento
    showThinking(true);

    try {
        const response = await fetch('/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId,
                usar_pesquisa: usarPesquisaGoogle,
                usar_code_execution: true,
                usar_contexto_bragantec: usarContextoBragantec
            })
        });

        // Verifica se a resposta foi OK
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        showThinking(false);

        if (data.error) {
            showError(data.message || 'Erro ao processar mensagem');
            return;
        }

        if (data.success) {
            // Log de tokens (se disponível)
            if (data.tokens_input || data.tokens_output) {
                window.lastTokenUsage = {
                    input: data.tokens_input,
                    output: data.tokens_output
                };
            }

            // Alerta se consumo muito alto
            if (data.tokens_input && data.tokens_input > 100000) {
                APBIA.showNotification(
                    `⚠️ Alto consumo de tokens: ${data.tokens_input.toLocaleString('pt-BR')} tokens de entrada!\n` +
                    `Dica: Desative o Modo Bragantec se não precisar do histórico completo.`,
                    'warning'
                );
            }

            // Adiciona resposta da IA
            addMessageToChat(
                'assistant',
                data.response,
                data.thinking_process,
                data.search_used,
                data.code_results
            );

            // Só mostra aviso se for REALMENTE uma nova conversa
            if (data.chat_id && !currentChatId) {
                currentChatId = data.chat_id;
                addChatToSidebar(data.chat_id, message);
            } else if (data.chat_id) {
                // Atualiza ID se mudou
                currentChatId = data.chat_id;
            }
        }

    } catch (error) {
        showThinking(false);
        // Mensagem de erro mais clara
        console.error('❌ Erro na requisição:', error);
        showError('Erro ao enviar mensagem. Verifique sua conexão e tente novamente.');
    }
}

function addChatToSidebar(chatId, firstMessage) {
    const chatHistory = document.getElementById('chatHistory');

    // Remove mensagem "Nenhum chat anterior" se existir
    const emptyMessage = chatHistory.querySelector('.sidebar-empty');
    if (emptyMessage) {
        emptyMessage.remove();
    }

    // Cria elemento do chat
    const chatItem = document.createElement('li');
    chatItem.className = 'chat-item active';
    chatItem.dataset.chatId = chatId;

    const now = new Date();
    const timeStr = now.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    const title = firstMessage.length > 40 ?
        firstMessage.substring(0, 40) + '...' :
        firstMessage;

    chatItem.innerHTML = `
        <div class="chat-item-header">
            <div style="flex: 1; min-width: 0;">
                <h6 class="chat-item-title">${title}</h6>
                <small class="chat-item-date">${timeStr}</small>
            </div>
            <button class="btn-delete-chat" 
                    data-chat-id="${chatId}"
                    title="Deletar conversa">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;

    // Adiciona no topo da lista
    chatHistory.insertBefore(chatItem, chatHistory.firstChild);

    // Adiciona handlers
    chatItem.addEventListener('click', function (e) {
        if (!e.target.classList.contains('btn-delete-chat') &&
            !e.target.closest('.btn-delete-chat')) {
            loadChat(this.dataset.chatId);
        }
    });

    chatItem.querySelector('.btn-delete-chat').addEventListener('click', function (e) {
        e.stopPropagation();
        deleteChat(this.dataset.chatId);
    });

    // Remove classe active de outros chats
    document.querySelectorAll('.chat-item').forEach(item => {
        if (item !== chatItem) {
            item.classList.remove('active');
        }
    });
}

function addMessageToChat(role, content, thinking = null, searchUsed = false, codeResults = null, arquivo = null, notasOrientador = null) {
    const messagesContainer = document.getElementById('chatMessages');

    // Remove mensagem de boas-vindas
    const welcome = document.getElementById('welcomeMessage');
    if (welcome) {
        welcome.remove();
    }

    // Cria elemento da mensagem
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} fade-in`;

    // Badge de arquivo anexado
    if (arquivo) {
        const fileBadge = document.createElement('div');
        fileBadge.className = 'alert alert-secondary border mb-2';
        fileBadge.style.background = '#f8f9fa';

        let icon = 'fa-file';
        if (arquivo.tipo && arquivo.tipo.startsWith('image/')) {
            icon = 'fa-image';
        } else if (arquivo.tipo && arquivo.tipo.startsWith('video/')) {
            icon = 'fa-video';
        } else if (arquivo.tipo && arquivo.tipo.startsWith('audio/')) {
            icon = 'fa-music';
        } else if (arquivo.tipo && arquivo.tipo.includes('pdf')) {
            icon = 'fa-file-pdf';
        }

        const tamanhoMB = (arquivo.tamanho / (1024 * 1024)).toFixed(2);

        fileBadge.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                    <i class="fas ${icon} fa-2x text-primary me-3"></i>
                    <div>
                        <strong>${arquivo.nome}</strong>
                        <br>
                        <small class="text-muted">
                            ${arquivo.tipo || 'Tipo desconhecido'} • ${tamanhoMB} MB
                        </small>
                    </div>
                </div>
                <div>
                    ${arquivo.url ? `
                        <a href="${arquivo.url}" 
                           class="btn btn-sm btn-outline-primary" 
                           target="_blank"
                           title="Visualizar arquivo">
                            <i class="fas fa-eye"></i> Ver
                        </a>
                    ` : ''}
                </div>
            </div>
        `;

        messageDiv.appendChild(fileBadge);
    }

    // Badge de thinking process
    if (role === 'assistant' && thinking) {
        const thinkingBadge = document.createElement('div');
        thinkingBadge.className = 'alert alert-light border mb-2';
        thinkingBadge.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-brain text-primary me-2"></i>
                <strong>Processo de Pensamento da IA:</strong>
                <button class="btn btn-sm btn-outline-primary ms-auto toggle-thinking">
                    <i class="fas fa-chevron-down"></i> Ver
                </button>
            </div>
            <div class="thinking-content" style="display: none; font-size: 0.9em; color: #666;">
                ${formatMessageContent(thinking)}
            </div>
        `;

        messageDiv.appendChild(thinkingBadge);

        thinkingBadge.querySelector('.toggle-thinking').addEventListener('click', function () {
            const content = thinkingBadge.querySelector('.thinking-content');
            const icon = this.querySelector('i');

            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.className = 'fas fa-chevron-up';
                this.innerHTML = '<i class="fas fa-chevron-up"></i> Ocultar';
            } else {
                content.style.display = 'none';
                icon.className = 'fas fa-chevron-down';
                this.innerHTML = '<i class="fas fa-chevron-down"></i> Ver';
            }
        });
    }

    // Badge de Code Execution
    if (role === 'assistant' && codeResults && Array.isArray(codeResults) && codeResults.length > 0) {
        const codeBadge = document.createElement('div');
        codeBadge.className = 'alert alert-dark border mb-2';
        codeBadge.style.background = '#1e1e1e';
        codeBadge.style.color = '#d4d4d4';

        codeBadge.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-code text-success me-2"></i>
                <strong style="color: #4ec9b0;">Código Python Executado:</strong>
                <span class="badge bg-success ms-2">${codeResults.length} script(s)</span>
                <button class="btn btn-sm btn-outline-success ms-auto toggle-code">
                    <i class="fas fa-chevron-down"></i> Ver Código
                </button>
            </div>
            <div class="code-content" style="display: none;">
                ${formatCodeResults(codeResults)}
            </div>
        `;

        messageDiv.appendChild(codeBadge);

        codeBadge.querySelector('.toggle-code').addEventListener('click', function () {
            const content = codeBadge.querySelector('.code-content');
            const icon = this.querySelector('i');

            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.className = 'fas fa-chevron-up';
                this.innerHTML = '<i class="fas fa-chevron-up"></i> Ocultar Código';
            } else {
                content.style.display = 'none';
                icon.className = 'fas fa-chevron-down';
                this.innerHTML = '<i class="fas fa-chevron-down"></i> Ver Código';
            }
        });
    }

    // Conteúdo principal
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessageContent(content);
    messageDiv.appendChild(contentDiv);

    // Badge de notas do orientador
    if (role === 'assistant' && notasOrientador && notasOrientador.length > 0) {
        const notasBadge = document.createElement('div');
        notasBadge.className = 'mt-2 p-2';
        notasBadge.style.background = 'rgba(255, 193, 7, 0.1)';
        notasBadge.style.borderLeft = '4px solid #FFC107';
        notasBadge.style.borderRadius = '8px';

        let notasHtml = '<strong style="color: #FFC107;"><i class="fas fa-sticky-note"></i> Notas do Orientador:</strong><br>';
        notasOrientador.forEach(nota => {
            notasHtml += `
                <div style="margin-top: 0.5rem; padding: 0.5rem; background: rgba(0,0,0,0.1); border-radius: 4px;">
                    <p style="margin: 0; color: var(--text-primary);">${nota.nota}</p>
                    <small style="color: var(--text-muted);">
                        ${nota.orientador_nome || 'Orientador'} - ${nota.data_criacao}
                    </small>
                </div>
            `;
        });

        notasBadge.innerHTML = notasHtml;
        messageDiv.appendChild(notasBadge);
    }

    // Badge de Google Search
    if (role === 'assistant' && searchUsed) {
        const searchBadge = document.createElement('div');
        searchBadge.className = 'mt-2';
        searchBadge.innerHTML = `
            <small class="badge bg-success">
                <i class="fas fa-search"></i> Consultou Google Search
            </small>
        `;
        messageDiv.appendChild(searchBadge);
    }

    // Badge de consumo de tokens
    if (role === 'assistant' && window.lastTokenUsage) {
        const tokenBadge = document.createElement('div');
        tokenBadge.className = 'mt-2';

        const inputTokens = window.lastTokenUsage.input || 0;
        const outputTokens = window.lastTokenUsage.output || 0;
        const totalTokens = inputTokens + outputTokens;

        const alertClass = inputTokens > 100000 ? 'bg-danger' :
            inputTokens > 50000 ? 'bg-warning' : 'bg-info';

        tokenBadge.innerHTML = `
            <small class="badge ${alertClass}">
                <i class="fas fa-coins"></i> 
                ${totalTokens.toLocaleString('pt-BR')} tokens
                (↑${inputTokens.toLocaleString('pt-BR')} ↓${outputTokens.toLocaleString('pt-BR')})
                ${inputTokens > 100000 ? ' ⚠️ Alto consumo!' : ''}
            </small>
        `;

        messageDiv.appendChild(tokenBadge);
        delete window.lastTokenUsage;
    }

    // Timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = new Date().toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
    messageDiv.appendChild(timestamp);

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatCodeResults(codeResults) {
    let html = '';

    codeResults.forEach((codeInfo, index) => {
        const language = codeInfo.language || 'python';
        const code = codeInfo.code || '';
        const result = codeInfo.result || null;

        html += `
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong style="color: #4ec9b0;">Script ${index + 1}:</strong>
                    <span class="badge bg-secondary">${language}</span>
                </div>
                <pre style="background: #282c34; color: #abb2bf; padding: 15px; border-radius: 8px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 0.9em;"><code>${escapeHtml(code)}</code></pre>
                ${result ? `
                    <div class="mt-2">
                        <div class="d-flex align-items-center gap-2 mb-2">
                            <strong style="color: #98c379;">Resultado da Execução:</strong>
                            <span class="badge ${result.outcome === 'OUTCOME_OK' ? 'bg-success' : 'bg-danger'}">
                                ${result.outcome === 'OUTCOME_OK' ? '✅ Sucesso' : '❌ Erro'}
                            </span>
                        </div>
                        ${result.output ? `
                            <pre style="background: #1e3a1e; color: #98c379; padding: 15px; border-radius: 8px; margin-top: 5px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 0.9em;"><code>${escapeHtml(result.output)}</code></pre>
                        ` : '<em style="color: #888;">Nenhuma saída gerada</em>'}
                    </div>
                ` : '<em style="color: #888;">Aguardando execução...</em>'}
            </div>
        `;
    });

    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMessageContent(content) {
    const div = document.createElement('div');
    div.textContent = content;
    let html = div.innerHTML;

    html = html.replace(/\n/g, '<br>');
    html = html.replace(/^- (.+)$/gm, '• $1');
    html = html.replace(/^\d+\. (.+)$/gm, '<strong>$&</strong>');
    html = html.replace(/`([^`]+)`/g, '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace;">$1</code>');

    return html;
}

function showThinking(show) {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) {
        indicator.style.display = show ? 'block' : 'none';
    }
}

async function createNewChat() {
    const titulo = prompt('Nome da nova conversa:', 'Nova conversa');

    if (!titulo) return;

    try {
        const response = await fetch('/chat/new-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ titulo })
        });

        const data = await response.json();

        if (data.success) {
            currentChatId = data.chat.id;
            clearChatMessages();
            addChatToSidebar(data.chat.id, titulo);
        } else {
            showError(data.message || 'Erro ao criar chat');
        }

    } catch (error) {
        showError('Erro ao criar nova conversa');
        console.error('Erro:', error);
    }
}

async function deleteChat(chatId) {
    if (!confirm('Deseja realmente deletar esta conversa? O histórico será perdido permanentemente.')) return;

    try {
        const response = await fetch(`/chat/delete-chat/${chatId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            APBIA.showNotification('Conversa deletada', 'success');

            const chatItem = document.querySelector(`[data-chat-id="${chatId}"]`);
            if (chatItem) {
                chatItem.remove();
            }

            if (currentChatId === parseInt(chatId)) {
                currentChatId = null;
                clearChatMessages();
            }

            const chatHistory = document.getElementById('chatHistory');
            if (chatHistory.children.length === 0) {
                chatHistory.innerHTML = `
                    <div class="sidebar-empty">
                        <i class="fas fa-inbox"></i>
                        <p>Nenhum chat anterior</p>
                    </div>
                `;
            }
        } else {
            showError(data.message || 'Erro ao deletar chat');
        }

    } catch (error) {
        showError('Erro ao deletar conversa');
        console.error('Erro:', error);
    }
}

async function loadChat(chatId) {
    currentChatId = parseInt(chatId);

    APBIA.showLoadingOverlay('Carregando histórico...');

    try {
        const response = await fetch(`/chat/load-history/${chatId}`);
        const data = await response.json();

        APBIA.hideLoadingOverlay();

        if (data.success) {
            clearChatMessages();

            // Carrega mensagens COM notas do orientador
            data.mensagens.forEach(msg => {
                addMessageToChat(
                    msg.role,
                    msg.conteudo,
                    msg.thinking_process,
                    false,
                    null,
                    msg.arquivo,
                    msg.notas || null  // Passa as notas do orientador
                );
            });

            // Exibe notas gerais do chat se houver
            if (data.notas_gerais && data.notas_gerais.trim()) {
                showChatNotes(data.notas_gerais);
            }

            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-chat-id="${chatId}"]`)?.classList.add('active');

        } else {
            showError(data.message || 'Erro ao carregar histórico');
        }

    } catch (error) {
        APBIA.hideLoadingOverlay();
        showError('Erro ao carregar histórico');
        console.error('Erro:', error);
    }
}

function showChatNotes(notas) {

    const messagesContainer = document.getElementById('chatMessages');

    const notesDiv = document.createElement('div');
    notesDiv.className = 'chat-notes-banner';
    notesDiv.style.cssText = `
        background: rgba(255, 193, 7, 0.1);
        border: 2px solid var(--warning);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        animation: fadeIn 0.3s;
    `;

    notesDiv.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 1rem;">
            <i class="fas fa-sticky-note" style="color: var(--warning); font-size: 1.5rem; margin-top: 0.25rem;"></i>
            <div style="flex: 1;">
                <strong style="color: var(--warning); display: block; margin-bottom: 0.5rem;">
                    📝 Notas do Orientador sobre esta conversa:
                </strong>
                <p style="margin: 0; color: var(--text-primary); white-space: pre-wrap;">${notas}</p>
            </div>
        </div>
    `;

    // Insere no topo das mensagens
    messagesContainer.insertBefore(notesDiv, messagesContainer.firstChild);
}

async function handleFileUpload(e) {
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
    formData.append('message', `Analise este arquivo`);
    formData.append('chat_id', currentChatId || '');

    showThinking(true);

    try {
        const response = await fetch('/chat/upload-file', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        showThinking(false);

        if (data.success) {
            addMessageToChat('user', `Analise este arquivo`, null, false, null, {
                nome: data.file_info.name,
                tipo: data.file_info.type,
                tamanho: data.file_info.size,
                url: data.file_info.url
            });

            addMessageToChat('assistant', data.response, data.thinking_process);

            APBIA.showNotification('Arquivo processado com sucesso!', 'success');
        } else {
            showError(data.message || 'Erro ao processar arquivo');
        }

    } catch (error) {
        showThinking(false);
        showError('Erro ao enviar arquivo');
        console.error('Erro:', error);
    }

    e.target.value = '';
}

function clearChatMessages() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="welcome-message" id="welcomeMessage">
            <i class="fas fa-robot"></i>
            <h4>Continue sua conversa</h4>
            <p>Digite uma mensagem para continuar.</p>
        </div>
    `;
}

function showError(message) {
    APBIA.showNotification(message, 'error');
}

function showInfo(message) {
    APBIA.showNotification(message, 'info');
}

// Atalho de teclado - Ctrl+Enter para enviar
document.getElementById('chatInput')?.addEventListener('keydown', function (e) {
    if (e.ctrlKey && e.key === 'Enter') {
        document.getElementById('chatForm').dispatchEvent(new Event('submit'));
    }
});
