import json
from datetime import datetime
from json import JSONDecodeError

from pydantic import ValidationError

from .. import _names
from .._names import CacheFileProperties, CacheModel
from ._loggers import Logger

logger = Logger()


def cache_is_stale(cache: CacheModel) -> bool:
    """Is the cache file itself older than the expiry window?

    Uses ``total_seconds()``: with plain ``.seconds`` a timedelta of, e.g.,
    2 days and 2 hours reports only 2 hours and would pass the check.
    """
    age = (datetime.now() - cache.date).total_seconds()
    return age > CacheFileProperties.expires_in_days


def host_is_stale(cache: CacheModel, host: str) -> bool:
    """Is *this host's* cached eLabFTW version older than the expiry window?

    Each host's version has its own expiry timestamp (``elab_hosts_updated``)
    so re-fetching one host no longer makes the other hosts' cached versions
    look fresh. Hosts written by older elAPI versions (no per-host timestamp)
    fall back to the cache file's global date.
    """
    fetched_at = cache.elab_hosts_updated.get(host, cache.date)
    age = (datetime.now() - fetched_at).total_seconds()
    return age > CacheFileProperties.expires_in_days


def _new_cache() -> CacheModel:
    # A stale/invalid cache file is replaced by a fresh, empty one, exactly
    # as before: every host's version is re-fetched from its server on next
    # use and re-stamped at that point.
    cache_ = CacheModel(date=datetime.now())
    update_cache(cache_)
    return cache_


def get_cached_data() -> CacheModel:
    try:
        raw_cache = json.loads(
            _names.CACHE_PATH.read_text(encoding=CacheFileProperties.encoding)
        )
    except (FileNotFoundError, JSONDecodeError, UnicodeDecodeError):
        raw_cache = {}
    try:
        cache = CacheModel(**raw_cache)
    except ValidationError:
        logger.debug(
            f"Cache found in '{_names.CACHE_PATH}' is either empty or invalid. "
            f"New cache will be created."
        )
        return _new_cache()
    else:
        if cache_is_stale(cache):
            logger.debug(
                f"Cache found in '{_names.CACHE_PATH}' is older than "
                f"{CacheFileProperties.expires_in_days} seconds. "
                f"New cache will be created."
            )
            return _new_cache()
        else:
            return cache


def update_cache(cache: CacheModel) -> None:
    cache.date = datetime.now()
    # Write through the module reference (not the module-level name) so the
    # location can be redirected, e.g. by tests.
    if not _names.CACHE_PATH.exists():
        _names.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _names.CACHE_PATH.touch(exist_ok=True)
    _names.CACHE_PATH.write_text(
        cache.model_dump_json(indent=CacheFileProperties.indent),
        encoding=CacheFileProperties.encoding,
    )
