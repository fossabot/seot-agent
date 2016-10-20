import asyncio
import logging
from abc import ABC, abstractmethod
from collections import deque
from contextlib import suppress

logger = logging.getLogger(__name__)


class Node(ABC):
    def __init__(self, name=None, loop=None):
        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self.name = name
        if self.name is None:
            self.name = self.__class__.__name__

        self._task = None

    @abstractmethod
    async def _run(self):
        pass

    def running(self):
        if self._task is None:
            return False
        return not self._task.done()

    def start(self):
        if self.running():
            raise RuntimeError("Node is already running")

        logger.info("Starting " + self.__class__.__name__ + " " + self.name)

        self._task = asyncio.ensure_future(self._run(), loop=self.loop)

        return self._task

    def stop(self):
        if not self.running():
            raise RuntimeError("Node is not running")

        logger.info("Stopping " + self.__class__.__name__ + " " + self.name)

        self._task.cancel()

        return self._task

    async def startup(self):
        pass

    async def cleanup(self):
        pass

    def next_nodes(self):
        return []


class Dataflow:
    def __init__(self, *args, loop=None):
        self.sources = []
        for source in args:
            if not isinstance(source, Node):
                raise ValueError("Expected a Node")
            self.sources.append(source)

        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

    def _topological_sort(self, sources):
        pending = set([])
        permanent = set([])
        result = deque([])

        def visit(node):
            if node in pending:
                raise RuntimeError("Dataflow graph contains cycle")
            elif node not in permanent:
                pending.add(node)
                for next_node in node.next_nodes():
                    visit(next_node)
                result.appendleft(node)
                permanent.add(node)

        for node in sources:
            visit(node)

        return list(result)

    def start(self):
        nodes = self._topological_sort(self.sources)

        tasks = [node.startup() for node in nodes]
        self.loop.run_until_complete(asyncio.wait(tasks))

        tasks = [node.start() for node in nodes]
        self.loop.run_until_complete(asyncio.wait(tasks))

    def stop(self):
        nodes = self._topological_sort(self.sources)

        tasks = [node.stop() for node in nodes]
        with suppress(asyncio.CancelledError):
            self.loop.run_until_complete(asyncio.wait(tasks))

        tasks = [node.cleanup() for node in nodes]
        self.loop.run_until_complete(asyncio.wait(tasks))
