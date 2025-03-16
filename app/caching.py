import json
import redis
from app.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_EXPIRATION = 60 * 60  # кэш на 1 час

def get_cached_link(short_code: str):
    data = redis_client.get(f"link:{short_code}")
    if data:
        return json.loads(data)
    return None

def set_cached_link(short_code: str, link_data: dict):
    redis_client.setex(f"link:{short_code}", CACHE_EXPIRATION, json.dumps(link_data))

def delete_cached_link(short_code: str):
    redis_client.delete(f"link:{short_code}")
