// =============================================
// APBIA - Login JavaScript
// Validação e interatividade da página de login
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeLoginHandlers();
});

function initializeLoginHandlers() {
    // Validação em tempo real do BP
    const bpInput = document.getElementById('bp');
    if (bpInput) {
        bpInput.addEventListener('input', validateBP);
    }
    
    // Validação do formulário
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', validateLoginForm);
    }
}

/**
 * Valida o formato do BP em tempo real
 */
function validateBP(e) {
    const bp = e.target.value.toUpperCase();
    e.target.value = bp;
    
    const validIndicator = document.getElementById('bpValidIndicator');
    const invalidIndicator = document.getElementById('bpInvalidIndicator');
    const helpText = document.getElementById('bpHelpText');
    
    // Se vazio, esconde todos os indicadores
    if (bp.length === 0) {
        validIndicator.style.display = 'none';
        invalidIndicator.style.display = 'none';
        helpText.style.display = 'block';
        return;
    }
    
    // Regex: BP + 1-8 dígitos + letra opcional
    const regex = /^BP\d{1,8}[A-Z]?$/;
    
    if (regex.test(bp)) {
        validIndicator.style.display = 'block';
        invalidIndicator.style.display = 'none';
        helpText.style.display = 'none';
    } else {
        validIndicator.style.display = 'none';
        invalidIndicator.style.display = 'block';
        helpText.style.display = 'none';
    }
}

/**
 * Valida o formulário antes do envio
 */
function validateLoginForm(e) {
    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;
    const bp = document.getElementById('bp').value;
    
    // Valida email e senha
    if (!email || !senha) {
        e.preventDefault();
        alert('Por favor, preencha email e senha.');
        return false;
    }
    
    // Se BP foi preenchido, valida formato
    if (bp && bp.length > 0) {
        const regex = /^BP\d{1,8}[A-Z]?$/;
        if (!regex.test(bp)) {
            e.preventDefault();
            alert('Formato de BP inválido. Use: BP12345678X\nExemplos: BP123456, BP12345678A');
            return false;
        }
    }
    
    return true;
}