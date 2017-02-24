import asyncio
import logging

from sense_hat import SenseHat

from . import BaseSource

logger = logging.getLogger(__name__)


class SenseHatSource(BaseSource):
    def __init__(self, interval=5, **kwargs):
        super().__init__(**kwargs)
        self.interval = interval
        self.sense = SenseHat()

    async def _run(self):
        while True:
            data = {
                "temperature": self.sense.get_temperature(),
                "humidity": self.sense.get_humidity(),
                "pressure": self.sense.get_pressure()
            }
            await self._emit(data)

            await asyncio.sleep(self.interval, loop=self.loop)

    @classmethod
    def can_run(cls):
        return True
