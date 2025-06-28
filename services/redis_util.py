import logging
import json

from redis_manager import RedisManager

def get_description_from_redis(session_id):
    redis_client = RedisManager.get_client()
    res = redis_client.get(session_id)
    logging.info(f"Get data from redis: {res}")

    if res is None:
        return None
    
    json_res = json.loads(res)

    return json_res["description"]


def get_core_concept(session_id):
    redis_client = RedisManager.get_client()
    res = redis_client.get(f"{session_id}_topic")
    logging.info(f"Get core concept from redis: {res}")

    if res is None:
        return None
    json_res = json.loads(res)

    return json_res["core_concept"] if "core_concept" in json_res else None

def get_description_instruction(session_id):
    redis_client = RedisManager.get_client()
    res = redis_client.get(f"{session_id}_instruction")
    logging.info(f"Get instruction from redis: {res}")

    if res is None:
        return None
    
    json_res = json.loads(res)

    if json_res["is_there_any_instruction"]:
        return json_res["instruction"] if "instruction" in json_res else None
    else:
        return None
