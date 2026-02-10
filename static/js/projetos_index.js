// =============================================
// APBIA - Projetos Index JavaScript
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    initProjetosHandlers();
});

function initProjetosHandlers() {
    // Gerar PDF
    document.querySelectorAll('.gerar-pdf').forEach(btn => {
        btn.addEventListener('click', handleGerarPDF);
    });

    // Deletar projeto
    document.querySelectorAll('.deletar-projeto').forEach(btn => {
        btn.addEventListener('click', handleDeletarProjeto);
    });
}

/**
 * Gera PDF do projeto
 */
async function handleGerarPDF() {
    const projetoId = this.dataset.projetoId;
    
    APBIA.showLoadingOverlay('Gerando PDF...');
    
    try {
        // Download direto
        window.location.href = `/projetos/gerar-pdf/${projetoId}`;
        
        setTimeout(() => {
            APBIA.hideLoadingOverlay();
            APBIA.showNotification('PDF gerado com sucesso!', 'success');
        }, 2000);
        
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao gerar PDF', 'error');
        console.error('Erro ao gerar PDF:', error);
    }
}

/**
 * Deleta um projeto
 */
async function handleDeletarProjeto() {
    if (!confirm('Deseja realmente deletar este projeto? Esta ação não pode ser desfeita.')) {
        return;
    }
    
    const projetoId = this.dataset.projetoId;
    const card = this.closest('.projeto-card');
    
    APBIA.showLoadingOverlay('Deletando projeto...');
    
    try {
        const response = await fetch(`/projetos/deletar/${projetoId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (data.success) {
            // Animação de saída
            card.style.opacity = '0';
            card.style.transform = 'scale(0.9)';
            card.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                card.remove();
                APBIA.showNotification('Projeto deletado com sucesso!', 'success');
                
                // Verifica se não há mais projetos
                const projetos = document.querySelectorAll('.projeto-card');
                if (projetos.length === 0) {
                    location.reload();
                }
            }, 300);
        } else {
            APBIA.showNotification('Erro ao deletar: ' + (data.message || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao deletar projeto', 'error');
        console.error('Erro ao deletar:', error);
    }
}

/**
 * Tooltip para badges de IA
 */
document.querySelectorAll('.badge.bg-info').forEach(badge => {
    badge.setAttribute('title', 'Este projeto foi gerado com auxílio da IA');
    badge.style.cursor = 'help';
});