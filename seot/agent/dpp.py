import logging

from .dataflow import DAG
from .sinks import DebugSink
from .sinks.mongodb_sink import MongoDBSink
from .sources.remote_source import RemoteSource

logger = logging.getLogger(__name__)


class DPPServer:
    def __init__(self):
        src = RemoteSource()
        src.connect(DebugSink())
        src.connect(MongoDBSink(database="seot", collection="test"))

        self.dag = DAG(src)

    def start(self, loop):
        self.dag.run()

    def stop(self, loop):
        self.dag.stop()
