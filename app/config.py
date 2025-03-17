from datetime import timedelta

from pydantic_settings import BaseSettings
from redis.asyncio import ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError


class RedisSettings(BaseSettings):
    sentinel_instances: list = [('127.0.0.1', 26379)]
    sentinel_service_name: str = 'mymaster'
    redis_host: str = '127.0.0.1'
    redis_port: int = 6379
    redis_password: str = ''
    redis_db: int = 0
    max_connections: int = 64
    redis_connection_timeout: int = 60
    with_blocking: bool = False
    blocking_timeout: float = timedelta(minutes=1).total_seconds()
    redis_retry_on_error: list[type[Exception]] | None = [RedisConnectionError]
    redis_retry: Retry | None = Retry(ExponentialBackoff(), 3)
    redis_connection_pool_class: type[ConnectionPool] | None = None  # type: ignore[type-arg]
    use_sentinel: bool = False

    @property
    def redis_url(self) -> str:
        return 'redis://{password}{host}:{port}/{db}'.format(  # noqa: FS002
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=f':{self.redis_password}@' if self.redis_password else '',
        )
