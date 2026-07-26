# Requirements Document

## Introduction

Aplicación web "Lector de Términos y Condiciones con IA" que permite a los usuarios subir documentos de términos y condiciones en formato PDF o Word (.docx), extraer su texto, enviarlo a un modelo de lenguaje para análisis, y presentar un resumen estructurado con puntos clave y cláusulas de riesgo. El sistema es stateless, no persiste documentos ni historial de usuario, y opera con un backend en Python (FastAPI) con templates Jinja2 para el frontend.

## Glossary

- **Sistema**: La aplicación web "Lector de Términos y Condiciones con IA"
- **Documento_TyC**: Archivo PDF o Word (.docx) que contiene términos y condiciones subidos por el usuario
- **Extractor**: Componente responsable de obtener texto plano a partir de un Documento_TyC
- **Analizador_LLM**: Componente abstracto que envía texto al modelo de lenguaje y retorna un resultado de análisis estructurado
- **AnalysisResult**: Esquema Pydantic que contiene: is_valid_terms (bool), summary_points (List[str], exactamente 5 elementos), risk_clauses (List[RiskClause]), rejection_reason (Optional[str])
- **RiskClause**: Esquema Pydantic que contiene: title (str), severity (Enum: HIGH, MEDIUM, LOW), explanation (str), quote (str, opcional)
- **Chunking**: Proceso de dividir texto largo en fragmentos por párrafos para análisis independiente
- **Map_Reduce**: Estrategia de análisis donde cada fragmento se analiza independientemente (Map) y luego se consolidan en un único AnalysisResult (Reduce)
- **Documento_Escaneado**: PDF que no contiene texto seleccionable (imagen escaneada)
- **Disclaimer_Legal**: Aviso visible indicando que el análisis es generado por IA con fines informativos y no constituye asesoría legal profesional

## Requirements

### Requirement 1: Carga de documentos

**User Story:** Como usuario, quiero subir un documento de términos y condiciones en formato PDF o Word, para que el sistema pueda analizar su contenido.

#### Acceptance Criteria

1. WHEN el usuario selecciona un archivo con extensión .pdf o .docx, THE Sistema SHALL aceptar el archivo para procesamiento
2. WHEN el usuario intenta subir un archivo con extensión diferente a .pdf o .docx, THE Sistema SHALL rechazar el archivo y mostrar un mensaje indicando que solo se aceptan formatos PDF y Word
3. WHEN el archivo subido excede el tamaño máximo configurado (por defecto 10 MB), THE Sistema SHALL rechazar el archivo y mostrar un mensaje indicando que el tamaño excede el límite permitido
4. WHEN el usuario sube un archivo válido, THE Sistema SHALL validar la extensión y el tamaño antes de iniciar la extracción de texto

### Requirement 2: Extracción de texto

**User Story:** Como usuario, quiero que el sistema extraiga automáticamente el texto de mi documento, para que pueda ser analizado sin intervención manual.

#### Acceptance Criteria

1. WHEN el Sistema recibe un archivo PDF válido, THE Extractor SHALL extraer el texto utilizando la librería pypdf
2. WHEN el Sistema recibe un archivo Word (.docx) válido, THE Extractor SHALL extraer el texto utilizando la librería python-docx
3. WHEN el texto extraído de un PDF tiene menos de 100 caracteres, THE Sistema SHALL considerar el documento como escaneado, lanzar ScannedDocumentException y retornar HTTP 400 con mensaje informando que el documento no puede procesarse en esta versión
4. WHEN el archivo subido está corrupto o es ilegible, THE Sistema SHALL retornar un mensaje claro indicando que el archivo no pudo ser leído
5. WHEN el texto extraído excede el límite máximo configurado (por defecto 20,000 palabras), THE Sistema SHALL rechazar el documento e informar al usuario que el contenido excede la capacidad de análisis

### Requirement 3: Estrategia de documentos largos (Map-Reduce)

**User Story:** Como usuario, quiero que documentos extensos sean analizados correctamente, para que el sistema maneje cualquier longitud de documento dentro del límite.

#### Acceptance Criteria

1. WHEN el texto extraído excede 12,000 caracteres, THE Sistema SHALL dividir el texto en fragmentos por párrafos para análisis independiente
2. WHEN el texto se divide en fragmentos, THE Analizador_LLM SHALL analizar cada fragmento de forma independiente (fase Map)
3. WHEN todos los fragmentos han sido analizados, THE Sistema SHALL consolidar los resultados parciales en un único AnalysisResult (fase Reduce), eliminando cláusulas de riesgo duplicadas o equivalentes
4. WHEN el texto extraído tiene 12,000 caracteres o menos, THE Analizador_LLM SHALL analizar el texto completo en una sola invocación

