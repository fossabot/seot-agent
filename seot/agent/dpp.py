import logging

from .dataflow import Dataflow
from .sinks import DebugSink
from .sinks.mongodb_sink import MongoDBSink
from .sources.zmq_source import ZMQSource

logger = logging.getLogger(__name__)


class DPPServer:
    def __init__(self):
        src = ZMQSource("tcp://127.0.0.1:51423")
        src.connect(DebugSink())
        src.connect(MongoDBSink(database="seot", collection="test"))

        self.dataflow = Dataflow(src)

    def start(self, loop):
        self.dataflow.start()

    def stop(self, loop):
        self.dataflow.stop()
