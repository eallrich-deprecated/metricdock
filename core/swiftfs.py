import logging
import os

import cloudfiles

from . import settings

logger = logging.getLogger(__name__)

def _init():
    """Connects to the Swift service and returns the specified container"""
    if not settings.swift:
        logger.error("Unable to connect to swift: Missing configuration")
        raise RuntimeError("Swift configuration is incomplete")
    
    connection = cloudfiles.get_connection(**settings.swift)
    container_name = settings.swift['container']
    
    # Return the container if it already exists
    for existing_container in connection.get_all_containers():
        if existing_container.name == container_name:
            return existing_container
    
    container = connection.create_container(container_name)
    return container


def write(source, target=None, content_type='binary/octet-stream'):
    """Creates 'target' and loads the contents from 'source'"""
    if target is None:
        target = os.path.basename(source)
    logger.debug("Writing %s as %s" % (source, target))
    container = _init()
    obj = container.create_object(target)
    obj.content_type = 'binary/octet-stream'
    obj.load_from_filename(source)


def read(source, target=None):
    """Saves the contents of 'source' to 'target'
    
    Returns the name of the resulting file."""
    if target is None:
        target = source
    logger.debug("Reading %s as %s" % (source, target))
    container = _init()
    obj = container.get_object(source)
    obj.save_to_filename(target)
    return target


def read_most_recent():
    """Locates and saves the most recently modified object.
    
    Returns the name of the local file with the contents."""
    container = _init()
    latest = None
    for obj in container.get_objects():
        if not latest or obj.last_modified > latest.last_modified:
            latest = obj
    if latest:
        logger.debug("Latest is %s (%s)" % (latest.name, latest.last_modified))
        return read(latest.name)
    else:
        logger.warning("Unable to find any objects, container is empty")
        return None


def trim(keep=10):
    """Removes old objects, leaving only the 'keep' most recent.
    
    Assumes the object names contain timestamps and may therefore be sorted
    to determine relative ages."""
    container = _init()
    names = [o.name for o in container.get_objects()]
    names.sort()
    to_delete = names[:-keep]
    logger.debug("Trimming %d objects from container" % len(to_delete))
    for name in to_delete:
        container.delete_object(name)

