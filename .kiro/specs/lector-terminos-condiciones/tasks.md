# Implementation Plan: Lector de Términos y Condiciones con IA

## Overview

Plan de implementación incremental basado en el diseño técnico (`design.md`). Cada tarea es pequeña, independiente y verificable con sus propios tests. Se incluyen checkpoints de verificación entre fases.

**Estado actual:** 173 tests pasando al 100%, 0 warnings.

**Convenciones:**
- Cada tarea indica qué Requirements y/o Properties valida
- Se usa `LLM_PROVIDER=mock` durante todo el desarrollo

## Tasks

- [x] 1. Scaffolding del proyecto y configuración
  - [x] 1.1 Crear estructura de directorios y archivos `__init__.py`
    - _Requirements: 9.1, 9.4_
  - [x] 1.2 Implementar `app/core/config.py` con AppSettings
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [x] 1.3 Implementar `app/core/exceptions.py` con excepciones personalizadas
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  - [x] 1.4 Escribir tests para configuración y excepciones (`tests/test_config.py`) — 23 tests
    - _Requirements: 9.2, 9.3_
- [x] 2. Esquemas Pydantic (modelos de datos)
  - [x] 2.1 Implementar `app/schemas/analysis.py`
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  - [x] 2.2 Escribir tests para esquemas (`tests/test_schemas.py`) — 17 tests
    - _Properties: 7, 8 | Requirements: 11.1, 11.2, 11.3, 11.4_
- [x] 3. **CHECKPOINT**: Verificar base (config + schemas) ✓ 40 tests
- [x] 4. Extractores de texto
  - [x] 4.1 Implementar `app/extractors/base.py` con BaseExtractor(ABC)
    - _Requirements: 2.1, 2.2_
  - [x] 4.2 Implementar `app/extractors/pdf_extractor.py`
    - _Requirements: 2.1, 2.3, 2.4_
  - [x] 4.3 Implementar `app/extractors/docx_extractor.py`
    - _Requirements: 2.2, 2.4_
  - [x] 4.4 Implementar `app/extractors/__init__.py` con factory get_extractor()
    - _Requirements: 1.1, 1.2_
  - [x] 4.5 Escribir tests para extractores (`tests/test_extractors.py`) — 22 tests
    - _Property: 3 | Requirements: 2.1, 2.2, 2.3, 2.4, 1.1, 1.2_
- [x] 5. Interfaz LLM y proveedor mock
  - [x] 5.1 Implementar `app/llm/base.py` con AnalizadorLLM(ABC)
    - _Requirements: 8.1_
  - [x] 5.2 Implementar `app/llm/mock_provider.py` con MockLLMAnalyzer
    - _Requirements: 8.2_
  - [x] 5.3 Implementar `app/llm/__init__.py` con factory get_llm_analyzer()
    - _Requirements: 8.2, 8.3, 8.4_
  - [x] 5.4 Escribir tests para LLM (`tests/test_llm.py`) — 11 tests
    - _Requirements: 8.1, 8.2, 8.3_
- [x] 6. **CHECKPOINT**: Verificar extractores y LLM ✓ 68 tests
- [x] 7. Servicio de chunking
  - [x] 7.1 Implementar `app/services/chunking.py`
    - _Requirements: 3.1_
  - [x] 7.2 Escribir tests para chunking (`tests/test_chunking.py`) — 12 tests
    - _Property: 5 | Requirements: 3.1_
- [x] 8. Servicio de consolidación (fase Reduce)
  - [x] 8.1 Implementar `app/services/consolidator.py`
    - _Requirements: 3.3_
  - [x] 8.2 Escribir tests para consolidador (`tests/test_consolidator.py`) — 18 tests
    - _Property: 6 | Requirements: 3.3_
- [x] 9. Pipeline de análisis (orquestador)
  - [x] 9.1 Implementar `app/services/analysis_pipeline.py`
    - _Requirements: 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 9.2 Escribir tests para pipeline (`tests/test_pipeline.py`) — 9 tests
    - _Requirements: 3.2, 3.4, 4.1, 4.3, 4.4, 4.5_
- [x] 10. **CHECKPOINT**: Verificar servicios de análisis ✓ 107 tests
- [x] 11. Aplicación FastAPI y router
  - [x] 11.1 Implementar `app/main.py`
    - _Requirements: 10.1, 12.1-12.6_
  - [x] 11.2 Implementar `app/routers/analyze.py`
    - _Requirements: 1.1-1.4, 2.5, 7.1, 10.1, 10.2, 10.3_
  - [x] 11.3 Escribir tests para router (`tests/test_api.py`) — 18 tests
    - _Properties: 1, 2, 9 | Requirements: 1.1-1.4, 2.5, 7.1, 10.1, 10.2, 10.3_
- [x] 12. **CHECKPOINT**: Verificar backend completo ✓ 122 tests
- [x] 13. Frontend (template HTML + CSS + JavaScript)
  - [x] 13.1 Crear `app/templates/index.html`
    - _Requirements: 5.1-5.5, 6.1-6.4, 7.2_
  - [x] 13.2 Crear `app/static/css/styles.css`
    - _Requirements: 5.4, 5.5, 6.3_
  - [x] 13.3 Crear `app/static/js/app.js`
    - _Requirements: 5.2, 5.3, 5.6_
  - [x] 13.4 Escribir tests para frontend (`tests/test_frontend.py`) — 17 tests
    - _Requirements: 5.1, 6.1, 7.2, 13.1-13.8_
