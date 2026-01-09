/**
 * Guest Projetos - Gerenciamento de projetos em localStorage
 * APBIA - Modo Anônimo
 */

// Fallback para APBIA se não estiver disponível
if (typeof APBIA === 'undefined') {
    window.APBIA = {
        showNotification: function (msg, type) {
            console.log(`[${type}] ${msg}`);
            alert(msg);
        },
        showLoadingOverlay: function (msg) { console.log('Loading:', msg); },
        hideLoadingOverlay: function () { console.log('Hide loading'); }
    };
}

// ========================================
// INICIALIZAÇÃO
// ========================================
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Guest Projetos JS carregado');

    // Verifica se está editando projeto existente
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('id');

    if (projectId) {
        loadProjectForEdit(projectId);
    }

    initGuestProjetosHandlers();
    console.log('✅ Handlers inicializados');
});

function loadProjectForEdit(projectId) {
    const projectsJson = localStorage.getItem('apbia_guest_projects');
    const projects = projectsJson ? JSON.parse(projectsJson) : [];
    const project = projects.find(p => p.id === projectId);

    if (!project) {
        APBIA.showNotification('Projeto não encontrado', 'error');
        return;
    }

    // Preenche campos
    document.getElementById('nome').value = project.nome || '';
    document.getElementById('categoria').value = project.categoria || '';
    document.getElementById('ano_edicao').value = project.ano_edicao || 2025;
    document.getElementById('resumo').value = project.resumo || '';
    document.getElementById('palavras_chave').value = project.palavras_chave || '';
    document.getElementById('introducao').value = project.introducao || '';
    document.getElementById('objetivo_geral').value = project.objetivo_geral || '';
    document.getElementById('metodologia').value = project.metodologia || '';
    document.getElementById('resultados_esperados').value = project.resultados_esperados || '';
    document.getElementById('referencias_bibliograficas').value = project.referencias_bibliograficas || '';

    // Objetivos específicos
    if (project.objetivos_especificos && project.objetivos_especificos.length > 0) {
        const container = document.getElementById('objetivos-especificos-container');
        container.innerHTML = '';

        project.objetivos_especificos.forEach((obj, index) => {
            const div = document.createElement('div');
            div.className = 'objetivo-item';
            div.innerHTML = `
                <span>${index + 1}.</span>
                <input type="text" class="form-control objetivo-especifico" value="${obj}">
                <button type="button" class="btn-remover-objetivo">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(div);
        });
    }

    // Cronograma
    if (project.cronograma && project.cronograma.length > 0) {
        const tbody = document.getElementById('cronogramaBody');
        tbody.innerHTML = '';
        const meses = ['Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov'];

        project.cronograma.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><input type="text" value="${item.etapa}"></td>
                ${meses.map(mes => `<td><input type="checkbox" ${item.meses.includes(mes) ? 'checked' : ''}></td>`).join('')}
                <td><button type="button" class="btn-remover-etapa"><i class="fas fa-times"></i></button></td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Continuação
    if (project.eh_continuacao) {
        document.getElementById('eh_continuacao').checked = true;
        document.getElementById('continuacao-fields').style.display = 'block';
        document.getElementById('projeto_anterior_titulo').value = project.projeto_anterior_titulo || '';
        document.getElementById('projeto_anterior_resumo').value = project.projeto_anterior_resumo || '';
        document.getElementById('projeto_anterior_inicio').value = project.projeto_anterior_inicio || '';
        document.getElementById('projeto_anterior_termino').value = project.projeto_anterior_termino || '';
    }

    // Guarda ID para edição
    document.getElementById('formProjeto').dataset.projectId = projectId;
    document.getElementById('formProjeto').dataset.geradoPorIa = project.gerado_por_ia || 'false';

    // Atualiza contador
    updateResumoCount();
}

// ========================================
// HANDLERS
// ========================================
function initGuestProjetosHandlers() {
    // Contador de caracteres
    const resumoInput = document.getElementById('resumo');
    if (resumoInput) {
        resumoInput.addEventListener('input', updateResumoCount);
    }

    // Toggle continuação
    const ehContinuacao = document.getElementById('eh_continuacao');
    if (ehContinuacao) {
        ehContinuacao.addEventListener('change', function () {
            document.getElementById('continuacao-fields').style.display = this.checked ? 'block' : 'none';
        });
    }

    // Adicionar objetivo
    const addObjetivo = document.getElementById('addObjetivo');
    if (addObjetivo) {
        addObjetivo.addEventListener('click', addObjetivoEspecifico);
    }

    // Adicionar etapa
    const addEtapa = document.getElementById('addEtapa');
    if (addEtapa) {
        addEtapa.addEventListener('click', addEtapaCronograma);
    }

    // Gerar ideias
    const btnGerarIdeias = document.getElementById('btnGerarIdeias');
    if (btnGerarIdeias) {
        btnGerarIdeias.addEventListener('click', handleGuestGerarIdeias);
    }

    // Autocompletar
    document.querySelectorAll('.btn-ia-autocompletar').forEach(btn => {
        btn.addEventListener('click', handleGuestAutocompletar);
    });

    // Salvar
    const formProjeto = document.getElementById('formProjeto');
    if (formProjeto) {
        formProjeto.addEventListener('submit', handleGuestSalvarProjeto);
    }
}

function updateResumoCount() {
    const resumo = document.getElementById('resumo');
    const count = document.getElementById('resumo-count');
    if (resumo && count) {
        count.textContent = `${resumo.value.length}/2000`;
    }
}

// ========================================
// OBJETIVO E CRONOGRAMA
// ========================================
function addObjetivoEspecifico() {
    const container = document.getElementById('objetivos-especificos-container');
    if (!container) return;

    const count = container.children.length + 1;

    const div = document.createElement('div');
    div.className = 'objetivo-item';
    div.innerHTML = `
        <span>${count}.</span>
        <input type="text" class="form-control objetivo-especifico" 
               placeholder="Objetivo específico ${count}...">
        <button type="button" class="btn-remover-objetivo">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(div);

    div.querySelector('.btn-remover-objetivo').addEventListener('click', function () {
        div.remove();
        renumerarObjetivos();
    });
}

function renumerarObjetivos() {
    const objetivos = document.querySelectorAll('.objetivo-item');
    objetivos.forEach((obj, index) => {
        obj.querySelector('span').textContent = `${index + 1}.`;
    });
}

function addEtapaCronograma() {
    const tbody = document.getElementById('cronogramaBody');
    if (!tbody) return;

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" placeholder="Nova etapa"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td><input type="checkbox"></td>
        <td>
            <button type="button" class="btn-remover-etapa">
                <i class="fas fa-times"></i>
            </button>
        </td>
    `;

    tbody.appendChild(tr);

    tr.querySelector('.btn-remover-etapa').addEventListener('click', function () {
        tr.remove();
    });
}

// ========================================
// GERAR IDEIAS
// ========================================
async function handleGuestGerarIdeias() {
    if (!confirm('Gerar ideias baseadas em projetos vencedores?\n\n⚠️ Processo pode levar 20-40 segundos')) {
        return;
    }

    showLoading('Analisando projetos vencedores...');

    try {
        const response = await fetch('/guest/projetos/gerar-ideias', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        hideLoading();

        if (data.success) {
            mostrarIdeias(data.ideias, data.metadata);
        } else {
            APBIA.showNotification('Erro ao gerar ideias: ' + data.message, 'error');
        }

    } catch (error) {
        hideLoading();
        APBIA.showNotification('Erro ao conectar com IA', 'error');
    }
}

function mostrarIdeias(ideias, metadata) {
    let html = '';

    if (metadata && metadata.modo_bragantec) {
        html += `
            <div class="alert alert-success mb-4">
                <strong><i class="fas fa-trophy"></i> Análise Completa Realizada</strong>
                <p class="mb-0">Modo Bragantec ativado com histórico completo.</p>
            </div>
        `;
    }

    if (typeof ideias === 'object') {
        html += '<div class="row g-3">';

        for (const [categoria, ideia] of Object.entries(ideias)) {
            const badgeColor =
                categoria === 'Informática' ? 'primary' :
                    categoria === 'Engenharias' ? 'success' :
                        categoria === 'Ciências da Natureza e Exatas' ? 'info' : 'warning';

            html += `
                <div class="col-md-6">
                    <div class="card h-100 shadow-sm">
                        <div class="card-header bg-${badgeColor} text-white">
                            <strong><i class="fas fa-trophy"></i> ${categoria}</strong>
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">${ideia.titulo || 'Sem título'}</h5>
                            <p class="card-text">${ideia.resumo || ''}</p>
                            ${ideia.palavras_chave ? `<p><small><i class="fas fa-tags"></i> ${ideia.palavras_chave}</small></p>` : ''}
                        </div>
                        <div class="card-footer">
                            <button class="btn btn-sm btn-success w-100 usar-ideia" 
                                    data-ideia='${JSON.stringify(ideia).replace(/'/g, "&apos;")}'
                                    data-categoria="${categoria}">
                                <i class="fas fa-check-circle"></i> Usar Esta Ideia
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        html += '</div>';
    } else {
        html += `<pre style="white-space: pre-wrap;">${ideias}</pre>`;
    }

    document.getElementById('ideiasContent').innerHTML = html;

    // Handlers
    document.querySelectorAll('.usar-ideia').forEach(btn => {
        btn.addEventListener('click', function () {
            const ideia = JSON.parse(this.dataset.ideia);
            const categoria = this.dataset.categoria;
            preencherComIdeia(ideia, categoria);
            document.getElementById('modalIdeias').style.display = 'none';
        });
    });

    document.getElementById('modalIdeias').style.display = 'flex';
}

