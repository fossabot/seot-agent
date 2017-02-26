import logging

from . import BaseSink
from .. import dpp

logger = logging.getLogger(__name__)


class DebugSink(BaseSink):
    def __init__(self, level=logging.INFO, **kwargs):
        super().__init__(**kwargs)
        self.level = level

    async def _process(self, data):
        logger.log(self.level, "{0} received:\n{1}".format(
            self.name, dpp.format(data)))

    @classmethod
    def can_run(cls):
        return True
