import importlib
import logging

from . import config
from .dataflow import Dataflow, Node

logger = logging.getLogger(__name__)

_REGISTERED_NODES = {}


graph_def = [
    {
        "name": "const",
        "type": "ConstSource",
        "args": {
            "const": {"foo": 123, "hoge": "hoi"},
            "interval": 1
        },
        "to": ["debug", "zmq"],
    },
    {
        "name": "debug",
        "type": "DebugSink",
        "to": []
    },
    {
        "name": "zmq",
        "type": "ZMQSink",
        "to": []
    }
]


class DPPServer:
    def __init__(self):
        self._load_node_classes()

        global graph_def, _REGISTERED_NODES

        nodes = {}
        sources = set([])
        for node_def in graph_def:
            cls = _REGISTERED_NODES[node_def["type"]]
            args = node_def.get("args", {})

            node = cls(**{"name": node_def["name"], **args})
            nodes[node_def["name"]] = node
            sources.add(node)

        for node_def in graph_def:
            if "to" not in node_def:
                continue
            for next_node in node_def["to"]:
                nodes[node_def["name"]].connect(nodes[next_node])
                sources.remove(nodes[next_node])

        self.dataflow = Dataflow(*sources)

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
        except ImportError:
            logger.warning("Could not load module {0}".format(mod_name))
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
