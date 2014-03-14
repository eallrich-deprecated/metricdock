import json
import logging
import time

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
        r = g._redis = redis.StrictRedis(**settings.redis_server)
    return r


@app.route('/')
def root():
    return "Hello!"


@app.route('/latest')
def latest():
    """Returns a json list of all metrics received recently"""
    metrics = get_redis().zrange(settings.redis_latest, 0, -1)
    logger.info("Latest zset contains %d metrics" % len(metrics))
    json_style = []
    for m in metrics:
        json_style.extend(json.loads(m))
    return json.dumps(json_style)

@app.route('/trim', methods=['POST'])
def trim():
    """Trims the set of latest metrics to a recent time interval"""
    discard_ts = int(time.time()) - settings.redis_latest_bound
    n = get_redis().zremrangebyscore(settings.redis_latest, '-inf', discard_ts)
    logger.info("Trimmed %d metrics from latest zset" % n)
    return "%d" % n

def save_to_redis(metrics):
    now = int(time.time())
    r.zadd(settings.redis_latest, now, json.dumps(metrics))

@app.route('/publish', methods=['POST'])
def publish():
    logger.debug("Publish called")
