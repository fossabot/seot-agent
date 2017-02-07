import asyncio
import time

from .. import config
from ..dataflow import Node
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


class ConstSource(BaseSource):
    def __init__(self, const=None, interval=1, **kwargs):
        super().__init__(**kwargs)
        self.const = const
        self.interval = interval

    async def _run(self):
        while True:
            await self._emit(self.const)
            await asyncio.sleep(self.interval, loop=self.loop)


class NullSource(BaseSource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _run(self):
        pass
