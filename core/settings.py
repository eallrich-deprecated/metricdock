import logging as logging_module
import os

# From metricdock/core/settings.py to metricdock/
cwd = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(cwd, os.pardir))


# logging
# -------
logging = {
    'format': '[%(levelname)s] %(message)s',
    'level':  'INFO',
}

logging_module.basicConfig(**logging)
logger = logging_module.getLogger(__name__)


# redis
# -----
redis_server = {
    'host': 'localhost',
    'port': 6379,
    'db':   0,
}

redis_latest = 'metrics:latest'
redis_latest_bound = 600 # seconds


# swift
# -----
try:
    swift = {
        'authurl': os.environ['SWIFT_AUTHURL'],
        'username': os.environ['SWIFT_USERNAME'],
        'api_key':  os.environ['SWIFT_API_KEY'],
        'container': os.environ['SWIFT_CONTAINER'],
    }
except KeyError:
    logger.warn("Swift configuration is incomplete; no persistence exists!")
    logger.warn("Have you defined all of the required environment variables?")
    swift = None


# whisper
# -------
whisper_path = os.path.join(PROJECT_ROOT, "whisper")
whisper_archives = "10s:24h,1m:7d,5m:30d,1h:2y"
whisper_xfilesfactor = 0.0
whisper_aggregation = "average"
