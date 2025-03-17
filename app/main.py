import asyncio
import logging
from datetime import datetime

from connections import init_redis_pool, get_sentinel, get_redis
from config import RedisSettings


async def who_is_master():
    settings = RedisSettings()

    await init_redis_pool(settings)
    sentinel_redis = get_sentinel(settings)
    result = await sentinel_redis.discover_master(settings.sentinel_service_name)
    print(result)


async def main():
    settings = RedisSettings()
    settings.use_sentinel = True
    settings.sentinel_instances = [('172.20.0.4', 26379), ('172.20.0.5', 26380), ('172.20.0.6', 26381)]

    while True:
        try:
            redis = await get_redis(settings=settings)
            await redis.set('saber', 1)
            value = await redis.get('saber')
            print(f'value from redis {value} {datetime.now()}')
            await asyncio.sleep(1)
        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
    # asyncio.run(who_is_master())
