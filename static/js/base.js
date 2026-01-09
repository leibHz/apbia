// =============================================
// APBIA - Base JavaScript (Extraído de base.html)
// Scripts globais para navbar, badges, etc.
// =============================================

/**
 * Atualiza badge de estatísticas Gemini na navbar
 */
async function updateStatsBadge() {
    try {
        const response = await fetch('/admin/gemini-stats-api');
        const data = await response.json();
        const badge = document.getElementById('gemini-stats-badge');
        
        if (badge && data && data.global) {
            const requests24h = data.global.requests_24h || 0;
            badge.textContent = requests24h;
            badge.title = `${requests24h} requisições (24h)`;
            
            // Remove spinner se estava carregando
            badge.classList.remove('spinner-border');
            badge.innerHTML = requests24h;
        }
    } catch (error) {
        console.error('Erro ao atualizar badge de stats:', error);
        const badge = document.getElementById('gemini-stats-badge');
        if (badge) {
            badge.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            badge.title = 'Erro ao carregar estatísticas';
        }
    }
}

/**
 * Inicializa atualizações automáticas do badge
 */
function initializeStatsBadge() {
    const badge = document.getElementById('gemini-stats-badge');
    
    if (badge) {
        // Atualiza imediatamente
        updateStatsBadge();
        
        // Atualiza a cada 30 segundos
        setInterval(updateStatsBadge, 30000);
    }
}

/**
 * Inicializa tooltips do Bootstrap em elementos do navbar
 */
function initializeNavbarTooltips() {
    const tooltips = document.querySelectorAll('.navbar [data-bs-toggle="tooltip"]');
    
    tooltips.forEach(element => {
        new bootstrap.Tooltip(element);
    });
}

/**
 * Fecha dropdown ao clicar fora
 */
function setupDropdownBehavior() {
    document.addEventListener('click', function(event) {
        const dropdowns = document.querySelectorAll('.navbar .dropdown-menu.show');
        
        dropdowns.forEach(dropdown => {
            if (!dropdown.parentElement.contains(event.target)) {
                const bsDropdown = bootstrap.Dropdown.getInstance(
                    dropdown.previousElementSibling
                );
                if (bsDropdown) {
                    bsDropdown.hide();
                }
            }
        });
    });
}

/**
 * Marca item ativo no menu baseado na URL atual
 */
function highlightActiveMenuItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        if (href === currentPath || 
            (currentPath.startsWith(href) && href !== '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Inicialização quando DOM estiver pronto
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa badge de stats se admin
    initializeStatsBadge();
    
    // Inicializa tooltips
    initializeNavbarTooltips();
    
    // Setup de dropdowns
    setupDropdownBehavior();
    
    // Destaca menu ativo
    highlightActiveMenuItem();
});