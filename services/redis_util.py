import logging
import json

from redis_manager import RedisManager

def get_description_from_redis(session_id):
    redis_client = RedisManager.get_client()
    res = redis_client.get(session_id)
    logging.info(f"Get data from redis: {res}")

    json_res = json.loads(res)

    return json_res["description"]