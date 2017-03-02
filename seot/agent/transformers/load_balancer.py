from itertools import cycle
from logging import getLogger

from . import BaseTransformer
from .. import dpp


logger = getLogger(__name__)


class LoadBalancer(BaseTransformer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def startup(self):
        self._node_iterator = cycle(self.next_nodes())

    async def _process(self, data):
        node = next(self._node_iterator)

        logger.debug("Node {0} of type {1} emitted to node {2}:\n{3}".format(
            self.name,
            self.__class__.__name__,
            node.name,
            dpp.format(data))
        )

        await node.write(data)

    @classmethod
    def can_run(cls):
        return True
