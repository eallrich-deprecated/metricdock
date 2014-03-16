import json
import logging
import os
import time

from flask import Flask, abort, g, request
import redis

from . import settings
from .whisperdb import Whisper

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
    return str(int(time.time()))


@app.route('/fetch')
def fetch():
    if os.path.isdir(settings.whisper_path):
        top_level = os.listdir(settings.whisper_path)
        response = {'metrics': [name for name in top_level]}
        return json.dumps(response)
    else:
        return json.dumps({'metrics': []})


@app.route('/fetch/<metric>')
def fetch_metric(metric):
    return "Asked for '%s'" % metric


@app.route('/fetch/<metric>/<start>/<end>')
def fetch_metric_interval(metric, start, end):
    return "Asked for '%s' from %d to %d" % (metric, int(start), int(end))


@app.route('/latest')
def latest():
    """Returns a json list of all metrics received recently"""
    metrics = get_redis().zrange(settings.redis_latest, 0, -1)
    logger.info("Latest zset contains %d entries" % len(metrics))
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
    return "%d\n" % n


def save(metrics):
    logger.info("Saving %d metrics" % len(metrics))
    
    now = int(time.time())
    get_redis().zadd(settings.redis_latest, now, json.dumps(metrics))
    
    for m in metrics:
        wsp = Whisper(m['metric'])
        wsp.save(m['value'], m['timestamp'])


@app.route('/publish', methods=['POST'])
def publish():
    """Accepts metrics from clients
    
    Saves metrics to whisper for persistence and also stashes them in a queue
    of latest metrics."""
    if request.content_type != 'application/json':
        abort(415) # Unsupported media type
    
    data = request.get_json()
    
    try:
        # List or dictionary?
        _ = data[0]
    except KeyError:
        # It's a dictionary, make it a list for consistency
        data = [data,]
    
    metrics = []
    
    # Make sure the syntax is as expected. If not, return 400 Bad Syntax
    for document in data:
        clean = {}
        
        # Make sure all the keys exist
        for key in ('metric', 'value', 'timestamp',):
            try:
                clean[key] = document[key]
            except KeyError:
                return "Missing required key '%s'\n" % key, 400
        
        # Float-able value?
        try:
            clean['value'] = float(clean['value'])
        except ValueError:
            return "'value' must be a float\n" % clean['value'], 400
        
        # Int-able timestamp?
        try:
            clean['timestamp'] = int(clean['timestamp'])
        except ValueError:
            return "'timestamp' must be an int\n" % clean['timestamp'], 400
        
        metrics.append(clean)
    
    save(metrics)
    
    # Created
    return "Saved %d metrics\n" % len(metrics), 201
