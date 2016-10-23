from abc import abstractmethod

from ..sinks import BaseSink
from ..sources import BaseSource


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


class IdentityTransformer(BaseTransformer):
    async def _process(self, data):
        return data


class LambdaTransformer(BaseTransformer):
    def __init(self, func=None, **kwargs):
        super().__init__(**kwargs)
        self.func = func

    async def _process(self, data):
        return await self.func(data)
