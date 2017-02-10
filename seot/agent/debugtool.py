import asyncio
import sys
from logging import getLogger

import zmq.asyncio

from . import config
from .graph_builder import GraphBuilder
from .util import configure_logging

logger = getLogger(__name__)


def main():
    # Initialize logging
    configure_logging()

    # Load configs
    config.load()

    # Discover platform information
    config.discover_facts()

    loop = zmq.asyncio.install()

    graph = GraphBuilder.from_yaml(sys.argv[1])
    asyncio.ensure_future(graph.start(), loop=loop)

    # Run main event loop
    logger.info("Starting main event loop...")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        logger.info("Shutting down...")

        if graph.running():
            loop.run_until_complete(graph.stop())

    loop.close()


if __name__ == "__main__":
    main()
