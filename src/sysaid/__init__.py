"""Python wrapper for the SysAid REST API."""

from .auth import LoginResult
from .client import SysAid
from .exceptions import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    SysAidError,
    SysAidHTTPError,
    UnauthorizedError,
)
from .models import Field, Record

__version__ = "0.1.0.dev0"

__all__ = [
    "AuthenticationError",
    "BadRequestError",
    "Field",
    "ForbiddenError",
    "LoginResult",
    "NotFoundError",
    "Record",
    "ServerError",
    "SysAid",
    "SysAidError",
    "SysAidHTTPError",
    "UnauthorizedError",
    "__version__",
]
