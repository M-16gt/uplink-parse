import inspect
from typing import Any

__all__ = ["is_stateless", "await_or_return"]


_VAR_ARGS = inspect.CO_VARARGS | inspect.CO_VARKEYWORDS


def is_stateless(cls: Any) -> bool:
    """``True``, если ``cls()`` можно вызвать без аргументов: ``__init__`` не
    объявлен или принимает только ``self`` (``*args``, ``**kwargs`` и
    keyword-only параметры тоже считаются состоянием)."""
    init = cls.__init__
    if init is object.__init__:
        return True
    code = init.__code__
    return (
        code.co_argcount == 1
        and not code.co_kwonlyargcount
        and not code.co_flags & _VAR_ARGS
    )


async def await_or_return(obj: Any) -> Any:
    if hasattr(obj, "__await__"):
        return await obj
    return obj
