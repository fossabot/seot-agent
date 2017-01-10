import asyncio
import shutil
import tempfile
from contextlib import suppress
from logging import getLogger
from pathlib import Path

import docker

from . import BaseTransformer
from .. import dpp


logger = getLogger(__name__)


class DockerTransformer(BaseTransformer):
    def __init__(self, repo=None, tag=None, cmd=None, **kwargs):
        super().__init__(**kwargs)
        self.repo = repo
        self.tag = tag
        self.cmd = cmd
        self.client = docker.from_env()
        self.send_queue = asyncio.Queue()
        self.recv_queue = asyncio.Queue()

    async def startup(self):
        self._health_check()

        await self._start_unix_server()

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
        self._dump_logs_task.cancel()
        await asyncio.wait([self._dump_logs_task])

        logger.info("Removing docker container {0}".format(
            self.container.short_id))
        await self.loop.run_in_executor(None, self._stop_container)

        shutil.rmtree(str(self.tmp_dir_path))

        logger.info("Removing docker image {0}:{1}".format(
            self.repo, self.tag))
        await self.loop.run_in_executor(None, self._remove_image)

    async def _process(self, data):
        await self.send_queue.put(data)
        return await self.recv_queue.get()

    def _health_check(self):
        if not self.client.ping():
            raise RuntimeError("Failed to connect to docker server")

        ver_info = self.client.version()
        logger.info("Docker server version: {0}".format(ver_info["Version"]))
        logger.info("Docker API version: {0}".format(ver_info["ApiVersion"]))

    def _pull_image(self):
        self.client.images.pull(self.repo, tag=self.tag)

    def _remove_image(self):
        with suppress(docker.errors.APIError):
            self.client.images.remove(self.repo)

    def _start_container(self):
        self.container = self.client.containers.run(
            self.repo,
            command=self.cmd,
            volumes={
                str(self.sock_path): {"bind": "/tmp/seot.sock", "mode": "rw"}
            },
            detach=True
        )

    def _dump_logs(self):
        for line in self.container.logs(stdout=True, stderr=True, stream=True,
                                        follow=True):
            logger.info(line.decode("utf-8").strip())

    def _stop_container(self):
        if self.container.status == "running":
            self.container.stop()
        self.container.remove()

    async def _start_unix_server(self):
        self.tmp_dir_path = Path(tempfile.mkdtemp(prefix="seot-", dir="/tmp"))
        self.sock_path = self.tmp_dir_path / "seot.sock"

        await asyncio.start_unix_server(self._handle_client,
                                        path=str(self.sock_path),
                                        loop=self.loop)

    async def _handle_client(self, reader, writer):
        logger.info("Client has connected")

        while True:
            data = await self.send_queue.get()

            writer.write(dpp.encode(data))
            resp = await reader.read(1024)

            if not resp:
                break

            await self.recv_queue.put(dpp.decode(resp))
