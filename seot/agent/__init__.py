import logging

from . import config, meta
from .agent import Agent
from .graph_builder import GraphBuilder
from .util import configure_logging, log_quit_message, log_startup_message
from .util import parse_cmd_args


__version__ = meta.__version__

logger = logging.getLogger(__name__)


def main():
    args = parse_cmd_args()

    # Initialize logging
    configure_logging(args.verbose)

    # Load configs
    config.load(args.config, args.state)

    # Discover platform information
    config.discover_facts()

    # Load available nodes
    GraphBuilder.load_node_classes()

    # Print startup message
    log_startup_message()

    agent = Agent()
    agent.run()

    log_quit_message()
