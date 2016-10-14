import logging
import sys
import uuid
from pathlib import Path

import kaptan

from seot import agent

CONFIG_FILE_PATH = Path("conf/config.yml")
SEOT_DIR_PATH = Path.home() / ".seot"
STATE_FILE_PATH = SEOT_DIR_PATH / "state.yml"

logger = logging.getLogger("conf")
logger.setLevel(logging.INFO)
_config = None
_state = None


def get(key=None):
    return _config.get(key)


def save_state():
    with STATE_FILE_PATH.open("w") as f:
        f.write(_state.export())


def init_state():
    if not SEOT_DIR_PATH.exists():
        SEOT_DIR_PATH.mkdir(parents=True)

    logger.info("Generating device UUID")
    _state.upsert("device_id", str(uuid.uuid4()))
    logger.info("Successfully generated device UUID: {0}".format(
        _state.get("device_id")
    ))
    _state.upsert("version", agent.__version__)

    save_state()


def get_state(key=None):
    return _state.get(key)


def init():
    global _config
    global _state

    try:
        logger.info("Loading configurations from {0}".format(CONFIG_FILE_PATH))
        _config = kaptan.Kaptan(handler="yaml")
        _config.import_config(str(CONFIG_FILE_PATH))
        logger.info("Configurations successfully loaded")
    except:
        logger.error("Failed to load configurations")
        sys.exit(1)

    _state = kaptan.Kaptan(handler="yaml")
    if STATE_FILE_PATH.exists():
        try:
            logger.info("Loading states from {0}".format(STATE_FILE_PATH))
            _state.import_config(str(STATE_FILE_PATH))
            logger.info("States successfully loaded")
        except:
            logger.error("Failed to load state")
            sys.exit(1)
    else:
        init_state()
