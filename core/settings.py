logging = {
    'format': '[%(levelname)s] %(message)s',
    'level':  'DEBUG',
}

redis_server = {
    'host': 'localhost',
    'port': 6379,
    'db':   0,
}

redis_latest = 'metrics:latest'
redis_latest_bound = 600 # seconds
