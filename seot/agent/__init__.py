import asyncio
import logging
import logging.config

from seot.agent import config
from seot.agent import dpp
from seot.agent import cpp
import uvloop


__version__ = "0.0.1"

logger = logging.getLogger(__name__)


def print_startup_message():
    logger.info("This is SEoT Agent version {0}".format(__version__))
    logger.info("Device ID: {0}".format(config.get_state("device_id")))
    logger.info("Owner of this device: {0}".format(
        config.get("device.user_id")
    ))
    logger.info("Device type: {0}".format(config.get("device.type")))
    logger.info("Device coordinate: ({0}, {1})".format(
        config.get("device.coordinate.longitude"),
        config.get("device.coordinate.latitude")
    ))
    logger.info("Heartbeat interval: {0}s".format(
        config.get("cpp.heartbeat_interval"))
    )


async def main_loop():
    while True:
        await asyncio.sleep(config.get("cpp.heartbeat_interval"))
        await cpp.heartbeat()


def main():
    # Configure logging and enable colorlog
    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s[%(levelname)s] "
                          + "%(fg_white)s[%(name)s]: %(message)s"
            },
        },
        "handlers": {
            "default": {
                "class": "colorlog.StreamHandler",
                "level": "INFO",
                "formatter": "colored"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
        "disable_existing_loggers": False,
    })

    # Use uvloop as event loop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # Initalize config component
    config.init()

    # Print diagnostic messages
    print_startup_message()

    # Initialize dpp component
    dpp.init()

    # Initialize cpp component
    cpp.init()

    # Run main event loop
    logger.info("Launching main event loop...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_loop())
