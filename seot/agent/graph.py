import asyncio
import logging
from collections import deque
from concurrent.futures import FIRST_EXCEPTION
from contextlib import suppress

from .node import Node

logger = logging.getLogger(__name__)


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

        self._task = None

    def nodes(self):
        """
        Returns a list of all dataflow nodes
        """
        return self._topological_sort(self.sources)

    def running(self):
        """
        Returns whether this dataflow graph is running or not.
        """
        return any([node.running() for node in self.nodes()])

    def _topological_sort(self, sources):
        """
        Return a list of dataflow nodes sorted in a topological order.
        """
        pending = set([])
        permanent = set([])
        result = deque([])

        def _walk(node):
            if node in pending:
                raise RuntimeError("Dataflow graph contains cycle")
            elif node not in permanent:
                pending.add(node)
                for next_node in node.next_nodes():
                    _walk(next_node)
                result.appendleft(node)
                pending.discard(node)
                permanent.add(node)

        for node in sources:
            _walk(node)

        return list(result)

    async def start(self, done_cb=None):
        """
        Start this dataflow graph.
        """
        if self.running():
            logger.error("Graph is already running")

        async def _run():
            # Now we actually launch each node by calling .start()
            done, pending = await asyncio.wait(
                [node.start() for node in self.nodes()],
                loop=self.loop, return_when=FIRST_EXCEPTION
            )

            # If we reach here, the dataflow graph has stopped for some reason
            for future in done:
                # Let's find out why...
                try:
                    future.result()
                # We ignore this error, because it is most likely caused by
                # graph.stop()
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    # Cancel unfinished tasks to avoid warnings
                    for f in pending:
                        f.cancel()

                    logger.error("Graph crashed: {0}".format(e))

            if done_cb:
                await done_cb(self)

        self._task = asyncio.ensure_future(_run(), loop=self.loop)

    async def stop(self):
        """
        Stop this dataflow graph.
        """
        if not self.running():
            logger.error("Graph is not running")

        running_nodes = [node for node in self.nodes() if node.running()]
        if not running_nodes:
            return

        # Request nodes to stop and wait until them to actually stop
        with suppress(asyncio.CancelledError):
            await asyncio.wait([node.stop() for node in self.nodes()],
                               loop=self.loop)

        # Now all nodes have stopped, but we need to wait until done_cb
        # finishes
        await asyncio.wait([self._task], loop=self.loop)

    async def startup(self):
        """
        Perform initializations required before starting this graph.
        """
        # Call node.startup() to initializate each node
        done, pending = await asyncio.wait(
            [node.startup() for node in self.nodes()],
            loop=self.loop, return_when=FIRST_EXCEPTION
        )

        # Let's check if nodes were successfully initialized
        for future in done:
            try:
                future.result()
            except Exception as e:
                # Cancel unfinished initializations
                for f in pending:
                    f.cancel()

                logger.error("Failed to initialize a node: {0}".format(e))
                raise RuntimeError("Dataflow graph failed to start")

    async def cleanup(self):
        """
        Perform cleanups required before starting this graph.
        """
        # Call node.cleanup() to initializate each node
        done, pending = await asyncio.wait(
            [node.cleanup() for node in self.nodes()],
            loop=self.loop
        )

        for future in done:
            try:
                future.result()
            except Exception as e:
                logger.warning("Failed to cleanup a node: {0}".format(e))
