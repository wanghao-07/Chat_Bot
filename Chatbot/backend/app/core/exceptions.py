class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND", status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)


class LLMError(AppError):
    def __init__(
        self,
        message: str = "LLM service error",
        code: str = "LLM_ERROR",
        status_code: int = 502,
    ):
        super().__init__(message, code=code, status_code=status_code)


class RAGError(AppError):
    def __init__(self, message: str = "Knowledge base error"):
        super().__init__(message, code="RAG_ERROR", status_code=500)
