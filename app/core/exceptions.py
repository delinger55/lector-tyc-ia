"""Excepciones personalizadas de la aplicación.

Cada excepción tiene un message (español, para el usuario) y un error_code
(inglés, para identificación programática).
"""


class AppBaseException(Exception):
    """Excepción base de la aplicación."""

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class InvalidFormatException(AppBaseException):
    """Formato de archivo no soportado."""

    def __init__(self):
        super().__init__(
            message="Solo se aceptan archivos en formato PDF (.pdf), Word (.docx) o texto (.txt).",
            error_code="INVALID_FORMAT",
        )


class FileTooLargeException(AppBaseException):
    """Archivo excede el tamaño máximo permitido."""

    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"El archivo excede el tamaño máximo permitido de {max_size_mb} MB.",
            error_code="FILE_TOO_LARGE",
        )


class ScannedDocumentException(AppBaseException):
    """PDF sin texto extraíble (imagen escaneada)."""

    def __init__(self):
        super().__init__(
            message=(
                "El documento parece ser escaneado (imagen). "
                "Esta versión solo procesa documentos con texto seleccionable."
            ),
            error_code="SCANNED_DOCUMENT",
        )


class ExtractionError(AppBaseException):
    """Archivo corrupto o ilegible."""

    def __init__(self):
        super().__init__(
            message="No se pudo leer el archivo. Verifique que no esté corrupto.",
            error_code="CORRUPT_FILE",
        )


class TextTooLongException(AppBaseException):
    """Texto extraído excede la capacidad de análisis."""

    def __init__(self, max_words: int):
        super().__init__(
            message=(
                f"El contenido del documento excede la capacidad de análisis "
                f"({max_words:,} palabras máximo)."
            ),
            error_code="TEXT_TOO_LONG",
        )


class LLMTimeoutError(AppBaseException):
    """Timeout en la comunicación con el LLM."""

    def __init__(self):
        super().__init__(
            message="El servicio de análisis no respondió a tiempo. Intente nuevamente.",
            error_code="LLM_TIMEOUT",
        )


class LLMCommunicationError(AppBaseException):
    """Error de red/API con el proveedor LLM."""

    def __init__(self):
        super().__init__(
            message="El servicio de análisis no está disponible temporalmente. Intente más tarde.",
            error_code="LLM_COMMUNICATION_ERROR",
        )


class AnalysisValidationError(AppBaseException):
    """El análisis no pudo completarse tras reintentos."""

    def __init__(self):
        super().__init__(
            message="El análisis no pudo completarse correctamente. Intente nuevamente.",
            error_code="ANALYSIS_FAILED",
        )


class NotTermsException(AppBaseException):
    """El documento no contiene términos y condiciones reales."""

    def __init__(self):
        super().__init__(
            message="El contenido del documento no corresponde a términos y condiciones.",
            error_code="NOT_TERMS",
        )
