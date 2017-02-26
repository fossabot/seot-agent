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

        self._running = False

    def running(self):
        return self._running

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
                pending.discard(node)
                permanent.add(node)

        for node in sources:
            walk(node)

        return list(result)

    async def start(self):
        """
        Start this dataflow graph.
        """
        if self.running():
            raise RuntimeError("Graph is already running")

        nodes = self._topological_sort(self.sources)

        # Call .startup() to initializate each node
        done, pending = await asyncio.wait(
            [node.startup() for node in nodes],
            loop=self.loop, return_when=FIRST_EXCEPTION
        )
        # Let's check if initialization was successful
        for future in done:
            try:
                future.result()
            except Exception as e:
                for f in pending:
                    f.cancel()

                logger.error("Graph failed to start: {0}".format(e))
                raise RuntimeError("Dataflow graph failed to start")

        async def run():
            self._running = True

            # Now we actually launch each node by calling .start()
            done, pending = await asyncio.wait(
                [node.start() for node in nodes],
                loop=self.loop, return_when=FIRST_EXCEPTION
            )

            # If we reach here, the dataflow graph has stopped
            self._running = False

            for future in done:
                try:
                    future.result()
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    for f in pending:
                        f.cancel()

                    logger.error("Graph crashed: {0}".format(e))
                    raise RuntimeError("Dataflow graph crashed")

        asyncio.ensure_future(run(), loop=self.loop)

    async def stop(self):
        """
        Stop this dataflow graph.
        """
        if not self.running():
            raise RuntimeError("Graph is not running")

        nodes = self._topological_sort(self.sources)

        # Request nodes to stop and wait until them to stop
        stop_tasks = [node.stop() for node in nodes if node.running()]
        if stop_tasks:
            with suppress(asyncio.CancelledError):
                await asyncio.wait(stop_tasks, loop=self.loop)

        # Do cleanup tasks
        cleanup_tasks = [node.cleanup() for node in nodes]
        await asyncio.wait(cleanup_tasks, loop=self.loop)
