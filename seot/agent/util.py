import logging
import logging.config

from seot import agent
from seot.agent import config

logger = logging.getLogger(__name__)


def log_startup_message():
    """ Print diagnostic messages """

    banner = """Launching...
     ____  _____    _____
    / ___|| ____|__|_   _|
    \___ \|  _| / _ \| |
     ___) | |__| (_) | |
    |____/|_____\___/|_|    Agent v{0}
    """.format(agent.__version__)
    logger.info(banner)
    logger.info("Device ID: {0}".format(config.get_state("device_id")))
    logger.info("Device owner: {0}".format(
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


def log_quit_message():
    """ Print quit message """

    farewell = """
     ______
    < Bye! >
     ------
            \   ^__^
             \  (oo)\_______
                (__)\       )\/\\
                    ||----w |
                    ||     ||
        """
    logger.info(farewell)


def configure_logging():
    """ Configure logging and enable colorlog """
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
