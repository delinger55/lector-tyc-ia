# Implementation Plan: Lector de Términos y Condiciones con IA

## Overview

Plan de implementación incremental basado en el diseño técnico (`design.md`). Cada tarea es pequeña, independiente y verificable con sus propios tests. Se incluyen checkpoints de verificación entre fases.

**Convenciones:**
- Cada tarea indica qué Requirements y/o Properties valida
- Se usa `LLM_PROVIDER=mock` durante todo el desarrollo

## Tasks

- [ ] 1. Scaffolding del proyecto y configuración
  - [ ] 1.1 Crear estructura de directorios y archivos `__init__.py`
    - Directorios: `app/`, `app/core/`, `app/extractors/`, `app/llm/`, `app/services/`, `app/schemas/`, `app/routers/`, `app/templates/`, `app/static/css/`, `app/static/js/`, `tests/`, `test_docs/`
    - Crear `requirements.txt` con: fastapi, uvicorn[standard], pypdf, python-docx, pydantic, pydantic-settings, python-multipart, jinja2, pytest, pytest-asyncio, httpx, hypothesis
    - Crear `.env.example` con todas las variables documentadas en design.md
    - _Requirements: 9.1, 9.4_
  - [ ] 1.2 Implementar `app/core/config.py` con AppSettings
    - Clase `AppSettings(BaseSettings)` con campos: llm_provider, llm_api_key, llm_timeout_seconds, max_file_size_mb, max_words, chunking_threshold, app_name, debug
    - `model_validator` que rechaza si `LLM_PROVIDER != "mock"` y `LLM_API_KEY` vacía
    - Propiedad `max_file_size_bytes`, función `get_settings()` con `@lru_cache`
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [ ] 1.3 Implementar `app/core/exceptions.py` con excepciones personalizadas
    - `AppBaseException`, `InvalidFormatException`, `FileTooLargeException`, `ScannedDocumentException`, `ExtractionError`, `TextTooLongException`, `LLMTimeoutError`, `LLMCommunicationError`, `AnalysisValidationError`, `NotTermsException`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  - [ ] 1.4 Escribir tests para configuración y excepciones (`tests/test_config.py`)
    - Test: AppSettings carga defaults, validación rechaza sin API key cuando provider != mock, cada excepción tiene error_code correcto
    - _Requirements: 9.2, 9.3_
- [ ] 2. Esquemas Pydantic (modelos de datos)
  - [ ] 2.1 Implementar `app/schemas/analysis.py`
    - Enum `Severity`: HIGH, MEDIUM, LOW. Modelos: `RiskClause`, `AnalysisResult` (con validator 5 puntos), `ErrorResponse`
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [ ] 2.2 Escribir tests para esquemas (`tests/test_schemas.py`)
    - Property 7: listas != 5 elementos lanzan ValidationError
    - Property 8: serialización round-trip preserva datos
    - Unit tests: instancia válida, RiskClause con quote=None, Severity tiene 3 valores
    - _Properties: 7, 8 | Requirements: 11.1, 11.2, 11.3, 11.4_
- [ ] 3. **CHECKPOINT**: Verificar base (config + schemas)
- [ ] 4. Extractores de texto
  - [ ] 4.1 Implementar `app/extractors/base.py` con BaseExtractor(ABC)
    - _Requirements: 2.1, 2.2_
  - [ ] 4.2 Implementar `app/extractors/pdf_extractor.py`
    - PdfExtractor con pypdf, ScannedDocumentException si < 100 chars, ExtractionError si corrupto
    - _Requirements: 2.1, 2.3, 2.4_
  - [ ] 4.3 Implementar `app/extractors/docx_extractor.py`
    - DocxExtractor con python-docx, ExtractionError si corrupto
    - _Requirements: 2.2, 2.4_
  - [ ] 4.4 Implementar `app/extractors/__init__.py` con factory get_extractor()
    - _Requirements: 1.1, 1.2_
  - [ ] 4.5 Escribir tests para extractores (`tests/test_extractors.py`)
    - Property 3: detección documento escaneado por umbral 100 chars
    - Unit tests: extracción PDF/DOCX válidos, archivos corruptos, factory por extensión
    - _Property: 3 | Requirements: 2.1, 2.2, 2.3, 2.4, 1.1, 1.2_
