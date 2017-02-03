import logging
import logging.config
from pathlib import Path

from . import config, meta

logger = logging.getLogger(__name__)


def log_startup_message():
    """ Print diagnostic messages """

    banner = """Launching...
     ____  _____    _____
    / ___|| ____|__|_   _|
    \___ \|  _| / _ \| |
     ___) | |__| (_) | |
    |____/|_____\___/|_|    Agent v{0}
    """.format(meta.__version__)
    logger.info(banner)
    logger.info("Agent ID: {0}".format(config.get_state("agent_id")))
    logger.info("Agent owner: {0}".format(config.get("agent.user_name")))
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
    log_ini = (Path(__file__) / "../conf/log.ini").resolve()
    logging.config.fileConfig(str(log_ini), disable_existing_loggers=False)
