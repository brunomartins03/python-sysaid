import pytest
import responses
from responses.matchers import json_params_matcher, query_param_matcher

from sysaid import RelationError, SysAid
from sysaid.resources.cis import Relation
from tests.conftest import API


@responses.activate
def test_list_uses_support_barcode_param(client: SysAid) -> None:
    responses.get(
        API + "/ci",
        json=[{"id": "1", "info": [{"key": "ci_name", "value": "n", "editable": "false"}]}],
        match=[
            query_param_matcher(
                {"ids": "1,2", "supportBarcode": "true", "fields": "ci_name", "owner": "x"}
            )
        ],
    )
    cis = client.cis.list(ids=[1, 2], support_barcode=True, fields=["ci_name"], owner="x")
    assert cis[0]["ci_name"] == "n"
    assert cis[0].fields["ci_name"].editable is False


@responses.activate
def test_iter(client: SysAid) -> None:
    responses.get(
        API + "/ci",
        json=[{"id": "1", "info": []}],
        match=[query_param_matcher({"offset": "0", "limit": "3"})],
    )
    assert [c.id for c in client.cis.iter(page_size=3)] == ["1"]


@responses.activate
def test_update(client: SysAid) -> None:
    responses.put(
        API + "/ci/273",
        match=[
            json_params_matcher(
                {
                    "id": "273",
                    "info": [{"key": "status", "value": 2}, {"key": "owner", "value": "s"}],
                }
            )
        ],
    )
    client.cis.update(273, status=2, owner="s")


@responses.activate
def test_types_view_and_relation_types(client: SysAid) -> None:
    responses.get(
        API + "/ci/type",
        json=[{"id": "1", "name": "Asset"}],
        match=[query_param_matcher({"supportBarcode": "false"})],
    )
    responses.get(
        API + "/ci/view/180",
        json=[{"key": "a"}],
        match=[query_param_matcher({"view": "barcode_book"})],
    )
    responses.get(API + "/ci/relationtypes", json=[{"relationTypeId": 5}])
    assert client.cis.types(support_barcode=False)[0]["name"] == "Asset"
    assert client.cis.view_fields(180, view="barcode_book") == [{"key": "a"}]
    assert client.cis.relation_types()[0]["relationTypeId"] == 5


@responses.activate
def test_relations_roundtrip(client: SysAid) -> None:
    body = [{"dest": 2, "ciRelationType": 3}, {"dest": 1, "ciRelationType": 2}]
    responses.get(API + "/ci/9/relation", json=[{"src": 9, "dest": 1, "ciRelationType": 2}])
    responses.post(API + "/ci/9/relation", body="OK", match=[json_params_matcher(body)])
    responses.delete(API + "/ci/9/relation", body="OK", match=[json_params_matcher(body)])
    assert client.cis.relations(9)[0]["dest"] == 1
    relations: list[Relation] = [(2, 3), {"dest": 1, "ciRelationType": 2}]
    client.cis.create_relations(9, relations)
    client.cis.delete_relations(9, relations)


@responses.activate
def test_create_relations_failure_lists_items(client: SysAid) -> None:
    message = "Ci:9 Invalid CI id 100,Ci:9 Invalid CI Relation type 11"
    responses.post(API + "/ci/9/relation", status=400, json={"status": 400, "message": message})
    with pytest.raises(RelationError) as info:
        client.cis.create_relations(9, [(100, 3)])
    assert info.value.failures == ["Ci:9 Invalid CI id 100", "Ci:9 Invalid CI Relation type 11"]
    assert info.value.status_code == 400
