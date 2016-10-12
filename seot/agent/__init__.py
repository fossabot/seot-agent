import asyncio
import logging


import colorlog
from seot.agent import config
import uvloop


__version__ = "0.0.1"

logger = logging.getLogger("core")
logger.setLevel(logging.INFO)


def print_startup_message():
    logger.info("Launching SEoT Agent version {0}".format(__version__))
    logger.info("Owner of this device: {0}".format(config.get("user_id")))
    logger.info("Device type: {0}".format(config.get("type")))
    logger.info("Device coordinate: ({0}, {1})".format(
        config.get("coordinate.longitude"),
        config.get("coordinate.latitude")
    ))
    logger.info("Heartbeat interval: {0}s".format(
        config.get("heartbeat_interval"))
    )


def main():
    # Init colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s[%(levelname)s] %(fg_white)s[%(name)s]: %(message)s"))
    colorlog.getLogger("").addHandler(handler)

    # Init uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    config.init()

    print_startup_message()
