// =============================================
// APBIA - Admin Dashboard JavaScript
// =============================================

// Toggle IA Status
document.getElementById('toggleIABtn')?.addEventListener('click', async function() {
    if (!confirm('Deseja alterar o status da IA?')) return;
    
    try {
        const response = await fetch('/admin/toggle-ia', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            location.reload();
        } else {
            alert('Erro: ' + data.message);
        }
    } catch (error) {
        alert('Erro ao alterar status da IA');
    }
});

// Adicionar usuário
document.getElementById('saveUserBtn')?.addEventListener('click', async function() {
    const form = document.getElementById('addUserForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Validação de BP
    const tipoId = parseInt(data.tipo_usuario_id);
    if ([2, 3].includes(tipoId) && !data.numero_inscricao) {
        alert('BP é obrigatório para participantes e orientadores');
        return;
    }
    
    if (data.numero_inscricao) {
        const bpRegex = /^BP\d{1,8}[A-Z]?$/;
        if (!bpRegex.test(data.numero_inscricao.toUpperCase())) {
            alert('BP inválido. Use o formato: BP12345678X\nExemplos: BP123456, BP12345678A');
            return;
        }
    }
    
    try {
        const response = await fetch('/admin/adicionar-usuario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Usuário criado com sucesso!');
            location.reload();
        } else {
            alert('Erro: ' + result.message);
        }
    } catch (error) {
        alert('Erro ao criar usuário');
    }
});