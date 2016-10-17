import getpass
import logging
import platform
import sys
import uuid
from pathlib import Path

from seot import agent
import yaml

CONFIG_FILE_PATH = Path.home() / ".config/seot/config.yml"
SEOT_DIR_PATH = Path.home() / ".local/share/seot"
STATE_FILE_PATH = SEOT_DIR_PATH / "state.yml"

REQUIRED_KEYS = [
    "agent.user_id",
    "agent.type",
    "agent.coordinate.longitude",
    "agent.coordinate.latitude"
]

logger = logging.getLogger(__name__)
_config = {
    "agent": {
    },
    "cpp": {
        "heartbeat_interval": "60",
        "base_url": "http://localhost:8888/api"
    },
    "dpp": {
        "listen_address": "0.0.0.0",
        "listen_port": "51423"
    },
    "source": {
    },
    "transformer": {
        "type": "docker",
        "url": "tcp://localhost:2375"
    },
    "sink": {
    },
}
_state = {}


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

    for key in REQUIRED_KEYS:
        if get(key) is None:
            logger.error("{0} is a required config key".format(key))
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
    else:
        _init_state()

    _validate_config()


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
