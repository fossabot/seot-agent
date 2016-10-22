import importlib
import logging

from . import config
from .dataflow import Graph, Node

logger = logging.getLogger(__name__)

_REGISTERED_NODES = {}


# graph_def = [
#     {
#         "name": "const",
#         "type": "ConstSource",
#         "args": {
#             "const": {"foo": 123, "hoge": "hoi"},
#             "interval": 1
#         },
#         "to": ["debug", "zmq"],
#     },
#     {
#         "name": "debug",
#         "type": "DebugSink",
#     },
#     {
#         "name": "zmq",
#         "type": "ZMQSink",
#     }
# ]

graph_def = [
   {
       "name": "zmq",
       "type": "ZMQSource",
       "to": ["debug", "mongodb"],
   },
   {
       "name": "debug",
       "type": "DebugSink",
   },
   {
       "name": "mongodb",
       "type": "MongoDBSink",
       "args": {
           "database": "seot",
           "collection": "test"
        }
   }
]


class DPPServer:
    def __init__(self):
        self._load_node_classes()

        global graph_def, _REGISTERED_NODES

        nodes = {}
        sources = set([])
        for node_def in graph_def:
            cls_name = node_def["type"]
            if cls_name not in _REGISTERED_NODES:
                raise RuntimeError("Node {0} is not loaded".format(cls_name))

            cls = _REGISTERED_NODES[cls_name]
            args = node_def.get("args", {})

            node = cls(**{"name": node_def["name"], **args})
            nodes[node_def["name"]] = node
            sources.add(node)

        for node_def in graph_def:
            for next_node in node_def.get("to", []):
                nodes[node_def["name"]].connect(nodes[next_node])
                sources.remove(nodes[next_node])

        self.dataflow = Graph(*sources)

    def start(self, loop):
        self.dataflow.start()

    def stop(self, loop):
        self.dataflow.stop()

    def _load_node_classes(self):
        global _REGISTERED_NODES

        for node in config.get("nodes"):
            if "module" not in node or "class" not in node:
                continue
            self._try_load_node(node["module"], node["class"])

    def _try_load_node(self, mod_name, cls_name):
        # First, import the module containing node
        try:
            importlib.import_module(mod_name)
        except ImportError as e:
            logger.warning("Failed to load module {0}: {1}".format(
                mod_name, e
            ))
            return

        # Now class node should be visible as a subclass of Node
        loaded = False
        for cls in Node.all_subclasses():
            if cls.__name__ == cls_name:
                _REGISTERED_NODES[cls_name] = cls
                loaded = True
                break

        if not loaded:
            logger.warning("Could not load class {0}".format(cls_name))
