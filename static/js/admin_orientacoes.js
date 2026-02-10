// =============================================
// APBIA - Admin Orientações JavaScript
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    initOrientacoesHandlers();
});

function initOrientacoesHandlers() {
    // Seleção de projeto
    const projetoSelect = document.getElementById('projetoSelect');
    if (projetoSelect) {
        projetoSelect.addEventListener('change', handleProjetoChange);
    }
    
    // Seleção de orientador
    const orientadorSelect = document.getElementById('orientadorSelect');
    if (orientadorSelect) {
        orientadorSelect.addEventListener('change', handleOrientadorChange);
    }
    
    // Confirmar orientação
    const btnConfirmar = document.getElementById('btnConfirmarOrientacao');
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', confirmarOrientacao);
    }
    
    // Remover orientação
    document.querySelectorAll('.remover-orientacao').forEach(btn => {
        btn.addEventListener('click', removerOrientacao);
    });
    
    // Filtros
    const filtroOrientador = document.getElementById('filtroOrientador');
    const filtroProjeto = document.getElementById('filtroProjeto');
    
    if (filtroOrientador) {
        filtroOrientador.addEventListener('change', filtrarTabela);
    }
    
    if (filtroProjeto) {
        filtroProjeto.addEventListener('change', filtrarTabela);
    }
}

function handleProjetoChange() {
    const projetoId = this.value;
    const passo2 = document.getElementById('passo2');
    const passo3 = document.getElementById('passo3');
    const projetoInfo = document.getElementById('projetoInfo');
    
    if (projetoId) {
        const option = this.options[this.selectedIndex];
        const nome = option.dataset.nome;
        const categoria = option.dataset.categoria;
        
        document.getElementById('projetoNome').textContent = nome;
        document.getElementById('projetoCategoria').textContent = `Categoria: ${categoria}`;
        
        projetoInfo.style.display = 'block';
        projetoInfo.classList.add('fade-in');
        
        passo2.style.display = 'block';
        passo2.classList.add('fade-in');
        
        // Carrega participantes do projeto
        carregarParticipantesProjeto(projetoId);
    } else {
        projetoInfo.style.display = 'none';
        passo2.style.display = 'none';
        passo3.style.display = 'none';
    }
}

function handleOrientadorChange() {
    const passo3 = document.getElementById('passo3');
    
    if (this.value) {
        passo3.style.display = 'block';
        passo3.classList.add('fade-in');
    } else {
        passo3.style.display = 'none';
    }
}

async function carregarParticipantesProjeto(projetoId) {
    try {
        const response = await fetch(`/admin/projeto/${projetoId}/participantes`);
        const data = await response.json();
        
        const lista = document.getElementById('participantesLista');
        lista.innerHTML = '';
        
        if (data.participantes && data.participantes.length > 0) {
            data.participantes.forEach(p => {
                lista.innerHTML += `
                    <div class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${p.nome_completo}</strong>
                                <br>
                                <small class="text-muted">${p.email} | BP: ${p.numero_inscricao}</small>
                            </div>
                            <span class="badge bg-success">
                                <i class="fas fa-check"></i> No projeto
                            </span>
                        </div>
                    </div>
                `;
            });
        } else {
            lista.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Este projeto ainda não tem participantes associados.
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar participantes:', error);
        APBIA.showNotification('Erro ao carregar participantes', 'error');
    }
}

async function confirmarOrientacao() {
    const projetoId = document.getElementById('projetoSelect').value;
    const orientadorId = document.getElementById('orientadorSelect').value;
    
    if (!projetoId || !orientadorId) {
        APBIA.showNotification('Selecione projeto e orientador', 'error');
        return;
    }
    
    if (!confirm('Confirma a criação desta orientação?')) return;
    
    APBIA.showLoadingOverlay('Criando orientação...');
    
    try {
        const response = await fetch('/admin/orientacoes/criar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                projeto_id: parseInt(projetoId),
                orientador_id: parseInt(orientadorId)
            })
        });
        
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (data.success) {
            APBIA.showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao criar orientação', 'error');
        console.error(error);
    }
}

async function removerOrientacao() {
    if (!confirm('Remover esta orientação?')) return;
    
    const orientadorId = this.dataset.orientadorId;
    const projetoId = this.dataset.projetoId;
    const row = this.closest('tr');
    
    try {
        const response = await fetch('/admin/orientacoes/remover', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                orientador_id: parseInt(orientadorId),
                projeto_id: parseInt(projetoId)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            APBIA.showNotification(data.message, 'success');
            row.classList.add('fade-out');
            setTimeout(() => row.remove(), 300);
        } else {
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.showNotification('Erro ao remover orientação', 'error');
        console.error(error);
    }
}

function filtrarTabela() {
    const orientadorId = document.getElementById('filtroOrientador').value;
    const projetoId = document.getElementById('filtroProjeto').value;
    
    const rows = document.querySelectorAll('#tabelaOrientacoes tbody tr');
    
    rows.forEach(row => {
        let mostrar = true;
        const texto = row.textContent.toLowerCase();
        
        if (orientadorId && !texto.includes(orientadorId.toLowerCase())) {
            mostrar = false;
        }
        
        if (projetoId && !texto.includes(projetoId.toLowerCase())) {
            mostrar = false;
        }
        
        row.style.display = mostrar ? '' : 'none';
    });
}

// Animação de fade out
const style = document.createElement('style');
style.textContent = `
    .fade-out {
        animation: fadeOut 0.3s ease-out forwards;
    }
    
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(-20px);
        }
    }
`;
document.head.appendChild(style);