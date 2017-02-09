import asyncio
import shutil
import tempfile
from contextlib import suppress
from logging import getLogger
from pathlib import Path

import docker

import msgpack

from . import BaseTransformer


logger = getLogger(__name__)


class DockerTransformer(BaseTransformer):
    def __init__(self, repo=None, tag=None, cmd=None, **kwargs):
        super().__init__(**kwargs)
        self.repo = repo
        self.tag = tag
        self.cmd = cmd
        self.docker_client = docker.from_env()
        self.clients = {}

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
        self.unix_server.close()

        self._dump_logs_task.cancel()
        await asyncio.wait([self._dump_logs_task])

        logger.info("Stopping and removing docker container {0}".format(
            self.container.short_id))
        await self.loop.run_in_executor(None, self._stop_container)

        shutil.rmtree(str(self.tmp_dir_path))

        logger.info("Removing docker image {0}:{1}".format(
            self.repo, self.tag))
        await self.loop.run_in_executor(None, self._remove_image)

    async def _process(self, data):
        for (reader, writer) in self.clients.values():
            writer.write(msgpack.packb(data))
            await writer.drain()

    def _health_check(self):
        ok = False
        try:
            ok = self.docker_client.ping()
        except:
            pass

        if not ok:
            raise RuntimeError("Failed to connect to docker server")

        ver_info = self.docker_client.version()
        logger.info("Docker server version: {0}".format(ver_info["Version"]))
        logger.info("Docker API version: {0}".format(ver_info["ApiVersion"]))

    def _pull_image(self):
        self.docker_client.images.pull(self.repo, tag=self.tag)

    def _remove_image(self):
        with suppress(docker.errors.APIError):
            self.docker_client.images.remove(self.repo)

    def _start_container(self):
        self.container = self.docker_client.containers.run(
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
        if self.container.status in ["running", "created"]:
            self.container.kill()
        self.container.remove()

    async def _start_unix_server(self):
        self.tmp_dir_path = Path(tempfile.mkdtemp(prefix="seot-", dir="/tmp"))
        self.sock_path = self.tmp_dir_path / "seot.sock"

        self.unix_server = await asyncio.start_unix_server(
            self._accept_unix_client,
            path=str(self.sock_path),
            loop=self.loop
        )

    async def _accept_unix_client(self, reader, writer):
        logger.info("A docker client has connected")

        task = asyncio.ensure_future(self._handle_unix_client(reader, writer),
                                     loop=self.loop)
        self.clients[task] = (reader, writer)

        def client_done(task):
            logger.info("A docker client has disconnected")
            del self.clients[task]

        task.add_done_callback(client_done)

    async def _handle_unix_client(self, reader, writer):
        unpacker = msgpack.Unpacker(encoding="utf-8")

        while True:
            buf = await reader.read(1024)
            # Client has disconnected
            if not buf:
                break

            unpacker.feed(buf)
            for msg in unpacker:
                await self._emit(msg)
