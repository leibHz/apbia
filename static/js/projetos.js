// =========================================
// APBIA - JavaScript para Projetos
// =========================================


// ===== VALIDAÇÃO DE DEPENDÊNCIAS =====
function checkDependencies() {
    const missing = [];
    
    if (typeof APBIA === 'undefined') {
        missing.push('APBIA global object');
    }
    
    if (!document.getElementById('loadingIA')) {
        missing.push('loadingIA element');
    }
    
    if (missing.length > 0) {
        console.error('❌ DEPENDÊNCIAS FALTANDO:', missing);
        return false;
    }
    
    return true;
}

// ===== HELPERS COM FALLBACK =====
function showLoading(message) {
    const loadingEl = document.getElementById('loadingIA');
    const messageEl = document.getElementById('loadingMessage');
    
    if (loadingEl) {
        loadingEl.style.display = 'flex';
        if (messageEl) {
            messageEl.textContent = message;
        }
    } else {
        console.error('❌ Elemento loadingIA não encontrado');
        // Fallback: usa APBIA se disponível
        if (typeof APBIA !== 'undefined' && APBIA.showLoadingOverlay) {
            APBIA.showLoadingOverlay(message);
        }
    }
}

function hideLoading() {
    const loadingEl = document.getElementById('loadingIA');
    
    if (loadingEl) {
        loadingEl.style.display = 'none';
    } else {
        // Fallback
        if (typeof APBIA !== 'undefined' && APBIA.hideLoadingOverlay) {
            APBIA.hideLoadingOverlay();
        }
    }
}

function showNotification(message, type = 'info') {
    
    // Tenta usar APBIA global
    if (typeof APBIA !== 'undefined' && APBIA.showNotification) {
        APBIA.showNotification(message, type);
    } else {
        // Fallback: alert simples
        alert(message);
    }
}

// ===== INICIALIZAÇÃO COM VALIDAÇÃO =====
document.addEventListener('DOMContentLoaded', function() {
    
    // Valida dependências
    if (!checkDependencies()) {
        console.error('❌ Inicialização abortada - dependências faltando');
        return;
    }
    
    initProjetosHandlers();
});

function initProjetosHandlers() {
    
    // Contador de caracteres do resumo
    const resumoInput = document.getElementById('resumo');
    if (resumoInput) {
        resumoInput.addEventListener('input', function() {
            const count = this.value.length;
            const counterEl = document.getElementById('resumo-count');
            if (counterEl) {
                counterEl.textContent = `${count}/2000`;
            }
            
            if (count > 2000) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    } else {
        console.warn('⚠️ resumoInput não encontrado');
    }
    
    // Toggle continuação
    const ehContinuacaoCheckbox = document.getElementById('eh_continuacao');
    if (ehContinuacaoCheckbox) {
        ehContinuacaoCheckbox.addEventListener('change', function() {
            const fields = document.getElementById('continuacao-fields');
            if (fields) {
                fields.style.display = this.checked ? 'block' : 'none';
            }
        });
    }
    
    // Adicionar objetivo específico
    const addObjetivoBtn = document.getElementById('addObjetivo');
    if (addObjetivoBtn) {
        addObjetivoBtn.addEventListener('click', addObjetivoEspecifico);
    }
    
    // Adicionar etapa no cronograma
    const addEtapaBtn = document.getElementById('addEtapa');
    if (addEtapaBtn) {
        addEtapaBtn.addEventListener('click', addEtapaCronograma);
    }
    
    // ===== GERAR IDEIAS (CRÍTICO) =====
    const btnGerarIdeias = document.getElementById('btnGerarIdeias');
    if (btnGerarIdeias) {
        btnGerarIdeias.addEventListener('click', handleGerarIdeias);
    } else {
        console.error('❌ btnGerarIdeias NÃO ENCONTRADO');
    }
    
    // ===== AUTOCOMPLETAR (CRÍTICO) =====
    const btnsAutocompletar = document.querySelectorAll('.btn-ia-autocompletar');
    
    if (btnsAutocompletar.length > 0) {
        btnsAutocompletar.forEach((btn, index) => {
            btn.addEventListener('click', handleAutocompletar);
        });
    } else {
        console.warn('⚠️ Nenhum botão .btn-ia-autocompletar encontrado');
    }
    
    // Salvar projeto
    const formProjeto = document.getElementById('formProjeto');
    if (formProjeto && !document.getElementById('projeto_id')) {
        formProjeto.addEventListener('submit', handleSalvarProjeto);
    }
    
}

// ===== GERAR IDEIAS (FUNÇÃO PRINCIPAL) =====
async function handleGerarIdeias() {
    
    // Confirmação
    const confirmacao = confirm(
        '🎯 MODO BRAGANTEC AUTOMÁTICO\n\n' +
        'A IA vai analisar TODOS os projetos vencedores das edições anteriores da Bragantec.\n\n' +
        '⚠️ ATENÇÃO:\n' +
        '• Processo pode levar 20-40 segundos\n' +
        '• Consome ~100k-200k tokens\n\n' +
        'Deseja continuar?'
    );
    
    if (!confirmacao) {
        return;
    }
    
    showLoading('🧠 Analisando projetos vencedores...');
    
    try {
        
        const response = await fetch('/projetos/gerar-ideias', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            }
        });
        
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            mostrarIdeias(data.ideias, data.metadata);
        } else {
            console.error('❌ Erro no backend:', data.message);
            showNotification('Erro ao gerar ideias: ' + (data.message || 'Erro desconhecido'), 'error');
        }
        
    } catch (error) {
        console.error('❌ ERRO na requisição:', error);
        hideLoading();
        showNotification('Erro ao conectar com IA: ' + error.message, 'error');
    }
}

