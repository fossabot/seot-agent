from abc import ABCMeta, abstractmethod


class BaseSink(metaclass=ABCMeta):
    @abstractmethod
    async def write(self, data):
        pass
