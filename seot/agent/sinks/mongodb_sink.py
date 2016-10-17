import collections
import logging


import motor.motor_asyncio
from seot.agent.sinks import BaseSink

logger = logging.getLogger(__name__)


class MongoDBSink(BaseSink):
    def __init__(self, host="localhost", port=27017, database=None,
                 collection=None):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(host, port)

        if database is None:
            logger.error("database is a required configuration key")
        if collection is None:
            logger.error("collection is a required configuration key")

        self.collection = self.client[database][collection]

    def _decode(self, data):
        if isinstance(data, bytes):
            return data.decode("utf-8")
        elif isinstance(data, collections.Mapping):
            return dict(map(self._decode, data.items()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self._decode, data))
        else:
            return data

    async def write(self, data):
        await self.collection.insert(self._decode(data))
