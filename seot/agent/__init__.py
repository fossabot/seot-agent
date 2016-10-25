import logging

import zmq.asyncio

from . import config, cpp, meta
from .graph_builder import GraphBuilder
from .util import configure_logging, log_startup_message
from .util import log_quit_message


__version__ = meta.__version__

logger = logging.getLogger(__name__)


class Agent():
    def __init__(self):
        self.loop = zmq.asyncio.install()

        self.cpp_server = cpp.CPPServer(self.loop)

        json_path = "tests/graph/const-debug-zmq.json"
        self.graph = GraphBuilder.from_json(json_path, loop=self.loop)

    def run(self):
        self.cpp_server.start()
        self.graph.start()

        # Run main event loop
        logger.info("Starting main event loop...")
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            logger.info("Shutting down...")

            self.cpp_server.stop()

            if self.graph.running():
                self.graph.stop()

        self.loop.close()
        log_quit_message()


def main():
    # Initialize logging
    configure_logging()

    # Load configs
    config.load()

    # Discover platform information
    config.discover_fact()

    # Print startup message
    log_startup_message()

    agent = Agent()
    agent.run()
