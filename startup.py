import logging
import os
import tarfile

import requests

from core import core, settings, swiftfs

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


def get_latest_from_cluster():
    try:
        servers = os.environ['DOCKS'].split(',')
    except KeyError:
        logger.warning("No servers defined for retrieving latest metrics.")
        return
    
    for server in servers:
        url = "%s/latest" % server
        logger.debug("Retrieving %s" % url)
        try:
            # Because we have less than 60 seconds, we're not going to wait
            # around for a long timeout. If we don't hear back almost
            # immediately we need to abandon the attempt and move on (even at
            # the risk of losing some metrics). Hopefully one of the other
            # redundant metricdocks will be reachable.
            r = requests.get(url, timeout=10)
            latest = r.json()
            with core.app.app_context():
                core.save(latest)
        except requests.exceptions.RequestException as exc:
            logger.error("Unable to retrieve /latest from %s" % server)
            logger.error("Exception: %s" % exc)


if __name__ == "__main__":
    logger.info("Initializing")
    get_whisper_baseline()
    get_latest_from_cluster()
    logger.info("Init complete")
