import logging

from flask import Flask, g
import redis

from . import settings

logging.basicConfig(**settings.logging)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Note that there is no teardown for the redis connection
def get_redis():
    r = getattr(g, '_redis', None)
    if not r:
        r = g._redis = redis.StrictRedis(**settings.redis)
    return r

@app.route('/')
def root():
    logger.info("Root!")
    return "Hello!"

@app.route('/redis')
def redis_test():
    r = get_redis()
    r.set('foo', 'bar')
    return "r.get('foo') => %s" % r.get('foo')
