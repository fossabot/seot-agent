import logging
import os
from pathlib import Path

import aiofiles

from . import BaseSink

logger = logging.getLogger(__name__)


class FileSystemSink(BaseSink):
    def __init__(self, dest="/tmp/seot", prefix="seot", postfix="",
                 data_key="data", **kwargs):
        super().__init__(**kwargs)
        self.dest = Path(dest)
        self.prefix = prefix
        self.postfix = postfix
        self.data_key = data_key
        self.serial = 0

    async def startup(self):
        os.makedirs(str(self.dest), exist_ok=True)

    async def _process(self, msg):
        if self.data_key not in msg:
            return

        data = msg[self.data_key]

        if not isinstance(data, bytes):
            return

        path = self.dest / (self.prefix + str(self.serial) + self.postfix)
        self.serial += 1

        async with aiofiles.open(str(path), mode="wb") as f:
            await f.write(data)