function preencherComIdeia(ideia, categoria) {
    document.getElementById('nome').value = ideia.titulo || '';
    document.getElementById('categoria').value = categoria || '';
    document.getElementById('resumo').value = ideia.resumo || '';
    document.getElementById('palavras_chave').value = ideia.palavras_chave || '';

    document.getElementById('formProjeto').dataset.geradoPorIa = 'true';

    updateResumoCount();
    APBIA.showNotification('Ideia aplicada! Revise o conteúdo.', 'success');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ========================================
// AUTOCOMPLETAR
// ========================================
async function handleGuestAutocompletar() {
    console.log('🤖 Autocompletar clicado');
    console.log('this:', this);
    console.log('this.dataset:', this.dataset);

    const campo = this.dataset.campo;
    console.log('Campo:', campo);

    if (!campo) {
        APBIA.showNotification('Campo não especificado', 'error');
        return;
    }

    if (!confirm(`Gerar conteúdo para: ${campo}?`)) return;

    showLoading(`Gerando ${campo}...`);

    try {
        const projetoParcial = {
            nome: document.getElementById('nome')?.value || '',
            categoria: document.getElementById('categoria')?.value || '',
            resumo: document.getElementById('resumo')?.value || '',
            palavras_chave: document.getElementById('palavras_chave')?.value || ''
        };

        console.log('Enviando para /guest/projetos/autocompletar:', { campos: [campo], projeto: projetoParcial });

        const response = await fetch('/guest/projetos/autocompletar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                campos: [campo],
                projeto: projetoParcial
            })
        });

        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);

        hideLoading();

        if (data.success) {
            aplicarConteudoGerado(campo, data.conteudo);
            APBIA.showNotification('Conteúdo gerado!', 'success');
        } else {
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }

    } catch (error) {
        console.error('Erro autocompletar:', error);
        hideLoading();
        APBIA.showNotification('Erro ao conectar com IA: ' + error.message, 'error');
    }
}

