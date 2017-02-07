import asyncio
import json
import logging

from aiodns.error import DNSError

import aiohttp
from aiohttp.errors import ClientOSError, ClientTimeoutError

import zmq.asyncio

from . import config, meta
from .graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class Agent:
    BASE_URL = None

    def __init__(self):
        self.__class__.BASE_URL = config.get("cpp.base_url")
        self.loop = zmq.asyncio.install()
        # Job UUID -> Graph
        self.jobs = {}

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

                    if 400 <= resp.status:
                        logger.error(resp.reason)
                        logger.error(await resp.text())
                        return

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

    async def _get_job(self, job_id):
        logger.info("Getting job detail {0}".format(job_id))
        return await self._request("GET", "/job/" + job_id)

    async def _notify_job_start(self, job_id):
        logger.info("Starting job {0}".format(job_id))
        return await self._request("POST", "/job/{0}/accept".format(job_id))

    async def _notify_job_stop(self, job_id):
        logger.info("Stopped job {0}".format(job_id))
        return await self._request("POST", "/job/{0}/stop".format(job_id))

    async def _reject_job(self, job_id):
        logger.info("Rejecting job {0}".format(job_id))
        return await self._request("POST", "/job/{0}/reject".format(job_id))

    async def _heartbeat(self):
        logger.info("Sending heartbeat to SEoT server...")

        resp = await self._request("POST", "/heartbeat", data={
            "user_name": config.get("agent.user_name"),
            "agent_id": config.get_state("agent_id"),
            "longitude": config.get("agent.coordinate.longitude"),
            "latitude": config.get("agent.coordinate.latitude"),
            "nodes": [node["class"] for node in config.get("nodes")],
        })

        logger.info("Received response for heartbeat")

        if resp is None:
            return

        if "run" in resp and resp["run"]:
            job_id = resp["run"]
            logger.info("Got job offer for job {0}".format(job_id))

            if job_id in self.jobs:
                logger.warning("Already running job {0}".format(job_id))
                await self._reject_job(job_id)
                return

            job = await self._get_job(job_id)

            await self._notify_job_start(job_id)
            del job["application_id"]
            del job["job_id"]

            graph = GraphBuilder.from_obj(job)
            self.jobs[job_id] = graph

            await graph.start()

        elif "kill" in resp and resp["kill"]:
            job_id = resp["kill"]
            graph = self.jobs.get(job_id)
            if not graph:
                logger.warning("Unknown job {0}".format(job_id))
                return

            if graph.running():
                logger.info("Terminating job {0}".format(job_id))
                await graph.stop()

            await self._notify_job_stop(job_id)

            del self.jobs[job_id]

        else:
            logger.info("Nothing to do")

    async def _main(self):
        sleep_length = config.get("cpp.heartbeat_interval")

        while True:
            try:
                await self._heartbeat()
            except Exception as e:
                logger.error("Heartbeat failed: {0}".format(e))
            await asyncio.sleep(sleep_length)

    def stop(self):
        if not self.task.cancelled() and not self.task.done():
            self.task.set_result(None)

    def run(self):
        self.task = asyncio.ensure_future(self._main(), loop=self.loop)

        # Run main event loop
        logger.info("Starting main event loop...")
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            logger.info("Shutting down...")

            self.stop()

            for job_id, graph in self.jobs.items():
                if not graph.running():
                    continue

                logger.info("Terminating job {0}".format(job_id))
                self.loop.run_until_complete(graph.stop())

        self.loop.close()
