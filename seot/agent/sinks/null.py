from . import BaseSink


class NullSink(BaseSink):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _process(self, data):
        pass
