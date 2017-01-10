import asyncio
import logging
import random

from . import BaseSource

logger = logging.getLogger(__name__)


class StubSenseHatSource(BaseSource):
    def __init__(self, interval=5, **kwargs):
        super().__init__(**kwargs)
        self.interval = interval

        # These synthetic values are generated based on Wiener process
        self.temperature = 25.0
        self.humidity = 50.0
        self.pressure = 1013.0

    async def _run(self):
        while True:
            sigma = self.interval / 100.0

            self.temperature = random.gauss(self.temperature, sigma)
            self.humidity = random.gauss(self.humidity, sigma)
            self.pressure = random.gauss(self.pressure, sigma)

            data = {
                "temperature": self.temperature,
                "humidity": self.humidity,
                "pressure": self.pressure
            }
            await self._emit(data)

            await asyncio.sleep(self.interval, loop=self.loop)
