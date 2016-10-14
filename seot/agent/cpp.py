import asyncio
import logging
import time

from aiodns.error import DNSError
import aiohttp
from aiohttp.errors import ClientOSError, ClientTimeoutError

from seot.agent import config

logger = logging.getLogger(__name__)


class CPPServer:
    BASE_URL = None

    def __init__(self):
        self.__class__.BASE_URL = config.get("cpp.base_url")

    async def _request(self, method, endpoint, data=None):
        url = self.__class__.BASE_URL + endpoint

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method=method, url=url, data=data,
                                           timeout=10) as resp:
                    status = resp.status
                    body = await resp.text()

                    logger.info(status)
                    logger.info(body)
            except DNSError:
                logger.error("Could not resolve name")
            except ClientOSError as e:
                logger.error("Socket error: [{0}] {1}".format(
                    e.errno, e.strerror
                ))
            except ClientTimeoutError:
                logger.error("Request timed out")
            except Exception as e:
                logger.error("Unexpected error: {0}".format(e))
                raise

    async def heartbeat(self):
        logger.info("Sending heartbeat to SEoT server...")

        await self._request("POST", "/heartbeat", data={
            "user_id": config.get("device.user_id"),
            "device_id": config.get_state("device_id"),
            "device_type": config.get("device.type"),
            "longitude": config.get("device.coordinate.longitude"),
            "latitude": config.get("device.coordinate.latitude"),
            "timestamp": time.time()
        })

    async def _main(self):
        sleep_length = config.get("cpp.heartbeat_interval")

        while True:
            await self.heartbeat()
            await asyncio.sleep(sleep_length)

    def start(self, loop):
        self.task = asyncio.ensure_future(self._main())

    def stop(self, loop):
        if not self.task.cancelled():
            self.task.set_result(None)
