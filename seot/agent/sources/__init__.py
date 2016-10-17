from abc import ABCMeta, abstractmethod


class BaseSource(metaclass=ABCMeta):
    @abstractmethod
    async def read(self):
        pass

    @abstractmethod
    async def prepare(self):
        pass

    @abstractmethod
    async def cleanup(self):
        pass
