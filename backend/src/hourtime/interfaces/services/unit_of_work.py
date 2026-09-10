from abc import ABC, abstractmethod


class UnitOfWork(ABC):
    """Transaction boundary owned by the use case that changes state."""

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    async def flush(self) -> None:
        """Push pending writes so later reads in the same transaction see them."""
