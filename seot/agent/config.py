import logging
import sys
import uuid
from pathlib import Path

from seot import agent
import yaml

CONFIG_FILE_PATH = Path.home() / ".config/seot/config.yml"
SEOT_DIR_PATH = Path.home() / ".local/share/seot"
STATE_FILE_PATH = SEOT_DIR_PATH / "state.yml"

logger = logging.getLogger(__name__)
_config = {
    "cpp": {
        "heartbeat_interval": "60",
        "base_url": "http://localhost:8888/api"
    },
    "dpp": {
        "listen_address": "0.0.0.0",
        "listen_port": "51423"
    },
    "docker": {
        "base_url": "tcp://localhost:1234"
    }
}
_state = {}


def _get(config, key):
    current = config

    for component in key.split("."):
        if component in current:
            current = current.get(component)
        else:
            return None

    return current


def get(key=None):
    """ Get a configuration value """
    return _get(_config, key)


def save_state():
    """ Persis current state """
    with STATE_FILE_PATH.open("w") as f:
        f.write(yaml.dump(_state))


def _init_state():
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
    """ Get a state value """
    return _get(_state, key)


def _merge_dict(dst, src):
    for k, v in src.items():
        if isinstance(v, dict):
            dst.setdefault(k, {})
            _merge_dict(dst[k], v)
        else:
            dst[k] = v

    return dst


def _validate_config():
    failed = False

    if get("device.user_id") is None:
        logger.error("device.user_id is a required config value")
        failed = True
    if get("device.type") is None:
        logger.error("device.type is a required config value")
        failed = True
    if get("device.coordinate.longitude") is None:
        logger.error("device.coordinate.longitude is a required config value")
        failed = True
    if get("device.coordinate.latitude") is None:
        logger.error("device.coordinate.latitude is a required config value")
        failed = True

    if failed:
        sys.exit(1)


def load():
    """ Load configurations from files """
    global _config
    global _state

    if CONFIG_FILE_PATH.exists():
        try:
            logger.info("Loading configurations from {0}".format(
                CONFIG_FILE_PATH
            ))
            with open(str(CONFIG_FILE_PATH)) as f:
                _merge_dict(_config, yaml.load(f))
            logger.info("Configurations successfully loaded")
        except:
            logger.error("Failed to load configurations")
            sys.exit(1)

    if STATE_FILE_PATH.exists():
        try:
            logger.info("Loading states from {0}".format(STATE_FILE_PATH))
            with open(str(STATE_FILE_PATH)) as f:
                _merge_dict(_state, yaml.load(f))
            logger.info("States successfully loaded")
        except:
            logger.error("Failed to load state")
            sys.exit(1)

    _validate_config()
