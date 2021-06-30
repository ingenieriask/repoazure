from core.services import SystemParameterHelper

import redis

def add_to_redis(id, data, type):
    redis_conf = SystemParameterHelper.get_json('REDIS_CONF')
    type_conf = list(filter(lambda x: x['type'] == type, redis_conf['types_conf']))[0]['data']

    r = None
    if 'password' in redis_conf:
        r = redis.Redis(host=redis_conf['host'], port=redis_conf['port'], db=type_conf['db'], password=redis_conf['password'])
    else:
        r = redis.Redis(host=redis_conf['host'], port=redis_conf['port'], db=type_conf['db'])
    return r.set(id, data, type_conf['expiration_seconds'])

def read_from_redis(id, type):
    redis_conf = SystemParameterHelper.get_json('REDIS_CONF')
    type_conf = list(filter(lambda x: x['type'] == type, redis_conf['types_conf']))[0]['data']

    r = None
    if 'password' in redis_conf:
        r = redis.Redis(host=redis_conf['host'], port=redis_conf['port'], db=type_conf['db'], password=redis_conf['password']) 
    else:
        r = redis.Redis(host=redis_conf['host'], port=redis_conf['port'], db=type_conf['db'])
    return r.get(id)