"""Regression tests for per-host eLabFTW version cache expiry (issue #200).

The bug: elAPI's cache uses ONE global ``date`` to gate freshness for every
host. When one host is re-fetched the global date is reset, so an untouched
host keeps its (possibly stale) cached version while the file as a whole is
still "fresh". A user who switches to that host gets a wrong eLabFTW version
and a wrong "not supported" warning; only ``elapi clear-cache`` recovers it.

The fix gives each host its own expiry timestamp.
"""

from datetime import datetime, timedelta

import pytest

from elapi._core_init import get_cached_data, update_cache
from elapi._names import (
    CACHE_PATH,
    CacheFileProperties,
    CacheModel,
)

EXPIRY = CacheFileProperties.expires_in_days  # 21600 s ("6 hours")


@pytest.fixture(autouse=True)
def _cache_path(tmp_path, monkeypatch):
    """Point CACHE_PATH at a temp file so tests never touch the real cache.

    All cache I/O goes through ``elapi._names.CACHE_PATH`` (module reference),
    so patching the single definition covers every caller.
    """
    import elapi._names as _names

    p = tmp_path / "elapi.json"
    monkeypatch.setattr(_names, "CACHE_PATH", p)
    return p


def _mk_cache(
    hosts,
    *,
    age_seconds=0,
    per_host_age=None,
    date=None,
):
    """Build a cache file on disk.

    hosts: {host: version}
    date:  global cache date (default now - age_seconds)
    per_host_age: {host: seconds} per-host fetch age; when omitted, the
                  legacy shape (no elab_hosts_updated) is written.
    """
    now = datetime.now()
    date = date or (now - timedelta(seconds=age_seconds))
    cache = CacheModel(date=date, elab_hosts=dict(hosts))
    if per_host_age is not None:
        for host, age in per_host_age.items():
            if host in hosts:
                cache.elab_hosts_updated[host] = now - timedelta(seconds=age)
    update_cache(cache)
    return cache


def test_fresh_host_version_is_trusted():
    from elapi.api.api import ElabFTWURL
    from elapi._core_init import get_cached_data as _g

    host = "https://a.example/api/v2"
    _mk_cache({host: "6.0.0"}, per_host_age={host: 10})
    cache = _g()
    from elapi._core_init._cache import host_is_stale
    assert host_is_stale(cache, host) is False


def test_stale_host_version_is_not_trusted():
    from elapi._core_init._cache import host_is_stale

    host = "https://a.example/api/v2"
    # global date is fresh (just written) but this host's own entry is old
    _mk_cache({host: "6.0.0"}, age_seconds=0, per_host_age={host: EXPIRY + 100})
    cache = get_cached_data()
    assert host_is_stale(cache, host) is True


def test_untracked_host_defaults_to_global_date():
    from elapi._core_init._cache import host_is_stale

    host = "https://a.example/api/v2"
    # legacy file: no per-host timestamp -> fall back to the global date
    _mk_cache({host: "6.0.0"}, age_seconds=10)  # fresh global
    cache = get_cached_data()
    assert host_is_stale(cache, host) is False

    _mk_cache({host: "6.0.0"}, age_seconds=EXPIRY + 100)  # stale global
    cache = get_cached_data()
    assert host_is_stale(cache, host) is True


