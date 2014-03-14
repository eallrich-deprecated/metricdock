import os

# From metricdock/core/settings.py to metricdock/
cwd = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(cwd), os.pardir)


# logging
# -------
logging = {
    'format': '[%(levelname)s] %(message)s',
    'level':  'DEBUG',
}


# redis
# -----
redis_server = {
    'host': 'localhost',
    'port': 6379,
    'db':   0,
}

redis_latest = 'metrics:latest'
redis_latest_bound = 600 # seconds


# whisper
# -------
whisper_path = os.path.join(PROJECT_ROOT, "whisper")
whisper_archives = "10s:24h,1m:7d,5m:30d,1h:2y"
whisper_xfilesfactor = 0.0
whisper_aggregation = "average"
