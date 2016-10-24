import getpass
import logging
import platform
import sys
import uuid
from pathlib import Path

from schema import Optional, Schema, SchemaError
from seot import agent
import yaml

CONFIG_FILE_PATH = Path.home() / ".config/seot/config.yml"
SEOT_DIR_PATH = Path.home() / ".local/share/seot"
STATE_FILE_PATH = SEOT_DIR_PATH / "state.yml"

logger = logging.getLogger(__name__)
_config = {}
_state = {}

_CONFIG_SCHEMA = Schema({
    "agent": {
        "user_id": str,
        "type": str,
        "coordinate": {
            "longitude": float,
            "latitude": float
        }
    },
    Optional("cpp"): {
        Optional("heartbeat_interval", default=60): int,
        Optional("base_url", default="http://localhost:8888/api"): str
    },
    Optional("dpp"): {
        Optional("listen_address", default="0.0.0.0"): str,
        Optional("listen_port", default=51423): int
    },
    Optional("nodes"): [{
        "module": str,
        "class": str
    }]
})

_STATE_SCHEMA = Schema({
    "version": str,
    "agent_id": str
})


def _get(config, key=None):
    if key is None:
        return config

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

    logger.info("Generating agent UUID")
    _state["agent_id"] = str(uuid.uuid4())
    logger.info("Successfully generated agent UUID: {0}".format(
        _state.get("agent_id")
    ))
    _state["version"] = agent.__version__

    save_state()


def get_state(key=None):
    """ Get a state value """
    return _get(_state, key)


def load():
    """ Load configurations from files """
    global _config, _state

    if CONFIG_FILE_PATH.exists():
        try:
            logger.info("Loading configurations from {0}".format(
                CONFIG_FILE_PATH
            ))
            with open(str(CONFIG_FILE_PATH)) as f:
                _config = _CONFIG_SCHEMA.validate(yaml.load(f))
            logger.info("Configurations successfully loaded")
        except SchemaError as e:
            logger.error("Configuration format is wrong: {0}".format(e.code))
            sys.exit(1)
        except Exception as e:
            logger.error("Failed to load configurations: {0}".format(e))
            sys.exit(1)

    if STATE_FILE_PATH.exists():
        try:
            logger.info("Loading states from {0}".format(STATE_FILE_PATH))
            with open(str(STATE_FILE_PATH)) as f:
                _state = _STATE_SCHEMA.validate(yaml.load(f))
            logger.info("States successfully loaded")
        except SchemaError as e:
            logger.error("State format is wrong {0}".format(e.code))
            sys.exit(1)
        except Exception as e:
            logger.error("Failed to load state: {0}".format(e))
            sys.exit(1)
    else:
        _init_state()


def discover_fact():
    """ Discover various platform information """
    kernel = platform.system()
    os_dist = "unknown"
    if kernel == "Darwin":
        os_dist = platform.mac_ver()[0]
    elif kernel == "Linux":
        os_dist = " ".join(platform.linux_distribution())

    _config["fact"] = {
        "agent_version": agent.__version__,
        "arch": platform.machine(),
        "processor": platform.processor(),
        "python": " ".join([
            platform.python_implementation(),
            platform.python_version()
        ]),
        "kernel": kernel,
        "os": os_dist,
        "user": getpass.getuser()
    }
