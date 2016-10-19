import logging
import logging.config

from seot import agent
from . import config

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
    logger.info("Agent ID: {0}".format(config.get_state("agent_id")))
    logger.info("Agent owner: {0}".format(
        config.get("agent.user_id")
    ))
    logger.info("Agent type: {0}".format(config.get("agent.type")))
    logger.info("Agent coordinate: ({0}, {1})".format(
        config.get("agent.coordinate.longitude"),
        config.get("agent.coordinate.latitude")
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
