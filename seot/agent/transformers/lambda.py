from . import SimpleTransformer


class LambdaTransformer(SimpleTransformer):
    def __init__(self, func=None, **kwargs):
        super().__init__(**kwargs)
        self.func = func

    async def _process(self, data):
        return await self.func(data)