- [ ] 5. Interfaz LLM y proveedor mock
  - [ ] 5.1 Implementar `app/llm/base.py` con AnalizadorLLM(ABC)
    - _Requirements: 8.1_
  - [ ] 5.2 Implementar `app/llm/mock_provider.py` con MockLLMAnalyzer
    - Retorna AnalysisResult válido con 5 puntos y cláusulas de ejemplo
    - _Requirements: 8.2_
  - [ ] 5.3 Implementar `app/llm/__init__.py` con factory get_llm_analyzer()
    - _Requirements: 8.2, 8.3, 8.4_
  - [ ] 5.4 Escribir tests para LLM (`tests/test_llm.py`)
    - Mock retorna resultado válido, factory selecciona correcto, error para proveedor no soportado
    - _Requirements: 8.1, 8.2, 8.3_
- [ ] 6. **CHECKPOINT**: Verificar extractores y LLM
- [ ] 7. Servicio de chunking
  - [ ] 7.1 Implementar `app/services/chunking.py`
    - chunk_text() divide por párrafos, agrupa sin exceder threshold, preserva contenido completo
    - _Requirements: 3.1_
  - [ ] 7.2 Escribir tests para chunking (`tests/test_chunking.py`)
    - Property 5: "\n\n".join(chunks) == text original
    - Unit tests: texto sin párrafos, texto en umbral, párrafo individual grande
    - _Property: 5 | Requirements: 3.1_
- [ ] 8. Servicio de consolidación (fase Reduce)
  - [ ] 8.1 Implementar `app/services/consolidator.py`
    - consolidate_results() deduplica por similitud de título, selecciona 5 summary_points, mayoría para is_valid_terms
    - _Requirements: 3.3_
  - [ ] 8.2 Escribir tests para consolidador (`tests/test_consolidator.py`)
    - Property 6: resultado tiene <= total cláusulas originales
    - Unit tests: duplicados eliminados, diferentes conservadas, 5 summary_points, mayoría is_valid_terms
    - _Property: 6 | Requirements: 3.3_
- [ ] 9. Pipeline de análisis (orquestador)
  - [ ] 9.1 Implementar `app/services/analysis_pipeline.py`
    - AnalysisPipeline: análisis directo vs Map-Reduce, retry si != 5 puntos, timeout con asyncio.wait_for
    - _Requirements: 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ] 9.2 Escribir tests para pipeline (`tests/test_pipeline.py`)
    - Tests: texto corto 1 llamada, texto largo múltiples, retry exitoso, doble fallo, timeout
    - _Requirements: 3.2, 3.4, 4.1, 4.3, 4.4, 4.5_
- [ ] 10. **CHECKPOINT**: Verificar servicios de análisis
- [ ] 11. Aplicación FastAPI y router
  - [ ] 11.1 Implementar `app/main.py`
    - FastAPI app, exception handler global, mount static, Jinja2 templates, include router
    - _Requirements: 10.1, 12.1-12.6_
  - [ ] 11.2 Implementar `app/routers/analyze.py`
    - GET / renderiza template, POST /api/v1/analyze con validación completa y cleanup en finally
    - _Requirements: 1.1-1.4, 2.5, 7.1, 10.1, 10.2, 10.3_
  - [ ] 11.3 Escribir tests para router (`tests/test_api.py`)
    - Properties 1, 2, 9: validación extensión, tamaño, endpoint rechaza inválidos
    - Unit tests: GET / 200 HTML, POST válido 200 JSON, POST inválidos 400
    - _Properties: 1, 2, 9 | Requirements: 1.1-1.4, 2.5, 7.1, 10.1, 10.2, 10.3_
