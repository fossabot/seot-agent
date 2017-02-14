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
    logger.info("Agent heartbeat interval: {0}s".format(
        config.get("cpp.heartbeat_interval"))
    )
    logger.info("Machine hostname: {0}".format(config.get("facts.hostname")))
    logger.info("Machine OS: {0} {1} ({2})".format(
        config.get("facts.kernel"),
        config.get("facts.os"),
        config.get("facts.arch")
    ))
    logger.info("Machine IP: {0}".format(config.get("facts.ip")))


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
