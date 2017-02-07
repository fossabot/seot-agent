import asyncio
import collections
import json
import logging
from abc import abstractmethod

from pygments import formatters, highlight, lexers

from ..dataflow import Node

logger = logging.getLogger(__name__)


class BaseSink(Node):
    def __init__(self, qsize=0, **kwargs):
        super().__init__(**kwargs)
        self._queue = asyncio.Queue(maxsize=qsize, loop=self.loop)

    async def write(self, data):
        await self._queue.put(data)

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            await self._process(input_data)


class DebugSink(BaseSink):
    def __init__(self, level=logging.INFO, **kwargs):
        super().__init__(**kwargs)
        self.level = level

    def _sanitize(self, data):
        if isinstance(data, str):
            return data
        if isinstance(data, bytes):
            return "<binary data ({0} bytes)>".format(len(data))
        elif isinstance(data, collections.Mapping):
            return dict(map(self._sanitize, data.items()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self._sanitize, data))
        else:
            return data

    async def _process(self, data):
        formatted_json = json.dumps(self._sanitize(data), indent=4)
        colorful_json = highlight(formatted_json, lexers.JsonLexer(),
                                  formatters.TerminalFormatter())
        logger.log(self.level, "{0} received:\n{1}".format(
            self.name, colorful_json.strip()))


class NullSink(BaseSink):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _process(self, data):
        pass