function aplicarConteudoGerado(campo, conteudo) {
    if (typeof conteudo === 'string') {
        const el = document.getElementById(campo);
        if (el) el.value = conteudo;
        return;
    }

    if (campo === 'resumo' && conteudo.resumo) {
        document.getElementById('resumo').value = conteudo.resumo;
        updateResumoCount();
    } else if (campo === 'introducao' && conteudo.introducao) {
        document.getElementById('introducao').value = conteudo.introducao;
    } else if (campo === 'objetivos' && conteudo.objetivo_geral) {
        document.getElementById('objetivo_geral').value = conteudo.objetivo_geral;
    } else if (campo === 'metodologia' && conteudo.metodologia) {
        document.getElementById('metodologia').value = conteudo.metodologia;
    } else if (campo === 'resultados_esperados' && conteudo.resultados_esperados) {
        document.getElementById('resultados_esperados').value = conteudo.resultados_esperados;
    }
}

// ========================================
// SALVAR PROJETO
// ========================================
function handleGuestSalvarProjeto(e) {
    e.preventDefault();

    const form = e.target;
    const submitBtn = e.submitter;
    const status = submitBtn?.dataset?.status || 'rascunho';

    const dados = coletarDadosCompletos(status);

    // Verifica se é edição
    const existingId = form.dataset.projectId;

    // Salva no localStorage
    const projectsJson = localStorage.getItem('apbia_guest_projects');
    let projects = projectsJson ? JSON.parse(projectsJson) : [];

    if (existingId) {
        // Atualiza existente
        const index = projects.findIndex(p => p.id === existingId);
        if (index !== -1) {
            dados.id = existingId;
            dados.data_criacao = projects[index].data_criacao;
            projects[index] = dados;
        }
    } else {
        // Novo projeto
        dados.id = 'guest_project_' + Date.now();
        dados.data_criacao = new Date().toISOString();
        projects.unshift(dados);
    }

    localStorage.setItem('apbia_guest_projects', JSON.stringify(projects));

    APBIA.showNotification('Projeto salvo no navegador!', 'success');

    setTimeout(() => {
        window.location.href = '/guest/projetos';
    }, 1000);
}