// ===== AUTOCOMPLETAR (FUNÇÃO PRINCIPAL) =====
async function handleAutocompletar() {
    
    const campo = this.dataset.campo;
    
    if (!campo) {
        console.error('❌ Campo não especificado');
        showNotification('Erro: campo não especificado', 'error');
        return;
    }
    
    const confirmacao = confirm(`A IA vai gerar conteúdo para: ${campo}. Continuar?`);
    
    if (!confirmacao) {
        return;
    }
    
    showLoading(`Gerando ${campo}...`);
    
    try {
        const projetoParcial = coletarDadosParciais();
        
        
        const response = await fetch('/projetos/autocompletar', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                campos: [campo],
                projeto: projetoParcial
            })
        });
        
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            aplicarConteudoGerado(campo, data.conteudo);
            showNotification('Conteúdo gerado! Revise e ajuste', 'success');
        } else {
            console.error('❌ Erro no backend:', data.message);
            showNotification('Erro: ' + (data.message || 'Erro desconhecido'), 'error');
        }
        
    } catch (error) {
        console.error('❌ ERRO na requisição:', error);
        hideLoading();
        showNotification('Erro ao conectar com IA: ' + error.message, 'error');
    }
}

// ===== MOSTRAR IDEIAS =====
function mostrarIdeias(ideias, metadata) {
    // Parse se vier como string
    let ideiasText = ideias;
    
    // Tenta parsear como JSON
    let ideiasObj = null;
    try {
        ideiasObj = typeof ideias === 'string' ? JSON.parse(ideias) : ideias;
    } catch (e) {
        // Silenciosamente continua com texto
    }
    
    let html = '';
    
    // Adiciona banner informativo sobre análise de vencedores
    if (metadata && metadata.analise_vencedores) {
        html += `
            <div class="alert alert-success mb-4">
                <h5><i class="fas fa-trophy"></i> <strong>Análise Completa Realizada</strong></h5>
                <p class="mb-2">
                    <i class="fas fa-check-circle"></i> <strong>Modo Bragantec ativado:</strong> 
                    ${metadata.contexto_usado}
                </p>
                <small class="text-muted">
                    <i class="fas fa-info-circle"></i> ${metadata.aviso_tokens}
                </small>
            </div>
        `;
    }
    
    if (ideiasObj && typeof ideiasObj === 'object') {
        // Renderiza ideias estruturadas
        html += '<div class="row g-3">';
        
        for (const [categoria, ideia] of Object.entries(ideiasObj)) {
            const titulo = ideia.titulo || ideia.nome || 'Sem título';
            const resumo = ideia.resumo || ideia.descricao || 'Sem descrição';
            const palavrasChave = ideia.palavras_chave || ideia.keywords || '';
            
            const inspiracao = ideia.inspiracao_vencedores || '';
            const diferenciais = ideia.diferenciais_competitivos || ideia.diferenciais || '';
            const viabilidade = ideia.viabilidade_tecnica || '';
            
            // Define cor do badge por categoria
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
                            <h5 class="card-title">${titulo}</h5>
                            
                            <div class="mb-3">
                                <strong class="text-muted">Resumo:</strong>
                                <p class="card-text">${resumo}</p>
                            </div>
                            
                            ${palavrasChave ? `
                                <div class="mb-2">
                                    <strong class="text-muted"><i class="fas fa-tags"></i> Palavras-chave:</strong>
                                    <p class="mb-0"><code>${palavrasChave}</code></p>
                                </div>
                            ` : ''}
                            
                            ${inspiracao ? `
                                <div class="alert alert-info py-2 mb-2">
                                    <strong><i class="fas fa-lightbulb"></i> Inspiração em Vencedores:</strong>
                                    <p class="mb-0 small">${inspiracao}</p>
                                </div>
                            ` : ''}
                            
                            ${diferenciais ? `
                                <div class="alert alert-success py-2 mb-2">
                                    <strong><i class="fas fa-star"></i> Diferenciais Competitivos:</strong>
                                    <p class="mb-0 small">${diferenciais}</p>
                                </div>
                            ` : ''}
                            
                            ${viabilidade ? `
                                <div class="alert alert-warning py-2 mb-2">
                                    <strong><i class="fas fa-tools"></i> Viabilidade Técnica:</strong>
                                    <p class="mb-0 small">${viabilidade}</p>
                                </div>
                            ` : ''}
                        </div>
                        <div class="card-footer bg-light">
                            <button class="btn btn-sm btn-success usar-ideia w-100" 
                                    data-ideia='${JSON.stringify(ideia).replace(/'/g, "&apos;")}'
                                    data-categoria="${categoria}">
                                <i class="fas fa-check-circle"></i> <strong>Usar Esta Ideia</strong>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
    } else {
        // Mostra como texto formatado
        html += `
            <div class="alert alert-info">
                <h5><i class="fas fa-lightbulb"></i> Ideias Geradas:</h5>
                <pre class="mb-0" style="white-space: pre-wrap; font-family: inherit;">${ideiasText}</pre>
            </div>
            <button class="btn btn-secondary" onclick="document.getElementById('modalIdeias').style.display='none'">Fechar</button>
        `;
    }
    
    document.getElementById('ideiasContent').innerHTML = html;
    
    // Adiciona handlers para botões "usar ideia"
    document.querySelectorAll('.usar-ideia').forEach(btn => {
        btn.addEventListener('click', function() {
            try {
                const ideia = JSON.parse(this.dataset.ideia);
                const categoria = this.dataset.categoria;
                preencherComIdeia(ideia, categoria);
                // Fecha o modal
                document.getElementById('modalIdeias').style.display = 'none';
            } catch (e) {
                if (window.APBIA && window.APBIA.showNotification) {
                    APBIA.showNotification('Erro ao aplicar ideia', 'error');
                } else {
                    alert('Erro ao aplicar ideia');
                }
            }
        });
    });
    
    // Mostra modal
    document.getElementById('modalIdeias').style.display = 'flex';
}

