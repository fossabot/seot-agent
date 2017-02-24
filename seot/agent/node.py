import asyncio
import logging
from abc import ABC, abstractmethod

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

        logger.info("Starting node {0} of type {1}".format(
            self.name, self.__class__.__name__
        ))

        self._task = asyncio.ensure_future(self._run(), loop=self.loop)

        return self._task

    def stop(self):
        """
        Stop this dataflow node.
        """
        if not self.running():
            raise RuntimeError("Node is not running")

        logger.info("Stopping node {0} of type {1}".format(
            self.name, self.__class__.__name__
        ))

        self._task.cancel()

        return self._task

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

    @classmethod
    def can_run(cls):
        """
        Return if this node is runnable on the current platform
        """
        return False
