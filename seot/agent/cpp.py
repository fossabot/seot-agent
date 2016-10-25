import asyncio
import json
import logging

from aiodns.error import DNSError
import aiohttp
from aiohttp.errors import ClientOSError, ClientTimeoutError

from . import config, meta
from .graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class CPPServer:
    BASE_URL = None

    def __init__(self, loop=None):
        self.__class__.BASE_URL = config.get("cpp.base_url")
        self.loop = loop
        if loop is None:
            self.loop = asyncio.get_event_loop()

    async def _request(self, method, endpoint, data=None, content_type=None):
        url = self.__class__.BASE_URL + endpoint
        headers = {
            "User-Agent": "seot-agent {0}".format(meta.__version__)
        }

        if data is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data)

        async with aiohttp.ClientSession(loop=self.loop) as session:
            try:
                async with session.request(method=method, url=url, data=data,
                                           timeout=10,
                                           headers=headers) as resp:
                    return await resp.json()
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

    async def _get_job(self, job_id):
        logger.info("Getting job detail {0}".format(job_id))
        return await self._request("GET", "/job/" + job_id)

    async def _accept_job(self, job_id):
        logger.info("Accepting job {0}".format(job_id))
        return await self._request("POST", "/job/{0}/accept".format(job_id))

    async def _heartbeat(self):
        logger.info("Sending heartbeat to SEoT server...")

        resp = await self._request("POST", "/heartbeat", data={
            "user_id": config.get("agent.user_id"),
            "agent_id": config.get_state("agent_id"),
            "longitude": config.get("agent.coordinate.longitude"),
            "latitude": config.get("agent.coordinate.latitude"),
            "nodes": ["foo", "hoge", "piyo"],
            "busy": False
        })

        if resp is not None:
            if resp.get("job_offer", False):
                job_id = resp["job_id"]
                logger.info("Got job offer for job {0}".format(job_id))
                job = await self._get_job(job_id)

                await self._accept_job(job_id)
                del job["application_id"]
                del job["job_id"]

                GraphBuilder.from_obj(job)
                logger.info("Built graph from job definition")

    async def _main(self):
        sleep_length = config.get("cpp.heartbeat_interval")

        while True:
            await self._heartbeat()
            await asyncio.sleep(sleep_length)

    def start(self):
        self.task = asyncio.ensure_future(self._main(), loop=self.loop)

    def stop(self):
        if not self.task.cancelled() and not self.task.done():
            self.task.set_result(None)
