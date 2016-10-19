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


class BaseSink(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._queue = asyncio.Queue(loop=self.loop)

    async def write(self, data):
        await self._queue.put(data)

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            await self._process(input_data)
            self._queue.task_done()


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
        await asyncio.wait([node.write(data) for node in self._next_nodes],
                           loop=self.loop)

    def next_nodes(self):
        return self._next_nodes


class BaseTransformer(BaseSource, BaseSink):
    def __init(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            output_data = await self._process(input_data)
            await self._emit(output_data)
            self._queue.task_done()


class LambdaTransformer(BaseTransformer):
    def __init(self, func, **kwargs):
        super().__init__(**kwargs)
        self.func = func

    async def _process(self, data):
        return await self.func(data)


class ConstSource(BaseSource):
    def __init__(self, const, interval, **kwargs):
        super().__init__(**kwargs)
        self.const = const
        self.interval = interval

    async def _run(self):
        while True:
            await self._emit(self.const)
            await asyncio.sleep(self.interval)


class DebugSink(BaseSink):
    async def _process(self, data):
        print(data)


class IdentityTransformer(BaseTransformer):
    async def _process(self, data):
        return data


class DAG:
    def __init__(self, *args, loop=None):
        self.sources = []
        for source in args:
            if not isinstance(source, BaseSource):
                raise ValueError("Expected a source")
            self.sources.append(source)
        self.nodes = self._topological_sort(self.sources)

        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

    def _topological_sort(self, sources):
        visited = set([])
        result = deque([])

        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for next_node in node.next_nodes():
                visit(next_node)
            result.appendleft(node)

        for node in sources:
            visit(node)

        return list(result)

    def run(self):
        tasks = [node.start() for node in self.nodes]
        self.loop.run_until_complete(asyncio.wait(tasks))

    def stop(self):
        tasks = [node.stop() for node in self.nodes]
        with suppress(asyncio.CancelledError):
            self.loop.run_until_complete(asyncio.wait(tasks))

if __name__ == "__main__":
    sink = DebugSink(name="debug")
    source = ConstSource(123, 1, name="foo")
    source2 = ConstSource("hogeppi", 2, name="hoge")
    transformer = IdentityTransformer(name="identity")
    source.connect(transformer).connect(sink)
    source2.connect(transformer)

    loop = asyncio.get_event_loop()

    dag = DAG(source, source2)
    try:
        dag.run()
    except KeyboardInterrupt:
        dag.stop()

    loop.close()
