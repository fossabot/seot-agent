import json
from importlib import import_module
from inspect import getmembers, isclass
from logging import getLogger
from pkgutil import walk_packages

from schema import Optional, Schema

import seot.agent

import yaml

from .dataflow import Graph, Node

logger = getLogger(__name__)


class GraphBuilder:
    _REGISTERED_NODES = None

    _GRAPH_DEF_SCHEMA = Schema({
        "nodes": [{
            "name": str,
            "type": str,
            Optional("args"): {Optional(str): object},
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
                raise RuntimeError("Node type {0} is not loaded".format(
                    cls_name
                ))

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
                if next_node not in nodes:
                    logger.warning("Ignoring unknown destionation node {0}"
                                   .format(next_node))
                    continue

                nodes[node_def["name"]].connect(nodes[next_node])
                sources.discard(nodes[next_node])

        return Graph(*sources, **kwargs)

    @classmethod
    def _load_node_classes(cls):
        cls._REGISTERED_NODES = {}

        root_pkg = seot.agent
        pkgs = walk_packages(root_pkg.__path__, root_pkg.__name__ + ".")

        # Walk over all submodules of seot.agent
        for importer, mod_name, is_pkg in pkgs:
            try:
                mod = import_module(mod_name)
            except ImportError:
                continue

            def is_node(node_cls):
                # check if c is a subclass of Node
                if isclass(node_cls) and issubclass(node_cls, Node):
                    # check if c can run on this platform
                    if node_cls != Node and node_cls.can_run():
                        return True

                return False

            for cls_name, node_cls in getmembers(mod, is_node):
                logger.debug("Loaded node type {0} from module {1}".format(
                    cls_name, mod_name
                ))
                cls._REGISTERED_NODES[cls_name] = node_cls