function coletarDadosCompletos(status) {
    // Objetivos específicos
    const objetivosEspecificos = Array.from(
        document.querySelectorAll('.objetivo-especifico')
    ).map(input => input.value).filter(v => v.trim());

    // Cronograma
    const cronograma = [];
    const meses = ['Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov'];

    document.querySelectorAll('#cronogramaBody tr').forEach(tr => {
        const etapaInput = tr.querySelector('input[type="text"]');
        if (!etapaInput || !etapaInput.value.trim()) return;

        const checkboxes = tr.querySelectorAll('input[type="checkbox"]');
        const mesesMarcados = [];

        checkboxes.forEach((cb, idx) => {
            if (cb.checked && idx < meses.length) {
                mesesMarcados.push(meses[idx]);
            }
        });

        cronograma.push({
            etapa: etapaInput.value.trim(),
            meses: mesesMarcados
        });
    });

    const geradoPorIA = document.getElementById('formProjeto')?.dataset.geradoPorIa === 'true';

    return {
        nome: document.getElementById('nome')?.value || '',
        categoria: document.getElementById('categoria')?.value || '',
        ano_edicao: parseInt(document.getElementById('ano_edicao')?.value) || 2025,
        resumo: document.getElementById('resumo')?.value || '',
        palavras_chave: document.getElementById('palavras_chave')?.value || '',
        introducao: document.getElementById('introducao')?.value || '',
        objetivo_geral: document.getElementById('objetivo_geral')?.value || '',
        objetivos_especificos: objetivosEspecificos,
        metodologia: document.getElementById('metodologia')?.value || '',
        cronograma: cronograma,
        resultados_esperados: document.getElementById('resultados_esperados')?.value || '',
        referencias_bibliograficas: document.getElementById('referencias_bibliograficas')?.value || '',
        eh_continuacao: document.getElementById('eh_continuacao')?.checked || false,
        projeto_anterior_titulo: document.getElementById('projeto_anterior_titulo')?.value || '',
        projeto_anterior_resumo: document.getElementById('projeto_anterior_resumo')?.value || '',
        projeto_anterior_inicio: document.getElementById('projeto_anterior_inicio')?.value || null,
        projeto_anterior_termino: document.getElementById('projeto_anterior_termino')?.value || null,
        status: status,
        gerado_por_ia: geradoPorIA
    };
}

// ========================================
// UI HELPERS
// ========================================
function showLoading(message) {
    const loadingEl = document.getElementById('loadingIA');
    const messageEl = document.getElementById('loadingMessage');

    if (loadingEl) {
        loadingEl.style.display = 'flex';
        if (messageEl) messageEl.textContent = message;
    }
}

function hideLoading() {
    const loadingEl = document.getElementById('loadingIA');
    if (loadingEl) loadingEl.style.display = 'none';
}
