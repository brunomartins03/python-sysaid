import os
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from sysaid import ForbiddenError, SysAid, UnauthorizedError


@pytest.fixture(scope="session")
def live() -> Iterator[SysAid]:
    """A logged-in client for the instance named by the ``SYSAID_*`` variables."""
    with SysAid(
        os.environ["SYSAID_URL"],
        os.environ["SYSAID_USERNAME"],
        os.environ["SYSAID_PASSWORD"],
        os.environ.get("SYSAID_ACCOUNT_ID"),
    ) as client:
        yield client


@pytest.fixture(scope="session")
def me(live: SysAid) -> str:
    """Id of the logged-in user."""
    user_id = live.login().user_id
    assert user_id is not None
    return user_id


@contextmanager
def permitted() -> Iterator[None]:
    """Skip the test when the account lacks the permission for the module under test."""
    try:
        yield
    except (UnauthorizedError, ForbiddenError) as exc:
        pytest.skip(f"account not permitted: {exc}")
