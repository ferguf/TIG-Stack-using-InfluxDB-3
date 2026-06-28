import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger("uvicorn.error")

async def global_exception_handler(request: Request, exc: Exception):
    """Catches all unhandled 500 errors and formats them as JSON."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Catches 422 Pydantic schema validation errors and logs the exact failure."""
    logger.error("Validation failed for request %s", request.url)
    logger.error("Errors: %s", exc.errors())
    logger.error("Body: %s", exc.body)

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": jsonable_encoder(exc.errors()),
            "body": exc.body
        }
    )

def setup_exception_handlers(app: FastAPI):
    """Mounts the exception handlers to the FastAPI application instance."""
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)