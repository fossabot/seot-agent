import logging

import asyncio
import zmq.asyncio

from . import config
from . import dpp
from . import cpp
from .util import configure_logging, log_startup_message
from .util import log_quit_message


__version__ = "0.0.1"

logger = logging.getLogger(__name__)


class Agent():
    states = ["idle"]

    def __init__(self):
        self.loop = zmq.asyncio.ZMQEventLoop()
        asyncio.set_event_loop(self.loop)
        self.cpp_server = cpp.CPPServer()
        self.dpp_server = dpp.DPPServer()

    def run(self):
        self.cpp_server.start(self.loop)
        self.dpp_server.start(self.loop)

        # Run main event loop
        logger.info("Starting main event loop...")
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            logger.info("Shutting down...")

            self.cpp_server.stop(self.loop)
            self.dpp_server.stop(self.loop)

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
