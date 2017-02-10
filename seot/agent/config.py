import getpass
import logging
import platform
import shutil
import socket
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

from schema import Optional, Schema, SchemaError

import yaml

from . import meta

CONFIG_FILE_PATH = Path.home() / ".config/seot/config.yml"
STATE_FILE_PATH = Path.home() / ".local/share/seot/state.yml"

logger = logging.getLogger(__name__)
_config = {}
_state = {}

_CONFIG_SCHEMA = Schema({
    "agent": {
        "user_name": str,
        "coordinate": {
            "longitude": float,
            "latitude": float
        }
    },
    "cpp": {
        Optional("heartbeat_interval", default=60): int,
        Optional("base_url", default="http://localhost:8888/api"): str
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
    if not STATE_FILE_PATH.parent.exists():
        STATE_FILE_PATH.parent.mkdir(parents=True)

    logger.info("Generating agent UUID")
    _state["agent_id"] = str(uuid.uuid4())
    logger.info("Successfully generated agent UUID: {0}".format(
        _state.get("agent_id")
    ))
    _state["version"] = meta.__version__

    save_state()


def get_state(key=None):
    """ Get a state value """
    return _get(_state, key)


def _init_config():
    if not CONFIG_FILE_PATH.parent.exists():
        CONFIG_FILE_PATH.parent.mkdir(parents=True)

    src = (Path(__file__) / "../conf/config.yml.sample").resolve()
    dst = CONFIG_FILE_PATH.parent / "config.yml.sample"

    try:
        shutil.copyfile(str(src), str(dst))
    except OSError:
        logger.error("Failed to copy configuration file template; please"
                     " manually copy")
        sys.exit(1)

    logger.info("Please rename {0} to {1} and adjust configuration values"
                .format(str(dst), str(CONFIG_FILE_PATH)))
    sys.exit(1)


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
    else:
        _init_config()

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


def _discover_ip():
    url = urlparse(get("cpp.base_url"))
    host = url.hostname
    if url.port:
        port = url.port
    if url.scheme == "http":
        port = 80
    elif url.scheme == "https":
        port = 443

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        return s.getsockname()[0]


def discover_facts():
    """ Discover various platform information """
    kernel = platform.system()
    os_dist = "unknown"
    if kernel == "Darwin":
        os_dist = platform.mac_ver()[0]
    elif kernel == "Linux":
        os_dist = " ".join(platform.linux_distribution())

    _config["facts"] = {
        "agent_version": meta.__version__,
        "arch": platform.machine(),
        "processor": platform.processor(),
        "python": " ".join([
            platform.python_implementation(),
            platform.python_version()
        ]),
        "kernel": kernel,
        "os": os_dist,
        "user": getpass.getuser(),
        "ip": _discover_ip()
    }
