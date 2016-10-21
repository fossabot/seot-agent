import copy
import logging


import motor.motor_asyncio
from pymongo.errors import ConnectionFailure

from . import BaseSink

logger = logging.getLogger(__name__)


class MongoDBSink(BaseSink):
    def __init__(self, host="localhost", port=27017, database=None,
                 collection=None, **kwargs):
        super().__init__(**kwargs)
        self.client = motor.motor_asyncio.AsyncIOMotorClient(host, port)

        if database is None:
            logger.error("database is a required configuration key")
        if collection is None:
            logger.error("collection is a required configuration key")

        self.collection = self.client[database][collection]

    async def _process(self, data):
        try:
            # Need deepcopy here because db.collection.insert() modifies
            # the object being inserted
            await self.collection.insert(copy.deepcopy(data))
        except ConnectionFailure as e:
            logger.error("Connection error: {0}".format(e))

    async def startup(self):
        logger.info("Trying to connect to MongoDB...")
        successful = False
        try:
            successful = await self.client.admin.command("ping")
        except ConnectionFailure as e:
            logger.error("Connection error: {0}".format(e))
            successful = False

        if successful:
            logger.info("Connected to MongoDB at {0}:{1}".format(
                self.client.host, self.client.port
            ))
        else:
            logger.error("Failed to connect to MongoDB")

    async def cleanup(self):
        logger.info("Disconnecting from MongoDB")
        self.client.close()
