import json
from datetime import datetime
from json import JSONDecodeError

from pydantic import ValidationError

from .._names import CacheFileProperties, CacheModel, CACHE_PATH
from ._loggers import Logger

logger = Logger()


def get_cached_data() -> CacheModel:
    def _new_cache() -> CacheModel:
        cache_ = CacheModel(date=datetime.now())
        update_cache(cache_)
        return cache_

    try:
        raw_cache = json.loads(
            CACHE_PATH.read_text(encoding=CacheFileProperties.encoding)
        )
    except (FileNotFoundError, JSONDecodeError, UnicodeDecodeError):
        raw_cache = {}
    try:
        cache = CacheModel(**raw_cache)
    except ValidationError:
        logger.debug(
            f"Cache found in '{CACHE_PATH}' is either empty or invalid. "
            f"New cache will be created."
        )
        return _new_cache()
    else:
        if (datetime.now() - cache.date).seconds > CacheFileProperties.expires_in_days:
            logger.debug(
                f"Cache found in '{CACHE_PATH}' is older than "
                f"{CacheFileProperties.expires_in_days} days. "
                f"New cache will be created."
            )
            return _new_cache()
        else:
            return cache


def update_cache(cache: CacheModel) -> None:
    cache.date = datetime.now()
    if not CACHE_PATH.exists():
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.touch(exist_ok=True)
    CACHE_PATH.write_text(
        cache.model_dump_json(indent=CacheFileProperties.indent),
        encoding=CacheFileProperties.encoding,
    )
