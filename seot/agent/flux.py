import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress


class Node(ABC):
    def __init__(self):
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

        self._task = asyncio.ensure_future(self._run())

        return self._task

    def stop(self):
        if not self.running():
            raise RuntimeError("Node is not running")

        self._task.cancel()

        return self._task

    async def startup(self):
        pass

    async def cleanup(self):
        pass


class BaseSink(Node):
    def __init__(self):
        super().__init__()
        self._queue = asyncio.Queue()

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
    def __init__(self):
        super().__init__()
        self._outputs = []

    def connect(self, node):
        if not isinstance(node, BaseSink):
            raise ValueError("Expected a sink")

        self._outputs.append(node)

        return node

    async def _emit(self, data):
        await asyncio.wait([node.write(data) for node in self._outputs])

    def start(self):
        # Start myself
        super().start()

        # Start connected nodes
        for node in self._outputs:
            if node.running():
                continue
            node.start()

    def stop(self):
        # Stop myself
        pending = [super().stop()]

        # Stop connected nodes
        for node in self._outputs:
            if node.running():
                continue
            pending.append(node.stop())

        return asyncio.ensure_future(asyncio.wait(pending))


class BaseTransformer(BaseSource, BaseSink):
    def __init(self):
        super().__init__()

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            output_data = await self._process(input_data)
            await self._emit(output_data)
            self._queue.task_done()


class ConstSource(BaseSource):
    def __init__(self, const, interval):
        super().__init__()
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


if __name__ == "__main__":
    sink = DebugSink()
    source = ConstSource(123, 1)
    source2 = ConstSource("hogeppi", 2)
    transformer = IdentityTransformer()
    source.connect(transformer).connect(sink)
    source2.connect(transformer)

    loop = asyncio.get_event_loop()
    try:
        source.start()
        source2.start()
        loop.run_forever()
    except KeyboardInterrupt:
        t1 = source.stop()
        t2 = source2.stop()
        with suppress(asyncio.CancelledError):
            loop.run_until_complete(asyncio.wait([t1, t2]))

    loop.close()
