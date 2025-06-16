import redis
import os
from dotenv import load_dotenv

load_dotenv()

class RedisManager:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = redis.Redis(
                host=os.getenv("REDIS_HOST", "host.docker.internal"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )
        return cls._client
