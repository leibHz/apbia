// =============================================
// APBIA - Admin Tipos de IA JavaScript
// static/js/admin_tipos_ia.js
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    // em breve faço algo aqui se precisar
});

/**
 * Abre modal
 */
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('active');
    }
}

/**
 * Fecha modal
 */
function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
        
        // Limpa campos
        if (id === 'addTipoModal') {
            document.getElementById('addNome').value = '';
        }
    }
}

/**
 * Abre modal de edição com dados preenchidos
 */
function editTipo(id, nome) {
    document.getElementById('editId').value = id;
    document.getElementById('editNome').value = nome;
    openModal('editTipoModal');
}

/**
 * Salva novo tipo de IA
 */
async function salvarNovoTipo() {
    const nome = document.getElementById('addNome').value.trim();
    
    if (!nome) {
        APBIA.showNotification('Nome é obrigatório', 'error');
        return;
    }
    
    APBIA.showLoadingOverlay('Criando tipo de IA...');
    
    try {
        const response = await fetch('/admin/tipos-ia/criar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome })
        });
        
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (data.success) {
            APBIA.showNotification(data.message, 'success');
            closeModal('addTipoModal');
            setTimeout(() => location.reload(), 1000);
        } else {
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao criar tipo de IA', 'error');
        console.error('Erro:', error);
    }
}

/**
 * Salva edição de tipo de IA
 */
async function salvarEdicaoTipo() {
    const id = document.getElementById('editId').value;
    const nome = document.getElementById('editNome').value.trim();
    
    if (!nome) {
        APBIA.showNotification('Nome é obrigatório', 'error');
        return;
    }
    
    APBIA.showLoadingOverlay('Atualizando tipo de IA...');
    
    try {
        const response = await fetch(`/admin/tipos-ia/editar/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome })
        });
        
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (data.success) {
            APBIA.showNotification(data.message, 'success');
            closeModal('editTipoModal');
            setTimeout(() => location.reload(), 1000);
        } else {
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao editar tipo de IA', 'error');
        console.error('Erro:', error);
    }
}

/**
 * Deleta tipo de IA
 */
async function deleteTipo(id, nome) {
    if (!confirm(`⚠️ Deseja realmente deletar o tipo "${nome}"?\n\nEsta ação é irreversível!`)) {
        return;
    }
    
    APBIA.showLoadingOverlay('Deletando tipo de IA...');
    
    try {
        const response = await fetch(`/admin/tipos-ia/deletar/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (data.success) {
            APBIA.showNotification(data.message, 'success');
            
            // Remove card com animação
            const cards = document.querySelectorAll('.stat-card');
            cards.forEach(card => {
                const cardTitle = card.querySelector('h6');
                if (cardTitle && cardTitle.textContent === nome) {
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.9)';
                    card.style.transition = 'all 0.3s ease';
                    
                    setTimeout(() => {
                        card.remove();
                    }, 300);
                }
            });
            
            setTimeout(() => location.reload(), 1000);
        } else {
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao deletar tipo de IA', 'error');
        console.error('Erro:', error);
    }
}

// Fecha modal ao clicar fora
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        const modalId = event.target.id;
        closeModal(modalId);
    }
});

// Fecha modal com ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal-overlay.active');
        modals.forEach(modal => {
            closeModal(modal.id);
        });
    }
});

// Previne submit dos forms (usamos funções customizadas)
document.getElementById('formAddTipo')?.addEventListener('submit', function(e) {
    e.preventDefault();
    salvarNovoTipo();
});

document.getElementById('formEditTipo')?.addEventListener('submit', function(e) {
    e.preventDefault();
    salvarEdicaoTipo();
});