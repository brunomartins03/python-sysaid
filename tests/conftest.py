import os

import pytest

INTEGRATION_ENV = ("SYSAID_URL", "SYSAID_USERNAME", "SYSAID_PASSWORD")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    missing = [name for name in INTEGRATION_ENV if not os.environ.get(name)]
    skip_live = pytest.mark.skip(reason=f"missing env vars: {', '.join(missing)}")
    skip_writes = pytest.mark.skip(reason="SYSAID_ALLOW_WRITES=1 not set")
    for item in items:
        if missing and "integration" in item.keywords:
            item.add_marker(skip_live)
        if os.environ.get("SYSAID_ALLOW_WRITES") != "1" and "destructive" in item.keywords:
            item.add_marker(skip_writes)
