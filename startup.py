import logging
import os
import tarfile

from core import settings, swiftfs

logging.basicConfig(**settings.logging)
logger = logging.getLogger(__name__)


def get_whisper_baseline():
    latest = swiftfs.read_most_recent()
    if not latest: # No archive found, container is probably empty
        logger.warning("No whisper archive found in storage")
        return
    
    archive = os.path.join(settings.PROJECT_ROOT, latest)
    tar = tarfile.open(archive)
    tar.extractall()
    tar.close()


if __name__ == "__main__":
    logger.info("Initializing")
    get_whisper_baseline()
    logger.info("Init complete")
