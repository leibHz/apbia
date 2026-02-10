// =============================================
// APBIA - Admin Usuários JavaScript
// =============================================

// Busca em tempo real
document.getElementById('searchInput')?.addEventListener('input', debounceSearch);

function debounceSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    filterTable(searchTerm, document.getElementById('filterTipo').value);
}

// Filtro por tipo
document.getElementById('filterTipo')?.addEventListener('change', function() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    filterTable(searchTerm, this.value);
});

function filterTable(searchTerm, tipo) {
    const rows = document.querySelectorAll('#usersTable tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const userTipo = row.querySelector('.badge').textContent.includes('Admin') ? '1' :
                        row.querySelector('.badge').textContent.includes('Participante') ? '2' :
                        row.querySelector('.badge').textContent.includes('Orientador') ? '3' : '4';
        
        const matchSearch = !searchTerm || text.includes(searchTerm);
        const matchTipo = !tipo || userTipo === tipo;
        
        row.style.display = (matchSearch && matchTipo) ? '' : 'none';
    });
}

// Adicionar usuário
document.getElementById('saveUserBtn')?.addEventListener('click', async function() {
    const form = document.getElementById('addUserForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // Validação de BP
    const tipoId = parseInt(data.tipo_usuario_id);
    if ([2, 3].includes(tipoId) && !data.numero_inscricao) {
        APBIA.showNotification('BP é obrigatório para participantes e orientadores', 'error');
        return;
    }
    
    if (data.numero_inscricao) {
        const bpRegex = /^BP\d{1,8}[A-Z]?$/;
        if (!bpRegex.test(data.numero_inscricao.toUpperCase())) {
            APBIA.showNotification('BP inválido. Use o formato: BP12345678X', 'error');
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
            APBIA.showNotification('Usuário criado com sucesso!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            APBIA.showNotification('Erro: ' + result.message, 'error');
        }
    } catch (error) {
        APBIA.showNotification('Erro ao criar usuário', 'error');
    }
});

// Atualiza indicador de BP obrigatório baseado no tipo
document.querySelector('select[name="tipo_usuario_id"]')?.addEventListener('change', function() {
    const tipoId = parseInt(this.value);
    const bpRequired = document.getElementById('addBpRequired');
    const bpHelp = document.getElementById('addBpHelp');
    const bpInput = document.getElementById('addBP');
    
    if ([2, 3].includes(tipoId)) {
        bpRequired.style.display = 'inline';
        bpHelp.textContent = 'Obrigatório para participantes e orientadores. Formato: BP12345678X';
        bpHelp.classList.add('text-danger');
        bpInput.required = true;
    } else {
        bpRequired.style.display = 'none';
        bpHelp.textContent = 'Opcional para administradores. Formato: BP12345678X';
        bpHelp.classList.remove('text-danger');
        bpInput.required = false;
    }
});

// Formata BP em tempo real
document.getElementById('addBP')?.addEventListener('input', function(e) {
    e.target.value = e.target.value.toUpperCase();
});

// Editar usuário
document.querySelectorAll('.edit-user').forEach(btn => {
    btn.addEventListener('click', function() {
        const userId = this.dataset.userId;
        const row = this.closest('tr');
        
        // Preenche o formulário
        document.getElementById('editUserId').value = userId;
        document.getElementById('editNome').value = row.cells[1].textContent.trim();
        document.getElementById('editEmail').value = row.cells[2].textContent;
        
        // Abre modal
        const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
        modal.show();
    });
});

// Atualizar usuário
document.getElementById('updateUserBtn')?.addEventListener('click', async function() {
    const userId = document.getElementById('editUserId').value;
    const form = document.getElementById('editUserForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await fetch(`/admin/editar-usuario/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            APBIA.showNotification('Usuário atualizado!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            APBIA.showNotification('Erro: ' + result.message, 'error');
        }
    } catch (error) {
        APBIA.showNotification('Erro ao atualizar usuário', 'error');
    }
});

// Deletar usuário
document.querySelectorAll('.delete-user').forEach(btn => {
    btn.addEventListener('click', async function() {
        if (!confirm(this.dataset.confirm)) return;
        
        const userId = this.dataset.userId;
        
        try {
            const response = await fetch(`/admin/deletar-usuario/${userId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                APBIA.showNotification('Usuário deletado!', 'success');
                this.closest('tr').remove();
            } else {
                APBIA.showNotification('Erro: ' + result.message, 'error');
            }
        } catch (error) {
            APBIA.showNotification('Erro ao deletar usuário', 'error');
        }
    });
});

// Debounce helper
function debounceSearch(e) {
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
        const searchTerm = e.target.value.toLowerCase();
        filterTable(searchTerm, document.getElementById('filterTipo').value);
    }, 300);
}