### Requirement 4: Análisis mediante modelo de lenguaje

**User Story:** Como usuario, quiero que un modelo de lenguaje analice el documento, para recibir un resumen comprensible y alertas sobre cláusulas riesgosas.

#### Acceptance Criteria

1. WHEN el Analizador_LLM completa el análisis exitosamente, THE Sistema SHALL retornar un AnalysisResult con exactamente 5 puntos de resumen sobre lo que el usuario acepta y qué pueden hacer con sus datos
2. WHEN el Analizador_LLM completa el análisis exitosamente, THE Sistema SHALL retornar una lista de cláusulas marcadas como sospechosas o riesgosas, cada una con nivel de severidad (HIGH, MEDIUM, LOW) y explicación en lenguaje simple
3. WHEN la comunicación con el LLM excede el tiempo máximo configurado (por defecto 30 segundos por fragmento), THE Sistema SHALL cancelar la operación y retornar un mensaje de error claro al usuario
4. WHEN el AnalysisResult no contiene exactamente 5 summary_points, THE Sistema SHALL reintentar la llamada al LLM una vez
5. IF el segundo intento de llamada al LLM también produce un AnalysisResult sin exactamente 5 summary_points, THEN THE Sistema SHALL registrar el error en logs y retornar un mensaje indicando que el análisis no pudo completarse correctamente
6. WHEN el documento analizado no contiene términos y condiciones reales, THE Sistema SHALL informar al usuario que el contenido no corresponde a un documento de términos y condiciones

### Requirement 5: Interfaz de usuario y experiencia visual

**User Story:** Como usuario, quiero una interfaz clara y visual que me guíe por el proceso, para entender fácilmente los resultados del análisis.

#### Acceptance Criteria

1. WHEN el usuario accede a la aplicación, THE Sistema SHALL renderizar la pantalla de carga de documentos mediante plantilla Jinja2 con formulario de subida y disclaimer legal visible
2. WHEN el usuario sube un documento válido, THE Sistema SHALL mostrar un estado de procesamiento con indicador visual de que el documento está siendo analizado
3. WHEN el análisis se completa exitosamente, THE Sistema SHALL mostrar la pantalla de resultados con el resumen de 5 puntos y las cláusulas de riesgo estructuradas por sección
4. WHEN se muestran cláusulas de riesgo, THE Sistema SHALL utilizar colores de severidad: rojo para HIGH, amarillo para MEDIUM y verde para LOW
5. WHEN se muestra la pantalla de resultados, THE Sistema SHALL presentar el disclaimer legal junto al resumen de 5 puntos sin necesidad de scroll, con contraste suficiente
6. THE Sistema SHALL manejar las transiciones entre pantallas con JavaScript nativo (fetch API) sin recarga de página

### Requirement 6: Disclaimer legal

**User Story:** Como usuario, quiero ver un aviso legal claro, para entender que el análisis es informativo y no constituye asesoría profesional.

#### Acceptance Criteria

1. THE Sistema SHALL mostrar el Disclaimer_Legal en la pantalla de carga de documentos antes de que el usuario suba un archivo
2. THE Sistema SHALL mostrar el Disclaimer_Legal en la pantalla de resultados junto al resumen de 5 puntos sin necesidad de scroll
3. THE Sistema SHALL presentar el Disclaimer_Legal con contraste suficiente para garantizar legibilidad
4. THE Sistema SHALL incluir en el Disclaimer_Legal texto indicando que el análisis es generado por inteligencia artificial con fines informativos y no constituye asesoría legal profesional

### Requirement 7: Privacidad y manejo de datos

**User Story:** Como usuario, quiero que mi documento no sea almacenado después del análisis, para proteger mi información personal.

#### Acceptance Criteria

1. WHEN el análisis se completa o falla, THE Sistema SHALL eliminar el documento subido y el texto extraído de la memoria del servidor, sin persistencia en disco ni base de datos
2. THE Sistema SHALL informar al usuario en la pantalla de carga que el contenido del documento será enviado a una API externa de IA para su análisis
3. THE Sistema SHALL operar de forma stateless, sin base de datos, sin persistencia de documentos y sin historial de usuario

### Requirement 8: Interfaz del LLM (Patrón Strategy)

