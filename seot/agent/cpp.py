import asyncio
import logging
import time

from aiodns.error import DNSError
import aiohttp
from aiohttp.errors import ClientOSError, ClientTimeoutError

from . import config

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

                    logger.info("Response status code: {0}".format(status))
                    logger.info("Response body:\n{0}".format(body.strip()))
            except DNSError:
                logger.error("Could not resolve name")
            except ClientOSError as e:
                logger.error("Socket error: [{0}] {1}".format(
                    e.errno, e.strerror
                ))
            except (ClientTimeoutError, asyncio.TimeoutError):
                logger.error("Request timed out")
            except Exception as e:
                logger.error("Unexpected error: {0}".format(e))
                raise

    async def heartbeat(self):
        logger.info("Sending heartbeat to SEoT server...")

        await self._request("POST", "/heartbeat", data={
            "user_id": config.get("agent.user_id"),
            "agent_id": config.get_state("agent_id"),
            "agent_type": config.get("agent.type"),
            "longitude": config.get("agent.coordinate.longitude"),
            "latitude": config.get("agent.coordinate.latitude"),
            "dpp_listen_port": config.get("dpp.listen_port"),
            "timestamp": int(time.time())
        })

    async def _main(self):
        sleep_length = config.get("cpp.heartbeat_interval")

        while True:
            await self.heartbeat()
            await asyncio.sleep(sleep_length)

    def start(self, loop):
        self.task = asyncio.ensure_future(self._main(), loop=loop)

    def stop(self, loop):
        if not self.task.cancelled() and not self.task.done():
            self.task.set_result(None)