// ===== PREENCHER COM IDEIA =====
function preencherComIdeia(ideia, categoria) {
    
    const nomeInput = document.getElementById('nome');
    const categoriaSelect = document.getElementById('categoria');
    const resumoInput = document.getElementById('resumo');
    const palavrasChaveInput = document.getElementById('palavras_chave');
    
    if (nomeInput) nomeInput.value = ideia.titulo || '';
    if (categoriaSelect) categoriaSelect.value = categoria || '';
    if (resumoInput) {
        resumoInput.value = ideia.resumo || '';
        resumoInput.dispatchEvent(new Event('input'));
    }
    if (palavrasChaveInput) palavrasChaveInput.value = ideia.palavras_chave || '';
    
    // ✅ NOVO: Adiciona atributo data para indicar que foi gerado por IA
    const formProjeto = document.getElementById('formProjeto');
    if (formProjeto) {
        formProjeto.setAttribute('data-gerado-por-ia', 'true');
    }
    
    showNotification('✅ Ideia aplicada! Revise o conteúdo gerado.', 'success');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ===== COLETAR DADOS PARCIAIS =====
function coletarDadosParciais() {
    return {
        nome: document.getElementById('nome')?.value || '',
        categoria: document.getElementById('categoria')?.value || '',
        resumo: document.getElementById('resumo')?.value || '',
        palavras_chave: document.getElementById('palavras_chave')?.value || ''
    };
}

// ===== APLICAR CONTEÚDO GERADO =====
function aplicarConteudoGerado(campo, conteudo) {
    
    // Se conteúdo for string, usa diretamente
    if (typeof conteudo === 'string') {
        const elemento = document.getElementById(campo);
        if (elemento) {
            elemento.value = conteudo;
        }
        return;
    }
    
    // Se for objeto, mapeia campos
    if (campo === 'resumo' && conteudo.resumo) {
        const el = document.getElementById('resumo');
        if (el) {
            el.value = conteudo.resumo;
            el.dispatchEvent(new Event('input'));
        }
    } else if (campo === 'introducao' && conteudo.introducao) {
        const el = document.getElementById('introducao');
        if (el) el.value = conteudo.introducao;
    } else if (campo === 'objetivos' && conteudo.objetivo_geral) {
        const el = document.getElementById('objetivo_geral');
        if (el) el.value = conteudo.objetivo_geral;
    } else if (campo === 'metodologia' && conteudo.metodologia) {
        const el = document.getElementById('metodologia');
        if (el) el.value = conteudo.metodologia;
    } else if (campo === 'resultados_esperados' && conteudo.resultados_esperados) {
        const el = document.getElementById('resultados_esperados');
        if (el) el.value = conteudo.resultados_esperados;
    } else if (conteudo.texto) {
        // Fallback
        const el = document.getElementById(campo);
        if (el) el.value = conteudo.texto;
    }
}

// ===== ADICIONAR OBJETIVO ESPECÍFICO =====
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
    
    div.querySelector('.btn-remover-objetivo').addEventListener('click', function() {
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

// ===== ADICIONAR ETAPA CRONOGRAMA =====
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
    
    tr.querySelector('.btn-remover-etapa').addEventListener('click', function() {
        tr.remove();
    });
}

// ===== SALVAR PROJETO =====
async function handleSalvarProjeto(e) {
    e.preventDefault();
        
    const submitBtn = e.submitter;
    const status = submitBtn?.dataset?.status || 'rascunho';
    
    const dados = coletarDadosCompletos(status);
    
    showLoading('Salvando projeto...');
    
    try {
        const response = await fetch('/projetos/criar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            showNotification('Projeto salvo com sucesso!', 'success');
            setTimeout(() => {
                window.location.href = '/projetos';
            }, 1500);
        } else {
            showNotification('Erro: ' + (data.message || ''), 'error');
        }
        
    } catch (error) {
        hideLoading();
        showNotification('Erro ao salvar projeto: ' + error.message, 'error');
        console.error('Erro:', error);
    }
}

function coletarDadosCompletos(status) {
    // Coleta objetivos específicos
    const objetivosEspecificos = Array.from(
        document.querySelectorAll('.objetivo-especifico')
    ).map(input => input.value).filter(v => v.trim());
    
    // Coleta cronograma
    const cronograma = [];
    const cronogramaRows = document.querySelectorAll('#cronogramaBody tr');
    
    cronogramaRows.forEach(tr => {
        const etapaInput = tr.querySelector('input[type="text"]');
        if (!etapaInput) return;
        
        const etapa = etapaInput.value.trim();
        if (!etapa) return;
        
        const checkboxes = tr.querySelectorAll('input[type="checkbox"]');
        const meses = ['Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov'];
        const mesesMarcados = [];
        
        checkboxes.forEach((cb, idx) => {
            if (cb.checked && idx < meses.length) {
                mesesMarcados.push(meses[idx]);
            }
        });
        
        if (etapa) {
            cronograma.push({ etapa, meses: mesesMarcados });
        }
    });
    
    const ehContinuacao = document.getElementById('eh_continuacao')?.checked || false;
    
    // ✅ CORREÇÃO: Converte strings vazias para null em campos de data
    const projeto_anterior_inicio = document.getElementById('projeto_anterior_inicio')?.value || null;
    const projeto_anterior_termino = document.getElementById('projeto_anterior_termino')?.value || null;
    // ✅ NOVO: Verifica se foi gerado por IA
    const geradoPorIA = document.getElementById('formProjeto')?.getAttribute('data-gerado-por-ia') === 'true';
    return {
        nome: document.getElementById('nome')?.value || '',
        categoria: document.getElementById('categoria')?.value || '',
        ano_edicao: parseInt(document.getElementById('ano_edicao')?.value) || new Date().getFullYear(),
        resumo: document.getElementById('resumo')?.value || '',
        palavras_chave: document.getElementById('palavras_chave')?.value || '',
        introducao: document.getElementById('introducao')?.value || '',
        objetivo_geral: document.getElementById('objetivo_geral')?.value || '',
        objetivos_especificos: objetivosEspecificos,
        metodologia: document.getElementById('metodologia')?.value || '',
        cronograma: cronograma,
        resultados_esperados: document.getElementById('resultados_esperados')?.value || '',
        referencias_bibliograficas: document.getElementById('referencias_bibliograficas')?.value || '',
        eh_continuacao: ehContinuacao,
        projeto_anterior_titulo: document.getElementById('projeto_anterior_titulo')?.value || '',
        projeto_anterior_resumo: document.getElementById('projeto_anterior_resumo')?.value || '',
        projeto_anterior_inicio: projeto_anterior_inicio,
        projeto_anterior_termino: projeto_anterior_termino,
        status: status,
        gerado_por_ia: geradoPorIA 
    };
}