import datetime
import logging
import os
import shutil
import time

import requests

from core import settings, swiftfs

logging.basicConfig(**settings.logging)
logger = logging.getLogger(__name__)


def persist_whisper():
    if not os.path.isdir(settings.whisper_path):
        logger.warning("Whisper path doesn't exist yet; not persisting...")
        return
    
    logger.info("Persisting whisper files in '%s'" % settings.whisper_path)
    files = os.listdir(settings.whisper_path)
    if len(files) == 0:
        logger.warning("No metrics saved yet; not persisting...")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    archive_name = 'whisper_%s' % timestamp
    root = settings.PROJECT_ROOT
    base = os.path.basename(settings.whisper_path)
    archive = shutil.make_archive(archive_name, 'gztar', root, base)
    swiftfs.write(archive)


def trim_persisted_whisper_files():
    swiftfs.trim(keep=10)


def trim_latest_metrics_queue():
    r = requests.get("")
    if r.status_code == 200:
        logger.debug("Flask reported success removing old metrics")
    else:
        logger.warn("Flask reported status %d when removing old metrics!" % r.status_code)


if __name__ == "__main__":
    logger.info("Pseudo-cron started")
    longest_interval = 10 # minutes
    i = 0
    start = 0
    used = 0
    while True:
        start = int(time.time())
        i += 1
        
        # Every minute:
        persist_whisper()
        
        # Every five minutes:
        if i % 5 == 0:
            trim_latest_metrics_queue()
        
        # Every ten minutes:
        if i % 10 == 0:
            trim_persisted_whisper_files()
        
        # Reset at the end of the interval
        if i == longest_interval:
            i = 0
        
        used = int(time.time()) - start
        time.sleep(60 - used) # sleep for the remainder of the minute

