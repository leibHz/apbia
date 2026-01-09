// =============================================
// APBIA - Perfil JavaScript
// Funcionalidades da página de perfil do usuário
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    initializePerfilHandlers();
});

function initializePerfilHandlers() {
    // Formulário de perfil
    const formPerfil = document.getElementById('formPerfil');
    if (formPerfil) {
        formPerfil.addEventListener('submit', handleSalvarPerfil);
    }
    
    // Formulário de senha
    const formSenha = document.getElementById('formSenha');
    if (formSenha) {
        formSenha.addEventListener('submit', handleAlterarSenha);
    }
    
    // Validação em tempo real do apelido
    const apelidoInput = document.getElementById('apelido');
    if (apelidoInput) {
        apelidoInput.addEventListener('input', validateApelido);
    }
}

/**
 * Salva as alterações do perfil
 */
async function handleSalvarPerfil(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);
    
    // Valida dados básicos
    if (!data.nome_completo || !data.email) {
        APBIA.showNotification('Por favor, preencha nome e email', 'error');
        return;
    }
    
    APBIA.showLoadingOverlay('Salvando perfil...');
    
    try {
        const response = await fetch(window.location.pathname, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (result.success) {
            APBIA.showNotification(result.message || 'Perfil atualizado com sucesso!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            APBIA.showNotification('Erro: ' + (result.message || 'Erro ao salvar perfil'), 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao salvar perfil', 'error');
        console.error('Erro:', error);
    }
}

/**
 * Altera a senha do usuário
 */
async function handleAlterarSenha(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = Object.fromEntries(formData);
    
    // Valida senhas
    if (!data.senha_atual || !data.nova_senha || !data.confirmar_senha) {
        APBIA.showNotification('Preencha todos os campos de senha', 'error');
        return;
    }
    
    if (data.nova_senha !== data.confirmar_senha) {
        APBIA.showNotification('As senhas não coincidem', 'error');
        return;
    }
    
    if (data.nova_senha.length < 6) {
        APBIA.showNotification('A nova senha deve ter no mínimo 6 caracteres', 'error');
        return;
    }
    
    APBIA.showLoadingOverlay('Alterando senha...');
    
    try {
        // Extrai base_url da URL atual
        const baseUrl = window.location.origin;
        
        const response = await fetch(`${baseUrl}/perfil/alterar-senha`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (result.success) {
            APBIA.showNotification(result.message || 'Senha alterada com sucesso!', 'success');
            this.reset();
        } else {
            APBIA.showNotification('Erro: ' + (result.message || 'Erro ao alterar senha'), 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao alterar senha', 'error');
        console.error('Erro:', error);
    }
}

/**
 * Valida o apelido em tempo real
 */
function validateApelido(e) {
    const apelido = e.target.value.trim();
    
    if (apelido.length === 0) {
        e.target.classList.remove('is-valid', 'is-invalid');
        return;
    }
    
    // Valida comprimento (máximo 50 caracteres)
    if (apelido.length > 50) {
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
        return;
    }
    
    // Validação básica: apenas letras, números, espaços e alguns caracteres especiais
    const regex = /^[a-zA-ZÀ-ÿ0-9\s\.\_\-]+$/;
    
    if (regex.test(apelido)) {
        e.target.classList.add('is-valid');
        e.target.classList.remove('is-invalid');
    } else {
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
    }
}

/**
 * Adiciona loading state aos botões
 */
function setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.classList.add('btn-loading');
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processando...';
    } else {
        button.disabled = false;
        button.classList.remove('btn-loading');
        button.innerHTML = button.dataset.originalText || button.innerHTML;
    }
}