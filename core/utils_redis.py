from core.utils_db import get_json_system_parameter

import redis

def add_to_redis(id, data, type):
    redis_conf = get_json_system_parameter('REDIS_CONF')
    type_conf = list(filter(lambda x: x['type'] == type, redis_conf['types_conf']))[0]['data']

    r = redis.Redis(host=redis_conf['host'], port=redis_conf['port'], db=type_conf['db'])
    return r.set(id, data, type_conf['expiration_seconds'])

def read_from_redis(id, type):
    redis_conf = get_json_system_parameter('REDIS_CONF')
    type_conf = list(filter(lambda x: x['type'] == type, redis_conf['types_conf']))[0]['data']

    r = redis.Redis(host=redis_conf['host'], port=redis_conf['port'], db=type_conf['db'])
    return r.get(id)