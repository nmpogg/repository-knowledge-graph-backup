from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def missing(resource: str = "Resource") -> AppError:
    return AppError(404, "not_found", f"{resource} not found")


def conflict(message: str) -> AppError:
    return AppError(409, "conflict", message)


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else {}
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=headers,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        # Never serialize SQL, constraint details or bound values.
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "conflict", "message": "Conflicting resource data"}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        fields = [{"field": list(e["loc"]), "type": e["type"]} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "fields": fields}},
        )

    @app.exception_handler(Exception)
    async def unexpected_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Internal server error"}},
        )
