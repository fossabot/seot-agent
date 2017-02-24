import asyncio
from contextlib import suppress
from logging import getLogger

import docker

import msgpack

from . import BaseTransformer
from ..dpp import encode


logger = getLogger(__name__)


CONTAINER_PRIVATE_PORT = "11423/tcp"
HOST_LOOPBACK_ADDRESS = "127.0.0.1"


class DockerTransformer(BaseTransformer):
    def __init__(self, repo=None, tag="latest", cmd=None, **kwargs):
        super().__init__(**kwargs)
        self.repo = repo
        self.tag = tag
        self.cmd = cmd
        self.docker_client = docker.DockerClient()
        self.docker_api_client = docker.APIClient()

    async def startup(self):
        self._health_check()

        await self.loop.run_in_executor(None, self._pull_image)

        self._start_container()

        self._dump_logs_task = asyncio.ensure_future(
            self.loop.run_in_executor(None, self._dump_logs), loop=self.loop
        )

        await self._connect_to_container()

        self._read_task = asyncio.ensure_future(
            self._read_from_container(), loop=self.loop
        )

    async def cleanup(self):
        self._read_task.cancel()
        self._dump_logs_task.cancel()
        await asyncio.wait([self._read_task, self._dump_logs_task])

        logger.info("Stopping and removing docker container {0}".format(
            self.container.short_id))
        await self.loop.run_in_executor(None, self._stop_container)

        logger.info("Removing docker image {0}:{1}".format(
            self.repo, self.tag))
        await self.loop.run_in_executor(None, self._remove_image)

    async def _process(self, data):
        self.writer.write(encode(data))
        await self.writer.drain()

    def _health_check(self):
        ok = False
        try:
            ok = self.docker_client.ping()
        except:
            pass

        if not ok:
            raise RuntimeError("Failed to connect to docker server")

        ver_info = self.docker_client.version()
        logger.debug("Docker server version: {0}".format(ver_info["Version"]))
        logger.debug("Docker API version: {0}".format(ver_info["ApiVersion"]))

    def _pull_image(self):
        logger.info("Pulling docker image {0}:{1}".format(self.repo, self.tag))
        self.docker_client.images.pull(self.repo, tag=self.tag)
        logger.info("Pulled docker image")

    def _remove_image(self):
        with suppress(docker.errors.APIError):
            self.docker_client.images.remove(self.repo)

    def _start_container(self):
        logger.info("Launching docker container")
        self.container = self.docker_client.containers.run(
            self.repo,
            command=self.cmd,
            ports={CONTAINER_PRIVATE_PORT: (HOST_LOOPBACK_ADDRESS, None)},
            detach=True
        )
        logger.info("Launched docker container {0}".format(
            self.container.short_id))

    async def _connect_to_container(self):
        port_mapping = self.docker_api_client.port(
            self.container.id,
            private_port=CONTAINER_PRIVATE_PORT
        )
        host_port = port_mapping[0]["HostPort"]

        logger.debug("Connecting to port {0}/tcp of container {1}".format(
            host_port, self.container.short_id
        ))

        (self.reader, self.writer) = await asyncio.open_connection(
            host=HOST_LOOPBACK_ADDRESS,
            port=host_port,
            loop=self.loop
        )

    def _dump_logs(self):
        for line in self.container.logs(stdout=True, stderr=True, stream=True,
                                        follow=True):
            logger.info(line.decode("utf-8").strip())

    def _stop_container(self):
        with suppress(docker.errors.APIError):
            self.container.kill()

        self.docker_api_client.wait(self.container.id)
        self.container.remove()

    async def _read_from_container(self):
        unpacker = msgpack.Unpacker(encoding="utf-8")

        while True:
            buf = await self.reader.read(1024)
            # We have disconnected
            if not buf:
                break

            unpacker.feed(buf)
            for msg in unpacker:
                await self._emit(msg)
