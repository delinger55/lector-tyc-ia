/**
 * Lector de Términos y Condiciones con IA
 * Gestión de estados, fetch API, drag-and-drop, tabs y renderizado de resultados.
 */

(function () {
    'use strict';

    // --- Estado de la aplicación ---
    const State = {
        UPLOAD: 'upload',
        PROCESSING: 'processing',
        RESULTS: 'results',
    };

    const InputMode = {
        FILE: 'file',
        URL: 'url',
    };

    var currentInputMode = InputMode.FILE;

    // --- Referencias al DOM ---
    const elements = {
        stateUpload: document.getElementById('state-upload'),
        stateProcessing: document.getElementById('state-processing'),
        stateResults: document.getElementById('state-results'),
        uploadForm: document.getElementById('upload-form'),
        fileInput: document.getElementById('file-input'),
        dropZone: document.getElementById('drop-zone'),
        fileNameDisplay: document.getElementById('file-name-display'),
        btnAnalyze: document.getElementById('btn-analyze'),
        btnNewAnalysis: document.getElementById('btn-new-analysis'),
        btnDismissError: document.getElementById('btn-dismiss-error'),
        errorBanner: document.getElementById('error-banner'),
        errorMessage: document.getElementById('error-message'),
        summaryList: document.getElementById('summary-list'),
        riskClausesContainer: document.getElementById('risk-clauses-container'),
        noRisksMessage: document.getElementById('no-risks-message'),
        // Tabs
        tabFile: document.getElementById('tab-file'),
        tabUrl: document.getElementById('tab-url'),
        panelFile: document.getElementById('panel-file'),
        panelUrl: document.getElementById('panel-url'),
        urlInput: document.getElementById('url-input'),
    };

    // --- Gestión de estados ---

    function setState(newState) {
        elements.stateUpload.classList.add('hidden');
        elements.stateProcessing.classList.add('hidden');
        elements.stateResults.classList.add('hidden');

        switch (newState) {
            case State.UPLOAD:
                elements.stateUpload.classList.remove('hidden');
                break;
            case State.PROCESSING:
                elements.stateProcessing.classList.remove('hidden');
                break;
            case State.RESULTS:
                elements.stateResults.classList.remove('hidden');
                break;
        }
    }

    // --- Tabs ---

    function switchTab(mode) {
        currentInputMode = mode;
        hideError();
        elements.btnAnalyze.disabled = true;

        if (mode === InputMode.FILE) {
            elements.tabFile.classList.add('input-tab--active');
            elements.tabUrl.classList.remove('input-tab--active');
            elements.panelFile.classList.remove('hidden');
            elements.panelUrl.classList.add('hidden');
            // Re-check if file is selected
            if (elements.fileInput.files && elements.fileInput.files[0]) {
                elements.btnAnalyze.disabled = false;
            }
        } else {
            elements.tabUrl.classList.add('input-tab--active');
            elements.tabFile.classList.remove('input-tab--active');
            elements.panelUrl.classList.remove('hidden');
            elements.panelFile.classList.add('hidden');
            // Re-check if URL has value
            if (elements.urlInput.value.trim()) {
                elements.btnAnalyze.disabled = false;
            }
        }
    }

    // --- Manejo de errores ---

    function showError(message, errorCode) {
        elements.errorBanner.classList.remove('hidden');

        if (errorCode === 'URL_EXTRACTION_FAILED') {
            elements.errorMessage.innerHTML =
                '<strong>No se pudo acceder a la página web.</strong><br>' +
                '<span class="error-detail">Es posible que el sitio web tenga restricciones de seguridad ' +
                '(como redes sociales o portales protegidos) que bloquean las solicitudes automáticas. ' +
                'Intenta con un enlace de términos o políticas público y accesible.</span>';
        } else {
            elements.errorMessage.textContent = message;
        }
    }

    function hideError() {
        elements.errorBanner.classList.add('hidden');
        elements.errorMessage.innerHTML = '';
    }

    // --- Drag and drop ---

    function setupDragAndDrop() {
        const dropZone = elements.dropZone;

        ['dragenter', 'dragover'].forEach(function (event) {
            dropZone.addEventListener(event, function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(function (event) {
            dropZone.addEventListener(event, function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('drag-over');
            });
        });

        dropZone.addEventListener('drop', function (e) {
            var files = e.dataTransfer.files;
            if (files.length > 0) {
                elements.fileInput.files = files;
                handleFileSelected();
            }
        });
    }

    // --- Selección de archivo ---

    function handleFileSelected() {
        var file = elements.fileInput.files[0];
        if (file) {
            elements.fileNameDisplay.textContent = '📎 ' + file.name;
            elements.btnAnalyze.disabled = false;
            hideError();
        } else {
            elements.fileNameDisplay.textContent = '';
            elements.btnAnalyze.disabled = true;
        }
    }

    // --- URL input change ---

    function handleUrlInput() {
        if (elements.urlInput.value.trim()) {
            elements.btnAnalyze.disabled = false;
        } else {
            elements.btnAnalyze.disabled = true;
        }
    }

    // --- Envío del formulario ---

    async function handleSubmit(event) {
        event.preventDefault();
        hideError();

        var formData = new FormData();

        if (currentInputMode === InputMode.FILE) {
            var file = elements.fileInput.files[0];
            if (!file) {
                showError('Por favor selecciona un archivo.');
                return;
            }

            // Validación del lado del cliente
            var ext = file.name.split('.').pop().toLowerCase();
            if (ext !== 'pdf' && ext !== 'docx' && ext !== 'txt') {
                showError('Solo se aceptan archivos PDF (.pdf), Word (.docx) y texto (.txt).');
                return;
            }

            if (file.size > 10 * 1024 * 1024) {
                showError('El archivo excede el tamaño máximo de 10 MB.');
                return;
            }

            formData.append('file', file);
        } else {
            var url = elements.urlInput.value.trim();
            if (!url) {
                showError('Por favor ingresa una URL.');
                return;
            }

            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                showError('La URL debe comenzar con http:// o https://');
                return;
            }

            formData.append('url', url);
        }

        // Cambiar a estado de procesamiento
        setState(State.PROCESSING);

        try {
            var response = await fetch('/api/v1/analyze', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                var errorData = await response.json();
                showError(
                    errorData.detail || 'Ocurrió un error inesperado.',
                    errorData.error_code || null
                );
                setState(State.UPLOAD);
                return;
            }

            var result = await response.json();
            renderResults(result);
            setState(State.RESULTS);
        } catch (error) {
            showError('Error de conexión. Verifique su red e intente nuevamente.');
            setState(State.UPLOAD);
        }
    }

    // --- Renderizado de resultados ---

    function renderResults(data) {
        elements.summaryList.innerHTML = '';
        data.summary_points.forEach(function (point) {
            var li = document.createElement('li');
            li.textContent = point;
            elements.summaryList.appendChild(li);
        });

        elements.riskClausesContainer.innerHTML = '';

        if (data.risk_clauses.length === 0) {
            elements.noRisksMessage.classList.remove('hidden');
        } else {
            elements.noRisksMessage.classList.add('hidden');
            data.risk_clauses.forEach(function (clause) {
                var card = createRiskClauseCard(clause);
                elements.riskClausesContainer.appendChild(card);
            });
        }
    }

    function createRiskClauseCard(clause) {
        var severityClass = 'risk-clause--' + clause.severity.toLowerCase();
        var severityLabel = getSeverityLabel(clause.severity);

        var card = document.createElement('div');
        card.className = 'risk-clause ' + severityClass;

        var header = document.createElement('div');
        header.className = 'risk-clause__header';

        var badge = document.createElement('span');
        badge.className = 'risk-clause__badge';
        badge.textContent = severityLabel;

        var title = document.createElement('span');
        title.className = 'risk-clause__title';
        title.textContent = clause.title;

        header.appendChild(badge);
        header.appendChild(title);
        card.appendChild(header);

        var explanation = document.createElement('p');
        explanation.className = 'risk-clause__explanation';
        explanation.textContent = clause.explanation;
        card.appendChild(explanation);

        if (clause.quote) {
            var quote = document.createElement('p');
            quote.className = 'risk-clause__quote';
            quote.textContent = '\"' + clause.quote + '\"';
            card.appendChild(quote);
        }

        return card;
    }

    function getSeverityLabel(severity) {
        switch (severity) {
            case 'HIGH': return 'Alto';
            case 'MEDIUM': return 'Medio';
            case 'LOW': return 'Bajo';
            default: return severity;
        }
    }

    // --- Reiniciar análisis ---

    function handleNewAnalysis() {
        elements.uploadForm.reset();
        elements.fileNameDisplay.textContent = '';
        elements.btnAnalyze.disabled = true;
        elements.summaryList.innerHTML = '';
        elements.riskClausesContainer.innerHTML = '';
        hideError();
        switchTab(InputMode.FILE);
        setState(State.UPLOAD);
    }

    // --- Theme toggle (Dark Mode) ---

    function getPreferredTheme() {
        var stored = localStorage.getItem('theme');
        if (stored) {
            return stored;
        }
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }

    function toggleTheme() {
        var current = document.documentElement.getAttribute('data-theme');
        var newTheme = current === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    }

    function setupThemeToggle() {
        applyTheme(getPreferredTheme());

        var btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.addEventListener('click', toggleTheme);
        }

        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
                if (!localStorage.getItem('theme')) {
                    applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    // --- Inicialización ---

    function init() {
        setupThemeToggle();
        setupDragAndDrop();

        elements.fileInput.addEventListener('change', handleFileSelected);
        elements.uploadForm.addEventListener('submit', handleSubmit);
        elements.btnNewAnalysis.addEventListener('click', handleNewAnalysis);
        elements.btnDismissError.addEventListener('click', hideError);

        // Tabs
        elements.tabFile.addEventListener('click', function () { switchTab(InputMode.FILE); });
        elements.tabUrl.addEventListener('click', function () { switchTab(InputMode.URL); });
        elements.urlInput.addEventListener('input', handleUrlInput);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
