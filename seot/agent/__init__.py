import logging

from . import config, meta
from .agent import Agent
from .util import configure_logging, log_startup_message
from .util import log_quit_message


__version__ = meta.__version__

logger = logging.getLogger(__name__)


def main():
    # Initialize logging
    configure_logging()

    # Load configs
    config.load()

    # Discover platform information
    config.discover_facts()

    # Print startup message
    log_startup_message()

    agent = Agent()
    agent.run()

    log_quit_message()
