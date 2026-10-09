"""Switch-off for features that have not been verified against a live SysAid server."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from .exceptions import UnverifiedFeatureError

P = ParamSpec("P")
R = TypeVar("R")

# The test suite sets this to ``False`` to keep exercising the disabled code.
DISABLED = True


def unverified(func: Callable[P, R]) -> Callable[P, R]:
    """Make ``func`` raise :class:`UnverifiedFeatureError` instead of running.

    Remove the decorator once the call has been verified against a live server.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if DISABLED:
            raise UnverifiedFeatureError(
                f"{func.__qualname__} is disabled: "
                "it has not been verified against a live SysAid server"
            )
        return func(*args, **kwargs)

    return wrapper
