import importlib
import json
import logging
from schema import Optional, Schema
import yaml

from . import config
from .dataflow import Graph, Node

logger = logging.getLogger(__name__)


class GraphBuilder:
    _REGISTERED_NODES = None

    _GRAPH_DEF_SCHEMA = Schema({
        "nodes": [{
            "name": str,
            "type": str,
            Optional("args"): {str: object},
            Optional("to"): [str]
        }]
    })

    @classmethod
    def from_json(cls, filename, **kwargs):
        with open(filename) as f:
            return cls.from_obj(json.load(f), **kwargs)

    @classmethod
    def from_yaml(cls, filename, **kwargs):
        with open(filename) as f:
            return cls.from_obj(yaml.load(f), **kwargs)

    @classmethod
    def from_obj(cls, obj, **kwargs):
        if cls._REGISTERED_NODES is None:
            cls._load_node_classes()

        graph_def = cls._GRAPH_DEF_SCHEMA.validate(obj)

        nodes = {}
        for node_def in graph_def["nodes"]:
            cls_name = node_def["type"]
            if cls_name not in cls._REGISTERED_NODES:
                raise RuntimeError("Node {0} is not loaded".format(cls_name))

            node_cls = cls._REGISTERED_NODES[cls_name]
            node_args = node_def.get("args", {})
            node_args["name"] = node_def["name"]
            if "loop" in kwargs:
                node_args["loop"] = kwargs["loop"]

            nodes[node_def["name"]] = node_cls(**node_args)

        sources = set(nodes.values())
        for node_def in graph_def["nodes"]:
            if "to" not in node_def:
                continue

            for next_node in node_def["to"]:
                nodes[node_def["name"]].connect(nodes[next_node])
                sources.remove(nodes[next_node])

        return Graph(*sources, **kwargs)

    @classmethod
    def _load_node_classes(cls):
        cls._REGISTERED_NODES = {}

        for node in config.get("nodes"):
            node_cls = cls._try_load_node(node["module"], node["class"])

            if node_cls is None:
                continue

            cls._REGISTERED_NODES[node["class"]] = node_cls

    @classmethod
    def _try_load_node(cls, mod_name, cls_name):
        # First, import the module containing node
        try:
            importlib.import_module(mod_name)
        except ImportError as e:
            logger.warning("Failed to load module {0}: {1}".format(
                mod_name, e
            ))
            return None

        # Now class node should be visible as a subclass of Node
        for node_cls in Node.all_subclasses():
            if node_cls.__name__ == cls_name:
                logger.info("Loaded node {0} from {1}".format(
                    cls_name, mod_name
                ))
                return node_cls

        logger.warning("Could not find class {0}".format(cls_name))
        return None
