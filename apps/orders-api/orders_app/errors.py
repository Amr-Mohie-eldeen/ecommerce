from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException


def http_exception_handler(_: Request, exc: HTTPException):
    payload = {"error": {"code": exc.status_code, "message": exc.detail}}
    return JSONResponse(status_code=exc.status_code, content=payload)