- [x] 14. **CHECKPOINT**: Verificar aplicación completa ✓ 135 tests
- [x] 15. Tests de integración end-to-end
  - [x] 15.1 Crear `tests/conftest.py` con fixtures compartidas
    - _Requirements: Todas_
  - [x] 15.2 Escribir tests de integración (`tests/test_integration.py`) — 24 tests
    - _Requirements: 1.1-1.4, 2.1-2.5, 7.1, 10.2, 10.3, 12.1-12.6, 14.1-14.5_
- [x] 16. **CHECKPOINT FINAL**: Verificar integración completa ✓ 155 tests
- [x] 17. Soporte para .txt y análisis por URL
  - [x] 17.1 Implementar `app/extractors/txt_extractor.py` con TxtExtractor (UTF-8 + Latin-1)
    - _Requirements: 14.1_
  - [x] 17.2 Implementar `app/extractors/web_extractor.py` con WebUrlExtractor (httpx + BeautifulSoup)
    - _Requirements: 14.2_
  - [x] 17.3 Actualizar factory `app/extractors/__init__.py` con .txt y get_web_extractor()
    - _Requirements: 14.1, 14.2_
  - [x] 17.4 Actualizar `app/routers/analyze.py` para aceptar .txt y parámetro url opcional (File|Form dual)
    - _Requirements: 14.1, 14.4, 14.5_
  - [x] 17.5 Actualizar frontend con tabs (Subir archivo / Ingresar URL)
    - _Requirements: 14.3_
  - [x] 17.6 Actualizar tests existentes y agregar nuevos tests para .txt y URL
    - _Requirements: 14.1-14.5_
  - [x] 17.7 Fix: Manejo robusto de URLs con `UrlExtractionError` y mensaje dinámico en frontend
    - Creada excepción `UrlExtractionError` (error_code `URL_EXTRACTION_FAILED`) con mensaje descriptivo sobre restricciones de seguridad
    - Router refactorizado con checks explícitos `has_url`/`has_file` y prioridad URL > File
    - Frontend JS detecta `URL_EXTRACTION_FAILED` y renderiza error enriquecido con HTML (título bold + detalle)
    - CSS `.error-detail` para jerarquía visual dentro del banner de error
    - Tests E2E: URL form-data, protocolo inválido, vacía, prioridad sobre file, mensaje amigable
    - _Requirements: 14.2, 14.5_
- [x] 18. Rediseño UI/UX Moderno (estilo SaaS)
  - [x] 18.1 Actualizar `app/templates/index.html` con diseño moderno
    - Tipografía Inter (Google Fonts), header con badge de versión, toggle dark mode con SVG, zona drag-and-drop con íconos SVG vectoriales y micro-animaciones, badges de formato (.PDF, .DOCX, .TXT), pasos de procesamiento animados, íconos SVG en section titles y badges de severidad
    - _Requirements: 13.1, 13.2, 13.3, 13.6, 13.7, 13.8_
  - [x] 18.2 Refactorizar `app/static/css/styles.css` con sistema de diseño moderno
    - Variables CSS con paleta sofisticada (light y dark), glassmorphism (backdrop-filter: blur), transiciones suaves (all 0.2s ease), hover lift (translateY -1px + shadow), animaciones fadeIn, grid responsivo con colapso en móvil, estilos para tabs y URL input
    - _Requirements: 13.4, 13.5_
  - [x] 18.3 Actualizar `app/static/js/app.js` con micro-interacciones y manejo dinámico de errores
    - Theme toggle con localStorage + prefers-color-scheme, tabs para file/URL switching, validación por modo de input, renderizado de errores enriquecido por error_code
    - _Requirements: 13.2, 13.3_
  - [x] 18.4 Verificar tests DOM pasan con nueva estructura — 173 tests al 100%
    - _Requirements: 13.1-13.8_

## Notes

- Se usa `LLM_PROVIDER=mock` durante todo el desarrollo
- Archivos de prueba se generan programáticamente en fixtures
- Property tests usan hypothesis con mínimo 200 ejemplos por propiedad
- Cada checkpoint verifica que todo lo anterior funciona antes de avanzar
- Tareas 17 y 18 fueron agregadas post-MVP como mejoras incrementales
- Suite actual: **173 tests pasando al 100%, 0 warnings** (pytest con `-W error::DeprecationWarning`)

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
    { "id": 16, "tasks": ["15.2"], "desc": "Tests integración E2E" },
    { "id": 17, "tasks": ["17.1", "17.2", "17.3", "17.4", "17.5", "17.6", "17.7"], "desc": "Soporte .txt + URL + fix robustez" },
    { "id": 18, "tasks": ["18.1", "18.2", "18.3", "18.4"], "desc": "Rediseño UI/UX Moderno" }
  ]
}
```
