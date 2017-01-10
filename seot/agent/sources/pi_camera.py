import asyncio
import logging
from io import BytesIO

from picamera import PiCamera

from . import BaseSource

logger = logging.getLogger(__name__)


class PiCameraSource(BaseSource):
    def __init__(self, interval=10, width=640, height=480, fmt="jpeg",
                 **kwargs):
        super().__init__(**kwargs)
        self.interval = interval
        self.camera = PiCamera()
        self.camera.resolution = (width, height)
        self.fmt = fmt

    async def cleanup(self):
        self.camera.close()

    async def _run(self):
        while True:
            with BytesIO() as b:
                self.camera.capture(b, self.fmt)

                data = {
                    "image": b.getvalue()
                }
                await self._emit(data)

            await asyncio.sleep(self.interval, loop=self.loop)
