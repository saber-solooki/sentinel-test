from typing import Any

import redis
import redis.asyncio as async_redis

from config import RedisSettings
from pools import SentinelBlockingConnectionPool, SyncSentinelConnectionPool

_redis_pool = None
_sync_redis_pool = None


async def get_redis(
    settings: RedisSettings | None = None,
    **kwargs: Any,
) -> async_redis.Redis:  # type: ignore[type-arg]
    global _redis_pool

    if _redis_pool is None:
        if settings is None:
            raise ValueError('Redis pool was not initialized')
        await init_redis_pool(settings, **kwargs)

    return async_redis.Redis(connection_pool=_redis_pool)


def get_sentinel(settings: RedisSettings, is_async: bool = True) -> async_redis.Sentinel | None:
    redis_package = async_redis if is_async else redis
    return (
        redis_package.Sentinel(settings.sentinel_instances)
        if settings.use_sentinel
        else None
    )


async def init_redis_pool(settings: RedisSettings, **kwargs: Any) -> None:
    global _redis_pool

    if 'encoding' not in kwargs:
        kwargs['encoding'] = 'utf-8'

    _redis_pool = get_pool(settings, **kwargs)


def init_sync_redis_pool_from_model(settings: RedisSettings, **kwargs: Any) -> None:
    global _sync_redis_pool

    _sync_redis_pool = get_pool(settings, is_async=False, **kwargs)


def get_sync_redis() -> redis.Redis:  # type: ignore[type-arg]
    global _sync_redis_pool

    if not _sync_redis_pool:
        raise ValueError('Invalid redis _sync_redis_pool')

    return redis.Redis(connection_pool=_sync_redis_pool)


async def close_redis_pool() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.disconnect()


def close_sync_redis_pool() -> None:
    global _sync_redis_pool
    if _sync_redis_pool is not None:
        _sync_redis_pool.disconnect()


def get_pool(settings: RedisSettings, is_async: bool = True, **kwargs: Any) -> redis.ConnectionPool | async_redis.ConnectionPool:
    redis_package = async_redis if is_async else redis

    pool_args = {
        'url': settings.redis_url,
        'max_connections': settings.max_connections,
        'retry_on_error': settings.redis_retry_on_error,
        'retry': settings.redis_retry,

        'socket_timeout': 10,
        'socket_connect_timeout': 10,
    }

    connection_pool_class = redis_package.ConnectionPool

    if settings.redis_connection_pool_class:
        connection_pool_class = settings.redis_connection_pool_class
    elif settings.use_sentinel and settings.with_blocking:
        connection_pool_class = SentinelBlockingConnectionPool if is_async else SyncSentinelConnectionPool
        pool_args['sentinel_manager'] = get_sentinel(settings, is_async)
        pool_args['service_name'] = settings.sentinel_service_name
    elif settings.use_sentinel:
        connection_pool_class = redis_package.SentinelConnectionPool
        pool_args['sentinel_manager'] = get_sentinel(settings, is_async)
        pool_args['service_name'] = settings.sentinel_service_name


        pool_args.pop('url')
        return connection_pool_class(**pool_args)

    elif settings.with_blocking:
        connection_pool_class = redis_package.BlockingConnectionPool
        kwargs['timeout'] = settings.blocking_timeout

    return connection_pool_class.from_url(**pool_args, **kwargs)
