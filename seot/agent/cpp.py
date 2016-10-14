import logging
import time

from aiodns.error import DNSError
import aiohttp
from aiohttp.errors import ClientOSError, ClientTimeoutError

from seot.agent import config

logger = logging.getLogger(__name__)

BASE_URL = None


async def _request(method, endpoint, data=None):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(method=method,
                                       url=BASE_URL + endpoint,
                                       data=data) as resp:
                status = resp.status
                body = await resp.text()

                logger.info(status)
                logger.info(body)
        except DNSError:
            logger.error("Could not resolve name")
        except ClientOSError as e:
            logger.error("Socket error: [{0}] {1}".format(e.errno, e.strerror))
        except ClientTimeoutError:
            logger.error("Request timed out")
        except Exception as e:
            logger.error("Unexpected error: {0}".format(e))
            raise


async def heartbeat():
    logger.info("Sending heartbeat...")

    await _request("POST", "/heartbeat", data={
        "user_id": config.get("device.user_id"),
        "device_type": config.get("device.type"),
        "longitude": config.get("device.coordinate.longitude"),
        "latitude": config.get("device.coordinate.latitude"),
        "timestamp": time.time()
    })


def init():
    """ Initialize cpp module """
    logger.info("Initializing CPP subsystem")

    global BASE_URL
    BASE_URL = config.get("cpp.base_url")

    logger.info("CPP subsystem successfully initialized")
