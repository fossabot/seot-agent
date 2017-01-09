import asyncio
from logging import getLogger

import docker

from . import BaseTransformer

logger = getLogger(__name__)


class DockerTransformer(BaseTransformer):
    def __init__(self, repo=None, tag=None, cmd=None, **kwargs):
        super().__init__(**kwargs)
        self.repo = repo
        self.tag = tag
        self.cmd = cmd
        self.client = docker.from_env()

    async def startup(self):
        self._health_check()

        logger.info("Pulling docker image {0}:{1}".format(self.repo, self.tag))
        await self.loop.run_in_executor(None, self._pull_image)
        logger.info("Pulled docker image")

        logger.info("Launching docker container")
        self._start_container()
        logger.info("Launched docker container {0}".format(
            self.container.short_id))

        self._dump_logs_task = asyncio.ensure_future(
            self.loop.run_in_executor(None, self._dump_logs), loop=self.loop
        )

    async def cleanup(self):
        if self.container and self.container.status == "running":
            logger.info("Stopping docker container {0}".format(
                self.container.short_id))
            await self.loop.run_in_executor(None, self._stop_container)

        logger.info("Removing docker image {0}:{1}".format(
            self.repo, self.tag))
        await self.loop.run_in_executor(None, self._remove_image)

    async def _process(self, data):
        return data

    def _health_check(self):
        if not self.client.ping():
            raise RuntimeError("Failed to connect to docker server")

        ver_info = self.client.version()
        logger.info("Docker server version: {0}".format(ver_info["Version"]))
        logger.info("Docker API version: {0}".format(ver_info["ApiVersion"]))

    def _pull_image(self):
        self.client.images.pull(self.repo, tag=self.tag)

    def _remove_image(self):
        self.client.images.remove(self.repo)

    def _start_container(self):
        self.container = self.client.containers.run(self.repo,
                                                    command=self.cmd,
                                                    detach=True)

    def _dump_logs(self):
        for line in self.container.logs(stdout=True, stderr=True, stream=True,
                                        follow=True):
            logger.info(line)

    def _stop_container(self):
        self.container.stop()
