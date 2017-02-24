from ..sinks import BaseSource


class NullSource(BaseSource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _run(self):
        pass

    @classmethod
    def can_run(cls):
        return True
