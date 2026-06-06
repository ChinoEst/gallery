import redis
import json
import os
from dotenv import load_dotenv


load_dotenv()


r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), decode_responses=True)

def get_cache(key: str):
    data = r.get(key)
    if data:
        return json.loads(data)
    return None


def set_cache(key: str, value, expire: int = 3600):
    r.set(key, json.dumps(value), ex=expire)


def delete_cache(key: str):
    r.delete(key)