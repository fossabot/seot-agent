import asyncio
import time

from .. import config
from ..node import Node
from ..sinks import BaseSink


class BaseSource(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._next_nodes = []

    def connect(self, node):
        if not isinstance(node, BaseSink):
            raise ValueError("Expected a sink")

        self._next_nodes.append(node)

        return node

    async def _emit(self, data):
        if "meta" not in data:
            data["meta"] = {
                "agent_id": config.get_state("agent_id"),
                "longitude": config.get("agent.coordinate.longitude"),
                "latitude": config.get("agent.coordinate.latitude"),
                "timestamp": time.time()
            }

        if not self._next_nodes:
            return
        await asyncio.wait([node.write(data) for node in self._next_nodes],
                           loop=self.loop)

    def next_nodes(self):
        return self._next_nodes
