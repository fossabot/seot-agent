import asyncio


import colorlog
from seot.agent import config
import uvloop


def main():
    # Init colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s[%(levelname)s] %(fg_white)s[%(name)s]: %(message)s"))
    colorlog.getLogger("").addHandler(handler)

    # Init uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    config.init()
    print(config.get(""))
