// ============================================
// APBIA - Relatório de Orientação
// Funções para impressão e salvamento de observações
// ============================================

/**
 * Exporta o relatório como PDF usando o diálogo de impressão do navegador
 */
function exportarPDF() {
    // Exibe notificação para o usuário
    if (typeof APBIA !== 'undefined' && APBIA.showNotification) {
        APBIA.showNotification('Preparando para impressão...', 'info');
    }
    // Aguarda um pouco para garantir que tudo está carregado e notificação foi exibida
    setTimeout(() => {
        window.print();
    }, 1000);
}

/**
 * Salva as observações do orientador sobre o orientado
 * @returns {Promise<void>}
 */
async function salvarObservacoes() {
    // Obtém o campo de observações
    const observacoesTextarea = document.getElementById('observacoesOrientador');

    // Valida se o campo existe
    if (!observacoesTextarea) {
        if (typeof APBIA !== 'undefined' && APBIA.showNotification) {
            APBIA.showNotification('Erro: Campo de observações não encontrado', 'error');
        }
        return;
    }

    const observacoes = observacoesTextarea.value.trim();

    // Obtém o ID do participante do atributo data
    const participanteId = observacoesTextarea.dataset.participanteId;

    // Valida se o ID do participante existe
    if (!participanteId) {
        if (typeof APBIA !== 'undefined' && APBIA.showNotification) {
            APBIA.showNotification('Erro: ID do participante não encontrado', 'error');
        }
        return;
    }

    // Exibe overlay de carregamento
    if (typeof APBIA !== 'undefined' && APBIA.showLoadingOverlay) {
        APBIA.showLoadingOverlay('Salvando observações...');
    }

    try {
        // Envia requisição para salvar observações
        const response = await fetch('/orientador/salvar-observacoes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                participante_id: parseInt(participanteId, 10),
                observacoes: observacoes
            })
        });

        // Verifica se a resposta foi bem-sucedida
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Processa a resposta JSON
        const data = await response.json();

        // Oculta overlay de carregamento
        if (typeof APBIA !== 'undefined' && APBIA.hideLoadingOverlay) {
            APBIA.hideLoadingOverlay();
        }

        // Exibe resultado
        if (data.success) {
            if (typeof APBIA !== 'undefined' && APBIA.showNotification) {
                APBIA.showNotification('Observações salvas com sucesso!', 'success');
            }

            // Atualiza a div de impressão com o novo conteúdo
            const observacoesPrint = document.querySelector('.observacoes-print');
            if (observacoesPrint) {
                observacoesPrint.textContent = observacoes || 'Nenhuma observação registrada.';
            }
        } else {
            if (typeof APBIA !== 'undefined' && APBIA.showNotification) {
                APBIA.showNotification('Erro: ' + (data.message || 'Erro desconhecido'), 'error');
            }
        }
    } catch (error) {
        // Oculta overlay em caso de erro
        if (typeof APBIA !== 'undefined' && APBIA.hideLoadingOverlay) {
            APBIA.hideLoadingOverlay();
        }

        // Exibe notificação de erro
        if (typeof APBIA !== 'undefined' && APBIA.showNotification) {
            APBIA.showNotification('Erro ao salvar observações', 'error');
        }
    }
}
