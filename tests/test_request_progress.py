"""HTTP-level workflow tests using in-memory MongoDB; no Atlas/API credentials."""
import importlib
import sys
import types
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import mongomock
import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Avoid the production database module's connection and index creation on import.
_fake_db = types.ModuleType('app.db')
_fake_db.requests_col = None
_fake_db.donations_col = None
with patch.dict(sys.modules, {'app.db': _fake_db}):
    routes = importlib.import_module('app.routes.requests')

HELPER = {'X-Device-Token': 'test-helper-secret'}
OTHER = {'X-Device-Token': 'test-other-secret'}
CREATOR = {'X-Device-Token': 'test-creator-secret'}


@pytest.fixture()
def ctx(monkeypatch):
    database = mongomock.MongoClient().test
    monkeypatch.setattr(routes, 'requests_col', database.requests)
    monkeypatch.setattr(routes, 'donations_col', database.donations)
    app = FastAPI()
    app.include_router(routes.router, prefix='/v1')
    with TestClient(app) as client:
        yield client, database


def create(client, goal=20):
    response = client.post('/v1/requests', headers=CREATOR, json={
        'raw_text': 'Need food delivered', 'category': 'groceries',
        'urgency_window': 'today', 'severity': 3, 'items': [],
        'estimated_total': goal, 'requester_afford': 0,
        'location': {'lat': 42.36, 'lng': -71.06},
    })
    assert response.status_code == 200, response.text
    return response.json()['request']['id']


def detail(client, rid, headers=HELPER):
    response = client.get(f'/v1/requests/{rid}', headers=headers)
    assert response.status_code == 200
    return response.json()['request']


def claim(client, rid, headers=HELPER):
    return client.post(f'/v1/requests/{rid}/claim', headers=headers)


def advance(client, rid, status, headers=HELPER):
    return client.patch(f'/v1/requests/{rid}/status', json={'status': status}, headers=headers)


def test_full_funding_claim_delivery_history(ctx):
    client, db = ctx
    rid = create(client)
    first = detail(client, rid)
    assert first['status_history'][0]['status'] == 'open'
    donated = client.post(f'/v1/requests/{rid}/donate', headers=OTHER, json={'amount': 20})
    assert donated.status_code == 200
    assert donated.json()['request']['status'] == 'funded'
    assert claim(client, rid).status_code == 200
    assert advance(client, rid, 'on_the_way').status_code == 200
    assert advance(client, rid, 'delivered').status_code == 200
    result = detail(client, rid)
    assert result['status'] == 'delivered'
    assert [e['status'] for e in result['status_history']] == ['open', 'funded', 'claimed', 'on_the_way', 'delivered']
    assert all(e['at'].endswith(('Z', '+00:00')) for e in result['status_history'])
    assert result['updated_at'] == result['status_history'][-1]['at']
    assert result['is_claiming_helper'] is True


def test_no_funding_needed_can_be_claimed_immediately(ctx):
    client, _ = ctx
    rid = create(client, 0)
    assert detail(client, rid)['status'] == 'funded'
    assert claim(client, rid).status_code == 200


def test_cannot_claim_unfunded_request(ctx):
    client, _ = ctx
    assert claim(client, create(client)).status_code == 409


def test_other_helper_cannot_claim_or_update(ctx):
    client, _ = ctx
    rid = create(client, 0)
    claim(client, rid)
    assert claim(client, rid, OTHER).status_code == 409
    assert advance(client, rid, 'on_the_way', OTHER).status_code == 403
    assert detail(client, rid, OTHER)['is_claiming_helper'] is False


def test_no_helper_credentials_in_any_public_response(ctx):
    client, _ = ctx
    rid = create(client, 0)
    response = claim(client, rid)
    advanced = advance(client, rid, 'on_the_way')
    for value in [response.text, advanced.text,
                  client.get(f'/v1/requests/{rid}').text,
                  client.get('/v1/requests').text]:
        assert 'test-helper-secret' not in value
        assert 'helper_id' not in value
    assert detail(client, rid, {})['is_claiming_helper'] is False


def test_missing_device_header_is_rejected(ctx):
    client, _ = ctx
    rid = create(client, 0)
    assert claim(client, rid, {}).status_code == 400
    assert advance(client, rid, 'on_the_way', {}).status_code == 400


def test_cannot_skip_or_reverse_delivery_steps(ctx):
    client, _ = ctx
    rid = create(client, 0)
    claim(client, rid)
    assert advance(client, rid, 'delivered').status_code == 409
    assert advance(client, rid, 'claimed').status_code == 422
    advance(client, rid, 'on_the_way')
    advance(client, rid, 'delivered')
    assert advance(client, rid, 'on_the_way').status_code == 409


def test_retries_do_not_duplicate_events_or_change_time(ctx):
    client, _ = ctx
    rid = create(client, 0)
    first = claim(client, rid).json()['request']
    assert claim(client, rid).json()['request'] == first
    for state in ['on_the_way', 'delivered']:
        first = advance(client, rid, state).json()['request']
        assert advance(client, rid, state).json()['request'] == first
    history = detail(client, rid)['status_history']
    assert len(history) == 5


def test_old_delivered_endpoint_uses_same_rules(ctx):
    client, _ = ctx
    rid = create(client, 0)
    claim(client, rid)
    assert client.post(f'/v1/requests/{rid}/delivered', headers=HELPER).status_code == 409
    advance(client, rid, 'on_the_way')
    assert client.post(f'/v1/requests/{rid}/delivered', headers=OTHER).status_code == 403
    assert client.post(f'/v1/requests/{rid}/delivered', headers=HELPER).status_code == 200


