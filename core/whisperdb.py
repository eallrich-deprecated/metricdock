import logging
import os
import time

import whisper

from . import settings

logger = logging.getLogger(__name__)

class Whisper(object):
    @staticmethod
    def make_db_name(metric_name):
        return metric_name.replace('.', '/')
    
    def __init__(self, metric):
        self.name = Whisper.make_db_name(metric)
        self.db = os.path.join(settings.whisper_path, self.name)
        
        if not os.path.exists(self.db):
            logger.info("Creating new whisper DB '%s'" % self.name)
            if not os.path.exists(os.path.dirname(self.db)):
                os.makedirs(os.path.dirname(self.db))
            retentions = settings.whisper_archives.split(',')
            logger.debug("Retentions: %s" % retentions)
            # Convert the human-readable retentions into (seconds/period, # periods)
            archives = map(whisper.parseRetentionDef, retentions)
            logger.debug("Archives: %s" % archives)
            whisper.create(
                self.db,
                archives,
                xFilesFactor=settings.whisper_xfilesfactor,
                aggregationMethod=settings.whisper_aggregation
            )
    
    def save(self, value, timestamp):
        whisper.update(self.db, value, timestamp)
    
    def fetch(self, start, end=None):
        if not end:
            end = int(time.time())
        # Returns ((start, end, step), [value1, value2, ...])
        return whisper.fetch(self.db, start, end)