**User Story:** Como desarrollador, quiero una interfaz abstracta para el LLM, para poder intercambiar proveedores fácilmente.

#### Acceptance Criteria

1. THE Analizador_LLM SHALL implementarse como clase abstracta (abc.ABC) con método async def analyze(self, text: str) -> AnalysisResult
2. WHEN la variable de entorno LLM_PROVIDER tiene valor "mock", THE Sistema SHALL activar MockLLMAnalyzer que retorna respuestas simuladas
3. WHEN la variable de entorno LLM_PROVIDER tiene un valor diferente de "mock", THE Sistema SHALL instanciar el proveedor correspondiente (por ejemplo OpenAILLMAnalyzer)
4. THE Sistema SHALL cargar la API key del LLM exclusivamente desde variables de entorno, sin valores hardcodeados en código

### Requirement 9: Configuración y arranque

**User Story:** Como desarrollador, quiero que la configuración se maneje mediante variables de entorno, para mantener seguridad y flexibilidad en distintos entornos.

#### Acceptance Criteria

1. THE Sistema SHALL cargar todas las variables sensibles y de configuración desde variables de entorno
2. WHEN las variables de entorno requeridas no están configuradas al arranque, THE Sistema SHALL rechazar el inicio de la aplicación con un mensaje descriptivo indicando qué variables faltan
3. THE Sistema SHALL utilizar Pydantic Settings para gestión y validación de configuración
4. THE Sistema SHALL exponer las siguientes variables configurables mediante entorno: tamaño máximo de archivo (por defecto 10 MB), máximo de palabras extraídas (por defecto 20,000), umbral de chunking (por defecto 12,000 caracteres), timeout del LLM (por defecto 30 segundos), proveedor LLM

### Requirement 10: Contrato de API

**User Story:** Como desarrollador frontend, quiero endpoints claros y documentados, para integrar correctamente el frontend con el backend.

#### Acceptance Criteria

1. WHEN se realiza GET /, THE Sistema SHALL renderizar la pantalla principal mediante Jinja2 con formulario de carga y disclaimer
2. WHEN se realiza POST /api/v1/analyze con un archivo válido, THE Sistema SHALL validar extensión y tamaño, procesar el documento y retornar JSON con estructura AnalysisResult
3. WHEN se realiza POST /api/v1/analyze con un archivo inválido, THE Sistema SHALL retornar un código HTTP apropiado (400 para errores de validación) con mensaje descriptivo en español

### Requirement 11: Esquemas de datos

**User Story:** Como desarrollador, quiero esquemas Pydantic bien definidos, para garantizar la integridad de los datos entre componentes.

#### Acceptance Criteria

1. THE Sistema SHALL definir RiskClause con campos: title (str), severity (Enum: HIGH, MEDIUM, LOW), explanation (str), quote (str, opcional)
2. THE Sistema SHALL definir AnalysisResult con campos: is_valid_terms (bool), summary_points (List[str] con exactamente 5 elementos), risk_clauses (List[RiskClause]), rejection_reason (Optional[str])
3. WHEN se valida un AnalysisResult, THE Sistema SHALL rechazar instancias donde summary_points no contenga exactamente 5 elementos
4. THE Sistema SHALL serializar AnalysisResult a JSON para la respuesta del endpoint POST /api/v1/analyze

### Requirement 12: Manejo de errores

**User Story:** Como usuario, quiero mensajes de error claros y específicos, para entender qué salió mal y qué puedo hacer.

#### Acceptance Criteria

1. WHEN el archivo subido está corrupto o es ilegible, THE Sistema SHALL mostrar un mensaje claro indicando que el archivo no pudo ser procesado
2. WHEN el archivo excede el tamaño máximo, THE Sistema SHALL mostrar un mensaje indicando el límite de tamaño permitido
3. WHEN el PDF no contiene texto extraíble (documento escaneado), THE Sistema SHALL mostrar un mensaje indicando que documentos escaneados no son compatibles en esta versión
4. WHEN el formato del archivo no es compatible, THE Sistema SHALL mostrar un mensaje indicando los formatos aceptados (PDF y Word)
5. WHEN el documento no contiene términos y condiciones reales, THE Sistema SHALL mostrar un mensaje indicando que el contenido no corresponde a un documento de TyC
6. WHEN ocurre un error de comunicación con el LLM, THE Sistema SHALL mostrar un mensaje indicando que el servicio de análisis no está disponible temporalmente
