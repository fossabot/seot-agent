import importlib
import json
import logging
from schema import Optional, Schema

from . import config
from .dataflow import Graph, Node

logger = logging.getLogger(__name__)

_REGISTERED_NODES = {}


class DPPServer:
    def __init__(self):
        self._load_node_classes()

        global _REGISTERED_NODES

        with open("tests/graph/const-debug-zmq.json") as f:
            data = json.load(f)

        schema = Schema({
            "nodes": [{
                "name": str,
                "type": str,
                Optional("args"): {str: object},
                Optional("to"): [str]
            }]
        })

        graph_def = schema.validate(data)

        nodes = {}
        sources = set([])
        for node_def in graph_def["nodes"]:
            cls_name = node_def["type"]
            if cls_name not in _REGISTERED_NODES:
                raise RuntimeError("Node {0} is not loaded".format(cls_name))

            cls = _REGISTERED_NODES[cls_name]
            args = node_def.get["args"]

            node = cls(**{"name": node_def["name"], **args})
            nodes[node_def["name"]] = node
            sources.add(node)

        for node_def in graph_def["nodes"]:
            for next_node in node_def["to"]:
                nodes[node_def["name"]].connect(nodes[next_node])
                sources.remove(nodes[next_node])

        self.dataflow = Graph(*sources)

    def start(self, loop):
        self.dataflow.start()

    def stop(self, loop):
        if not self.dataflow.running():
            return
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

        if loaded:
            logger.info("Loaded node {0} from {1}".format(cls_name, mod_name))
        else:
            logger.warning("Could not find class {0}".format(cls_name))
