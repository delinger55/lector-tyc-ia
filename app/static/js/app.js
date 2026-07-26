/**
 * Lector de Términos y Condiciones con IA
 * Gestión de estados, fetch API, drag-and-drop y renderizado de resultados.
 */

(function () {
    'use strict';

    // --- Estado de la aplicación ---
    const State = {
        UPLOAD: 'upload',
        PROCESSING: 'processing',
        RESULTS: 'results',
    };

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
    };

    // --- Gestión de estados ---

    function setState(newState) {
        // Ocultar todas las secciones
        elements.stateUpload.classList.add('hidden');
        elements.stateProcessing.classList.add('hidden');
        elements.stateResults.classList.add('hidden');

        // Mostrar la sección correspondiente
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

    // --- Manejo de errores ---

    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.errorBanner.classList.remove('hidden');
    }

    function hideError() {
        elements.errorBanner.classList.add('hidden');
        elements.errorMessage.textContent = '';
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

    // --- Envío del formulario ---

    async function handleSubmit(event) {
        event.preventDefault();
        hideError();

        var file = elements.fileInput.files[0];
        if (!file) {
            showError('Por favor selecciona un archivo.');
            return;
        }

        // Validación del lado del cliente (informativa)
        var ext = file.name.split('.').pop().toLowerCase();
        if (ext !== 'pdf' && ext !== 'docx') {
            showError('Solo se aceptan archivos PDF (.pdf) y Word (.docx).');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            showError('El archivo excede el tamaño máximo de 10 MB.');
            return;
        }

        // Cambiar a estado de procesamiento
        setState(State.PROCESSING);

        // Enviar archivo al backend
        var formData = new FormData();
        formData.append('file', file);

        try {
            var response = await fetch('/api/v1/analyze', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                var errorData = await response.json();
                showError(errorData.detail || 'Ocurrió un error inesperado.');
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
        // Renderizar summary_points
        elements.summaryList.innerHTML = '';
        data.summary_points.forEach(function (point) {
            var li = document.createElement('li');
            li.textContent = point;
            elements.summaryList.appendChild(li);
        });

        // Renderizar risk_clauses
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
        // Limpiar formulario y resultados
        elements.uploadForm.reset();
        elements.fileNameDisplay.textContent = '';
        elements.btnAnalyze.disabled = true;
        elements.summaryList.innerHTML = '';
        elements.riskClausesContainer.innerHTML = '';
        hideError();
        setState(State.UPLOAD);
    }

    // --- Theme toggle (Dark Mode) ---

    function getPreferredTheme() {
        var stored = localStorage.getItem('theme');
        if (stored) {
            return stored;
        }
        // Respetar preferencia del sistema
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
        // Aplicar tema al cargar
        applyTheme(getPreferredTheme());

        // Escuchar click en el botón
        var btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.addEventListener('click', toggleTheme);
        }

        // Escuchar cambios en preferencia del sistema
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
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