def test_issue_repro_refetches_stale_second_host(monkeypatch):
    """The exact issue scenario: A was just re-fetched (global date now fresh),
    B's entry is old. Switching to B must re-fetch B, not trust its stale value.
    """
    import elapi.api.api as api

    host_a = "https://a.example/api/v2"
    host_b = "https://b.example/api/v2"

    # B is old (stale), A was fetched 10s ago (fresh) -> bumps global date.
    _mk_cache(
        {host_a: "6.0.4", host_b: "5.6.12"},
        age_seconds=0,
        per_host_age={host_a: 10, host_b: EXPIRY + 100},
    )

    fetched = []

    class FakeResp:
        is_success = True

        def json(self):
            return {"elabftw_version": "6.0.0"}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def get(self, url, **k):
            fetched.append(url)
            return FakeResp()

    monkeypatch.setattr(api, "SimpleClient", FakeClient)
    monkeypatch.setattr(api, "get_active_host", lambda skip_validation=False: host_b)
    monkeypatch.setattr(api, "get_active_api_token", lambda skip_validation=False: "tok")

    # B is stale -> must be re-fetched (not trusted at 5.6.12).
    version = api.ElabFTWURL.get_elab_version()
    assert version == "6.0.0"
    assert any(host_b in u for u in fetched), f"B should have been re-fetched, got {fetched}"


def test_refetching_one_host_does_not_refresh_another():
    """The class of the bug: after A is fetched, B must keep its OWN (old)
    timestamp, not inherit the new global date."""
    from datetime import timedelta as _td

    host_a = "https://a.example/api/v2"
    host_b = "https://b.example/api/v2"
    _mk_cache(
        {host_a: "6.0.0", host_b: "5.6.12"},
        per_host_age={host_a: 10, host_b: 10},
    )
    # B's entry is now ~1h old (stale for a 6h window? no, fresh) -- age it
    # to 5h so a fetch of A must NOT bring B back to fresh.
    import elapi._names as _names
    import json as _json

    raw = _json.loads(_names.CACHE_PATH.read_text(encoding="utf-8"))
    b_old = (datetime.now() - _td(hours=5)).isoformat()
    raw["elab_hosts_updated"][host_b] = b_old
    _names.CACHE_PATH.write_text(
        _json.dumps(raw, indent=4), encoding="utf-8"
    )

    from elapi._core_init import get_cached_data as _g
    from elapi._core_init._cache import host_is_stale, update_cache

    cache = _g()
    # B is fresh (5h < 6h window); A was fetched 10s ago.
    assert host_is_stale(cache, host_b) is False
    # Simulate fetching A (exactly what get_elab_version() does).
    cache.elab_hosts[host_a] = "6.0.1"
    cache.elab_hosts_updated[host_a] = datetime.now()
    update_cache(cache)  # re-stamps the GLOBAL date too

    # Re-read: B must still carry its own 5h-old timestamp. With the old
    # global-date model, B would look fresh right up to 6h after A's fetch.
    cache2 = _g()
    b_fetched = cache2.elab_hosts_updated[host_b]
    a_fetched = cache2.elab_hosts_updated[host_a]
    assert a_fetched > b_fetched, "A refreshed, B must not have been"
    b_age = (datetime.now() - b_fetched).total_seconds()
    assert b_age > 5 * 3600, f"B's entry was refreshed: age {b_age:.0f}s"


def test_file_older_than_a_day_is_detected_stale():
    """Sibling bug: the file-level reset used ``.seconds`` (0-86399) so a cache
    older than 24h could still look fresh. Use total seconds instead."""
    from elapi._core_init._cache import cache_is_stale, host_is_stale
    from elapi._names import CACHE_PATH as _CP, CacheModel as _CM

    host = "https://a.example/api/v2"
    # A legacy file (no per-host timestamps) whose global date is 30h old.
    # Written directly: update_cache() would re-stamp the global date.
    cache = _CM(
        date=datetime.now() - timedelta(seconds=30 * 3600),
        elab_hosts={host: "6.0.0"},
    )
    _CP.write_text(
        cache.model_dump_json(indent=4), encoding="utf-8"
    )
    import json as _json

    raw = _json.loads(_CP.read_text(encoding="utf-8"))
    cache = _CM(**raw)
    assert (datetime.now() - cache.date).total_seconds() > EXPIRY
    # With total_seconds a 30h-old file is stale; with .seconds it would
    # report 12h (< 24h) and slip through.
    assert cache_is_stale(cache) is True
    assert host_is_stale(cache, host) is True
