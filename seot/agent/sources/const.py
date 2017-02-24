import asyncio

from . import BaseSource


class ConstSource(BaseSource):
    def __init__(self, const=None, interval=1, **kwargs):
        super().__init__(**kwargs)
        self.const = const
        self.interval = interval

    async def _run(self):
        while True:
            await self._emit(self.const)
            await asyncio.sleep(self.interval, loop=self.loop)