- [ ] 12. **CHECKPOINT**: Verificar backend completo
- [ ] 13. Frontend (template HTML + CSS + JavaScript)
  - [ ] 13.1 Crear `app/templates/index.html`
    - 3 estados (upload, processing, results), disclaimers, formulario, sección resultados con colores
    - _Requirements: 5.1-5.5, 6.1-6.4, 7.2_
  - [ ] 13.2 Crear `app/static/css/styles.css`
    - Colores severidad (rojo/amarillo/verde), disclaimer con contraste, spinner, layout responsivo
    - _Requirements: 5.4, 5.5, 6.3_
  - [ ] 13.3 Crear `app/static/js/app.js`
    - Gestión estados, fetch API, renderizado resultados, manejo errores, transiciones sin recarga
    - _Requirements: 5.2, 5.3, 5.6_
  - [ ] 13.4 Escribir tests para frontend (`tests/test_frontend.py`)
    - Tests: HTML contiene disclaimer, input file, 3 secciones estado, botón analizar, aviso API
    - _Requirements: 5.1, 6.1, 7.2_
- [ ] 14. **CHECKPOINT**: Verificar aplicación completa
- [ ] 15. Tests de integración end-to-end
  - [ ] 15.1 Crear `tests/conftest.py` con fixtures compartidas
    - AsyncClient, sample PDF/DOCX bytes, hypothesis config, settings override
    - _Requirements: Todas_
  - [ ] 15.2 Escribir tests de integración (`tests/test_integration.py`)
    - E2E: PDF válido 200, DOCX válido 200, .txt 400, archivo grande 400, PDF escaneado 400, corrupto 400
    - _Requirements: 1.1-1.4, 2.1-2.5, 7.1, 10.2, 10.3, 12.1-12.6_
- [ ] 16. **CHECKPOINT FINAL**: Verificar integración completa

## Notes

- Se usa `LLM_PROVIDER=mock` durante todo el desarrollo
- Archivos de prueba se generan programáticamente en fixtures
- Property tests usan hypothesis con mínimo 200 ejemplos
- Cada checkpoint verifica que todo lo anterior funciona antes de avanzar

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"], "desc": "Scaffolding" },
    { "id": 1, "tasks": ["1.2", "1.3"], "desc": "Config y excepciones" },
    { "id": 2, "tasks": ["1.4", "2.1"], "desc": "Tests config + Schemas" },
    { "id": 3, "tasks": ["2.2"], "desc": "Tests schemas (Properties 7, 8)" },
    { "id": 4, "tasks": ["4.1", "5.1"], "desc": "Clases abstractas" },
    { "id": 5, "tasks": ["4.2", "4.3", "5.2"], "desc": "Implementaciones concretas" },
    { "id": 6, "tasks": ["4.4", "5.3"], "desc": "Factories" },
    { "id": 7, "tasks": ["4.5", "5.4"], "desc": "Tests extractores y LLM" },
    { "id": 8, "tasks": ["7.1", "8.1"], "desc": "Chunking + Consolidator" },
    { "id": 9, "tasks": ["7.2", "8.2"], "desc": "Tests chunking y consolidación" },
    { "id": 10, "tasks": ["9.1"], "desc": "Pipeline de análisis" },
    { "id": 11, "tasks": ["9.2"], "desc": "Tests pipeline" },
    { "id": 12, "tasks": ["11.1", "11.2"], "desc": "FastAPI app + router" },
    { "id": 13, "tasks": ["11.3"], "desc": "Tests router" },
    { "id": 14, "tasks": ["13.1", "13.2", "13.3"], "desc": "Frontend" },
    { "id": 15, "tasks": ["13.4", "15.1"], "desc": "Tests frontend + fixtures" },
    { "id": 16, "tasks": ["15.2"], "desc": "Tests integración E2E" }
  ]
}
```