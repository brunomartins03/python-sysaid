import json
import os
from pathlib import Path
from typing import Any

import pytest

from sysaid import SysAid

INTEGRATION_ENV = ("SYSAID_URL", "SYSAID_USERNAME", "SYSAID_PASSWORD")
FIXTURES = Path(__file__).parent / "fixtures"
BASE_URL = "https://sysaid.test"
API = BASE_URL + "/api/v1"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    missing = [name for name in INTEGRATION_ENV if not os.environ.get(name)]
    skip_live = pytest.mark.skip(reason=f"missing env vars: {', '.join(missing)}")
    skip_writes = pytest.mark.skip(reason="SYSAID_ALLOW_WRITES=1 not set")
    for item in items:
        if missing and "integration" in item.keywords:
            item.add_marker(skip_live)
        if os.environ.get("SYSAID_ALLOW_WRITES") != "1" and "destructive" in item.keywords:
            item.add_marker(skip_writes)


@pytest.fixture
def client() -> SysAid:
    """A client without credentials, so no login call is made."""
    return SysAid(BASE_URL)


@pytest.fixture
def load_fixture() -> Any:
    def load(name: str) -> Any:
        return json.loads((FIXTURES / name).read_text())

    return load
