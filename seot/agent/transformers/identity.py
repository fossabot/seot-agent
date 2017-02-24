from . import SimpleTransformer


class IdentityTransformer(SimpleTransformer):
    async def _process(self, data):
        return data

    @classmethod
    def can_run(cls):
        return True
