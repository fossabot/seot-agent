import asyncio
import logging
from abc import ABC, abstractmethod
from collections import deque
from contextlib import suppress

logger = logging.getLogger(__name__)


class Node(ABC):
    """
    Abstract base class of all dataflow nodes
    """
    def __init__(self, name=None, loop=None):
        """
        Initilize this node. Optional argument name specifies a human-readable
        name of this node. Use argument loop to specify the asyncio event loop
        on which this node is executed.
        """
        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self.name = name
        if self.name is None:
            self.name = self.__class__.__name__

        self._task = None

    @abstractmethod
    async def _run(self):
        """
        Coroutine performing the main task of this node. Must be overridden by
        subclasses.
        """
        pass

    def running(self):
        """
        Returns whether this node is running or not.
        """
        if self._task is None:
            return False
        return not self._task.done()

    def start(self):
        """
        Start this dataflow node.
        """
        if self.running():
            raise RuntimeError("Node is already running")

        logger.info("Starting " + self.__class__.__name__ + " " + self.name)

        self._task = asyncio.ensure_future(self._run(), loop=self.loop)

        return self._task

    def stop(self):
        """
        Stop this dataflow node.
        """
        if not self.running():
            raise RuntimeError("Node is not running")

        logger.info("Stopping " + self.__class__.__name__ + " " + self.name)

        self._task.cancel()

        return self._task

    @classmethod
    def all_subclasses(cls):
        return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                       for g in s.all_subclasses()]

    async def startup(self):
        """
        Perform initializations required before starting this node.
        """
        pass

    async def cleanup(self):
        """
        Perform cleanups required before starting this node.
        """
        pass

    def next_nodes(self):
        """
        Return a list of dataflow nodes connected to this node.
        """
        return []


class Graph:
    """
    A directed acyclic graph composed of dataflow nodes
    """
    def __init__(self, *args, loop=None):
        """
        Initialize this dataflow graph. Arguments specify the source nodes.
        Optionally, use argument loop to specify the asyncio event loop on
        which this node is executed.
        """
        self.sources = []
        if not args:
            raise ValueError("Expected at least one source node")

        for source in args:
            if not isinstance(source, Node):
                raise ValueError("Expected a Node")
            self.sources.append(source)

        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

    def _topological_sort(self, sources):
        """
        Return a list of dataflow nodes sorted in a topological order.
        """
        pending = set([])
        permanent = set([])
        result = deque([])

        def walk(node):
            if node in pending:
                raise RuntimeError("Dataflow graph contains cycle")
            elif node not in permanent:
                pending.add(node)
                for next_node in node.next_nodes():
                    walk(next_node)
                result.appendleft(node)
                permanent.add(node)

        for node in sources:
            walk(node)

        return list(result)

    def start(self):
        """
        Start this dataflow graph. This method returns immediately and the
        dataflow will be executed in a background task.
        """
        nodes = self._topological_sort(self.sources)

        async def start():
            await asyncio.wait([node.startup() for node in nodes],
                               loop=self.loop)
            await asyncio.wait([node.start() for node in nodes],
                               loop=self.loop)

        asyncio.ensure_future(start(), loop=self.loop)

    def stop(self):
        """
        Stop this dataflow graph. This method will block until the entire
        dataflow is stopped.
        """
        nodes = self._topological_sort(self.sources)

        # Request nodes to stop and wait until them top stop
        tasks = [node.stop() for node in nodes if node.running()]
        if tasks:
            with suppress(asyncio.CancelledError):
                self.loop.run_until_complete(asyncio.wait(tasks))

        # Do cleanup tasks
        tasks = [node.cleanup() for node in nodes]
        self.loop.run_until_complete(asyncio.wait(tasks))
