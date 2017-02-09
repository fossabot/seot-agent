from abc import abstractmethod

from ..sinks import BaseSink
from ..sources import BaseSource


class BaseTransformer(BaseSource, BaseSink):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SimpleTransformer(BaseTransformer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    async def _process(self, data):
        pass

    async def _run(self):
        while True:
            input_data = await self._queue.get()
            output_data = await self._process(input_data)

            if output_data is not None:
                await self._emit(output_data)


class IdentityTransformer(SimpleTransformer):
    async def _process(self, data):
        return data


class LambdaTransformer(SimpleTransformer):
    def __init__(self, func=None, **kwargs):
        super().__init__(**kwargs)
        self.func = func

    async def _process(self, data):
        return await self.func(data)
