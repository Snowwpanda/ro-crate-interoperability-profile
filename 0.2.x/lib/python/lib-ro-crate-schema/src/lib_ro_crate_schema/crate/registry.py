from typing import TypeVar, Dict, Callable, Any

from pydantic import BaseModel

T = TypeVar("T")
R = TypeVar("R")


class ForwardRef[R](BaseModel):
    """
    This internal class is used to mark
    properties as forward refs to be resolved
    """

    ref: str


class Registry[T]:
    """
    A registry used for
    forward reference resolution
    """

    def __init__(self):
        self._store: Dict[str, T] = {}

    def register(self, key: str, value: T):
        self._store[key] = value

    def resolve(self, key: ForwardRef[T]) -> T:
        return self._store.get(key.ref)

    def clear(self):
        self._store.clear()


type_registry = Registry[BaseModel]()