def test_last_updated_does_not_change_on_reads_or_reranking(ctx):
    client, db = ctx
    rid = create(client)
    earlier = datetime.now(timezone.utc) - timedelta(hours=2)
    db.requests.update_one({'_id': ObjectId(rid)}, {'$set': {'updated_at': earlier}})
    before = detail(client, rid)['updated_at']
    client.get('/v1/requests')
    assert client.post('/v1/ai/rank').status_code == 200
    assert detail(client, rid)['updated_at'] == before
    assert db.requests.find_one({'_id': ObjectId(rid)})['ranked_at'] > earlier.replace(tzinfo=None)


def test_partial_donation_updates_time_without_status_event(ctx):
    client, db = ctx
    rid = create(client)
    earlier = datetime.now(timezone.utc) - timedelta(hours=1)
    db.requests.update_one({'_id': ObjectId(rid)}, {'$set': {'updated_at': earlier}})
    before = detail(client, rid)['updated_at']
    response = client.post(f'/v1/requests/{rid}/donate', headers=OTHER, json={'amount': 5})
    assert response.status_code == 200
    after = detail(client, rid)
    assert after['updated_at'] != before
    assert after['status'] == 'open'
    assert len(after['status_history']) == 1


def test_list_exposes_utc_timestamps_and_new_status_filter(ctx):
    client, _ = ctx
    rid = create(client, 0)
    claim(client, rid)
    advance(client, rid, 'on_the_way')
    rows = client.get('/v1/requests?status=on_the_way').json()['requests']
    assert rows[0]['id'] == rid
    assert rows[0]['updated_at'].endswith(('Z', '+00:00'))
    assert rows[0]['created_at'].endswith(('Z', '+00:00'))


def test_legacy_claim_can_advance_without_migration(ctx):
    client, db = ctx
    rid = create(client, 0)
    claim(client, rid)
    db.requests.update_one({'_id': ObjectId(rid)}, {'$unset': {'status_history': ''}})
    assert advance(client, rid, 'on_the_way').status_code == 200
    events = detail(client, rid)['status_history']
    assert [e['status'] for e in events] == ['open', 'claimed', 'on_the_way']


def test_legacy_delivery_time_is_not_fabricated(ctx):
    client, db = ctx
    rid = create(client, 0)
    claim(client, rid)
    db.requests.update_one({'_id': ObjectId(rid)}, {'$set': {'status': 'delivered'}, '$unset': {'status_history': ''}})
    events = detail(client, rid)['status_history']
    assert events[-1] == {'status': 'delivered', 'at': None}


def test_legacy_missing_updated_time_falls_back_to_created(ctx):
    client, db = ctx
    rid = create(client)
    db.requests.update_one({'_id': ObjectId(rid)}, {'$unset': {'updated_at': ''}})
    result = detail(client, rid)
    assert result['updated_at'] == result['created_at']


def test_unknown_or_malformed_ids(ctx):
    client, _ = ctx
    assert advance(client, str(ObjectId()), 'on_the_way').status_code == 404
    assert advance(client, 'bad-id', 'on_the_way').status_code == 400
    assert claim(client, str(ObjectId())).status_code == 404


def test_cancelled_request_cannot_be_advanced(ctx):
    client, db = ctx
    rid = create(client, 0)
    claim(client, rid)
    db.requests.update_one({'_id': ObjectId(rid)}, {'$set': {'status': 'cancelled'}})
    assert advance(client, rid, 'on_the_way').status_code == 409


def test_invalid_donation_does_not_create_record(ctx):
    client, db = ctx
    rid = create(client, 0)
    claim(client, rid)
    assert client.post(f'/v1/requests/{rid}/donate', headers=OTHER, json={'amount': 5}).status_code == 409
    assert db.donations.count_documents({}) == 0


def test_concurrent_claim_cannot_be_overwritten_by_donation(ctx, monkeypatch):
    client, db = ctx
    rid = create(client, 0)
    original = db.requests.find_one_and_update
    raced = False
    def intercept(query, update, **kwargs):
        nonlocal raced
        if not raced and 'funded_amount' in query:
            raced = True
            original({'_id': ObjectId(rid), 'status': 'funded'}, {'$set': {'status': 'claimed', 'claim': {'helper_id': 'other'}}})
        return original(query, update, **kwargs)
    monkeypatch.setattr(db.requests, 'find_one_and_update', intercept)
    response = client.post(f'/v1/requests/{rid}/donate', headers=OTHER, json={'amount': 5})
    assert response.status_code == 409
    assert db.requests.find_one({'_id': ObjectId(rid)})['status'] == 'claimed'
    assert db.donations.count_documents({}) == 0


def test_concurrent_transition_retry_records_one_event(ctx, monkeypatch):
    client, db = ctx
    rid = create(client, 0)
    claim(client, rid)
    original = db.requests.find_one_and_update
    raced = False
    def intercept(query, update, **kwargs):
        nonlocal raced
        if not raced and query.get('status') == 'claimed':
            raced = True
            original(query, update, **kwargs)
        return original(query, update, **kwargs)
    monkeypatch.setattr(db.requests, 'find_one_and_update', intercept)
    assert advance(client, rid, 'on_the_way').status_code == 200
    assert sum(e['status'] == 'on_the_way' for e in detail(client, rid)['status_history']) == 1
