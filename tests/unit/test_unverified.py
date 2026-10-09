from collections.abc import Callable
from typing import Any

import pytest

from sysaid import SysAid, UnverifiedFeatureError, _unverified, oauth

DISABLED_CALLS: list[Callable[[SysAid], Any]] = [
    lambda c: c.service_requests.delete(1),
    lambda c: c.action_items.list(),
    lambda c: c.action_items.iter(),
    lambda c: c.action_items.count(),
    lambda c: c.action_items.approve(1),
    lambda c: c.action_items.reject(1),
    lambda c: c.action_items.complete(1),
    lambda c: c.action_items.reopen(1),
    lambda c: c.assets.list(),
    lambda c: c.assets.iter(),
    lambda c: c.assets.get("a"),
    lambda c: c.assets.search("a"),
    lambda c: c.cis.list(),
    lambda c: c.cis.iter(),
    lambda c: c.cis.update(1, status=2),
    lambda c: c.cis.types(),
    lambda c: c.cis.view_fields(1),
    lambda c: c.cis.relation_types(),
    lambda c: c.cis.relations(1),
    lambda c: c.cis.create_relations(1, [(2, 3)]),
    lambda c: c.cis.delete_relations(1, [(2, 3)]),
    lambda c: c.addons.list(),
    lambda c: c.addons.get("a"),
    lambda c: c.addons.update("a", active=True),
    lambda c: c.addons.test_connection("a"),
    lambda c: c.addons.refresh(),
    lambda c: c.password_services.domains(),
    lambda c: c.password_services.permissions(),
    lambda c: c.password_services.questions("reset", "u"),
    lambda c: c.password_services.unlock(1, []),
    lambda c: c.password_services.reset(1, []),
    lambda c: c.password_services.update_password(1, "p", "t"),
    lambda c: c.reports.operators(),
    lambda c: c.reports.run_preview(1, {}),
    lambda c: SysAid.from_oauth("https://h", "key", "token", "secret"),
    lambda c: oauth.request_token("https://h", "key", "https://cb"),
    lambda c: oauth.authorize_url("https://h", "token"),
    lambda c: oauth.access_token("https://h", "key", "token", "secret", "verifier"),
]


@pytest.mark.parametrize("call", DISABLED_CALLS)
def test_unverified_features_are_disabled(
    client: SysAid, monkeypatch: pytest.MonkeyPatch, call: Callable[[SysAid], Any]
) -> None:
    # No HTTP mock is registered: the call must fail before any request is made.
    monkeypatch.setattr(_unverified, "DISABLED", True)
    with pytest.raises(UnverifiedFeatureError, match="not been verified"):
        call(client)
