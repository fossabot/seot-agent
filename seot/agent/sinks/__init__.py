from abc import ABCMeta, abstractmethod


class BaseSink(metaclass=ABCMeta):
    @abstractmethod
    async def write(self, data):
        pass

    @abstractmethod
    async def prepare(self):
        pass

    @abstractmethod
    async def cleanup(self):
        pass
