import asyncio
import logging

import aiohttp
import colorlog
from seot.agent import config
from seot.agent import dpp
import uvloop


__version__ = "0.0.1"

logger = logging.getLogger("core")
logger.setLevel(logging.INFO)


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


async def send_heartbeat():
    print("Sending heartbeat...")
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.github.com/events") as resp:
            print(resp.status)
            print(await resp.text())


async def main_loop():
    while True:
        await asyncio.sleep(config.get("cpp.heartbeat_interval"))
        await send_heartbeat()


def main():
    # Enable colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s[%(levelname)s] %(fg_white)s[%(name)s]: %(message)s"))
    colorlog.getLogger("").addHandler(handler)

    # Use uvloop as event loop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # Initalize config component
    config.init()

    # Print diagnostic messages
    print_startup_message()

    # Initialize dpp component
    dpp.init()

    # Run main event loop
    logger.info("Launching main event loop...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_loop())
