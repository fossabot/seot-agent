import collections
import json
import logging

from pygments import formatters, highlight, lexers

from . import BaseSink

logger = logging.getLogger(__name__)


class DebugSink(BaseSink):
    def __init__(self, level=logging.INFO, **kwargs):
        super().__init__(**kwargs)
        self.level = level

    def _sanitize(self, data):
        if isinstance(data, str):
            return data
        if isinstance(data, bytes):
            return "<binary data ({0} bytes)>".format(len(data))
        elif isinstance(data, collections.Mapping):
            return dict(map(self._sanitize, data.items()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self._sanitize, data))
        else:
            return data

    async def _process(self, data):
        formatted_json = json.dumps(self._sanitize(data), indent=4)
        colorful_json = highlight(formatted_json, lexers.JsonLexer(),
                                  formatters.TerminalFormatter())
        logger.log(self.level, "{0} received:\n{1}".format(
            self.name, colorful_json.strip()))

    @classmethod
    def can_run(cls):
        return True
