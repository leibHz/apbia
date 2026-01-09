// =============================================
// APBIA - Gemini Stats JavaScript
// Atualização em tempo real das estatísticas
// =============================================

let usageChart = null;

/**
 * Atualiza as estatísticas chamando a API
 */
async function refreshStats() {
    try {
        const response = await fetch('/admin/gemini-stats-api');
        const data = await response.json();
        
        if (data.error) {
            APBIA.showNotification('Erro ao carregar estatísticas', 'error');
            return;
        }
        
        updateStats(data);
        
    } catch (error) {
        console.error('Erro:', error);
        APBIA.showNotification('Erro ao atualizar estatísticas', 'error');
    }
}

/**
 * Atualiza os elementos DOM com os dados das estatísticas
 */
function updateStats(data) {
    const global = data.global;
    
    // RPM (Requests Per Minute)
    document.getElementById('rpm-current').textContent = global.requests_minute;
    document.getElementById('rpm-remaining').textContent = `Disponível: ${global.rpm_remaining}`;
    updateProgress('rpm', global.requests_minute, global.rpm_limit);
    
    // TPM (Tokens Per Minute)
    const tpmK = Math.round(global.tokens_minute / 1000);
    document.getElementById('tpm-current').textContent = tpmK + 'k';
    document.getElementById('tpm-remaining').textContent = `Disponível: ${Math.round(global.tpm_remaining / 1000)}k`;
    updateProgress('tpm', global.tokens_minute, global.tpm_limit);
    
    // RPD (Requests Per Day)
    document.getElementById('rpd-current').textContent = global.requests_today;
    document.getElementById('rpd-remaining').textContent = `Disponível: ${global.rpd_remaining}`;
    updateProgress('rpd', global.requests_today, global.rpd_limit);
    
    // Google Search
    document.getElementById('search-current').textContent = global.searches_today;
    document.getElementById('search-remaining').textContent = `Disponível: ${global.search_remaining}`;
    updateProgress('search', global.searches_today, global.search_limit);
    
    // Alertas
    updateAlerts(global);
}

/**
 * Atualiza as barras de progresso
 */
function updateProgress(type, current, limit) {
    const percent = Math.min((current / limit) * 100, 100);
    
    // Barra de progresso principal
    document.getElementById(`${type}-bar`).style.width = `${percent}%`;
    
    // Percentual no card de uso do sistema
    document.getElementById(`${type}-percent`).textContent = `${percent.toFixed(1)}%`;
    document.getElementById(`${type}-percent-bar`).style.width = `${percent}%`;
    
    // Cor da barra baseada no uso
    const bar = document.getElementById(`${type}-bar`);
    const percentBar = document.getElementById(`${type}-percent-bar`);
    
    // Remove todas as classes de cor
    bar.classList.remove('bg-primary', 'bg-warning', 'bg-info', 'bg-success', 'bg-danger');
    percentBar.classList.remove('bg-primary', 'bg-warning', 'bg-info', 'bg-success', 'bg-danger');
    
    // Adiciona cor baseada no percentual
    if (percent >= 90) {
        bar.classList.add('bg-danger');
        percentBar.classList.add('bg-danger');
    } else if (percent >= 75) {
        bar.classList.add('bg-warning');
        percentBar.classList.add('bg-warning');
    } else {
        // Mantém cor original do tipo
        const originalColor = type === 'rpm' ? 'bg-primary' :
                            type === 'tpm' ? 'bg-info' :
                            type === 'rpd' ? 'bg-success' : 'bg-warning';
        bar.classList.add(originalColor);
        percentBar.classList.add(originalColor);
    }
}

/**
 * Atualiza alertas de limite
 */
function updateAlerts(global) {
    const alertsDiv = document.getElementById('limit-alerts');
    alertsDiv.innerHTML = '';
    
    const alerts = [];
    
    // Alerta de RPM
    if (global.requests_minute >= global.rpm_limit * 0.9) {
        alerts.push({
            type: 'danger',
            message: `⚠️ RPM próximo do limite: ${global.requests_minute}/${global.rpm_limit}`
        });
    }
    
    // Alerta de RPD
    if (global.requests_today >= global.rpd_limit * 0.9) {
        alerts.push({
            type: 'warning',
            message: `⚠️ RPD próximo do limite: ${global.requests_today}/${global.rpd_limit}`
        });
    }
    
    // Alerta de Google Search
    if (global.searches_today >= global.search_limit * 0.9) {
        alerts.push({
            type: 'warning',
            message: `⚠️ Google Search próximo do limite: ${global.searches_today}/${global.search_limit}`
        });
    }
    
    // Renderiza alertas
    alerts.forEach(alert => {
        const div = document.createElement('div');
        div.className = `alert alert-${alert.type} alert-dismissible fade show`;
        div.innerHTML = `
            ${alert.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertsDiv.appendChild(div);
    });
}

// Inicializa e atualiza a cada 10 segundos
document.addEventListener('DOMContentLoaded', function() {
    refreshStats();
    setInterval(refreshStats, 10000);
});