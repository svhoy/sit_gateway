# Futures
from __future__ import annotations

# Standard Library
import abc


class AbstractUnitOfWork(abc.ABC):
    async def __aenter__(self) -> AbstractUnitOfWork:
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    def collect_new_events(self):
        pass

    @abc.abstractmethod
    async def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError


class UnitOfWork(AbstractUnitOfWork):
    async def __aenter__(self) -> AbstractUnitOfWork:
        return await super().__aenter__()

    async def __aexit__(self, *args):
        await super().__aexit__(*args)

    async def commit(self):
        await self._commit()

    async def _commit(self):
        pass

    async def rollback(self):
        pass
