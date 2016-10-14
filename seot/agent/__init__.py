import asyncio
import logging
import logging.config

from seot.agent import config
from seot.agent import dpp
from seot.agent import cpp
from seot.agent.util import configure_logging, log_startup_message
from transitions import Machine
import uvloop


__version__ = "0.0.1"

logger = logging.getLogger(__name__)


class Agent():
    states = ["init", "idle"]

    def __init__(self):
        self.machine = Machine(model=self, states=self.__class__.states,
                               initial="init")
        self.machine.add_transition(trigger="init", source="init", dest="idle")

        self.loop = asyncio.get_event_loop()
        self.cpp_server = cpp.CPPServer()
        self.dpp_server = dpp.DPPServer()

    def run(self):
        self.cpp_server.start(self.loop)
        self.dpp_server.start(self.loop)

        # Run main event loop
        logger.info("Starting main event loop...")
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()


def main():
    # Initialize logging
    configure_logging()

    # Load configs
    config.load()

    # Print startup message
    log_startup_message()

    # Use uvloop as event loop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    agent = Agent()
    agent.run()
