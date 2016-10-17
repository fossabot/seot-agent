from abc import ABCMeta, abstractmethod


class BaseSource(metaclass=ABCMeta):
    @abstractmethod
    async def read(self):
        pass

    async def prepare(self):
        pass

    async def cleanup(self):
        pass
