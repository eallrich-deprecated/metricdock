import datetime
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


def find_whispers():
    whispers = []
    if not os.path.isdir(settings.whisper_path):
        return whispers
    
    # We're going to remove this prefix from results
    prefix = "%s/" % settings.whisper_path
    
    for root, _, files in os.walk(settings.whisper_path):
        root = root.replace(prefix, '')
        for name in files:
            # Drop the extension
            name = name.rsplit('.', 1)[0]
            path = os.path.join(root, name)
            whispers.append(path)
    
    return whispers


@app.route('/fetch')
def fetch():
    response = {'metrics': [w.replace('/','.') for w in find_whispers()]}
    return json.dumps(response)


@app.route('/fetch/<metric>')
def fetch_metric(metric):
    return fetch_metric_hour(metric)


@app.route('/fetch/<metric>/<start>/<end>')
def fetch_metric_interval(metric, start, end):
    wsp = Whisper(metric)
    timeinfo, values = wsp.fetch(start, end)
    start, stop, step = timeinfo
    
    response = {'start': start, 'stop': stop, 'step': step, 'values': values}
    return json.dumps(response)


@app.route('/fetch/<metric>/hour')
def fetch_metric_hour(metric):
    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
    start_ts = one_hour_ago.strftime("%s")
    end_ts = int(time.time())
    
    return fetch_metric_interval(metric, start_ts, end_ts)


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


@app.route('/delete/<metric>', methods=['DELETE'])
def delete(metric):
    """Deletes the Whisper database for the specified metric"""
    path = Whisper.make_db_path(Whisper.make_db_name(metric))
    
    if os.path.isfile(path):
        logger.info("Deleting '%s' at '%s'" % (metric, path))
        os.remove(path)
        try:
            os.removedirs(os.path.dirname(path))
        except OSError, err:
            logger.warning("Unable to remove leaf directory containing deleted Whisper file")
            logger.debug("OSError: %s" % err)
    
    # No content
    return "", 204
