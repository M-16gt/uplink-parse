from __future__ import annotations

from typing import Any


class UplinkParseError(Exception):
    """
    Корень иерархии всех исключений библиотеки.

    Любое исключение библиотеки можно поймать через `except UplinkParseError`,
    не заботясь о конкретном подклассе. Каждое исключение автоматически
    пытается захватить текущий ScraperCtxData (если есть активный контекст) —
    удобно для отладки скрапинга: видно на каком request/response всё упало.
    """

    def __init__(self, message: str = "", *, context: Any = None, source: Any = None):
        self.message = message
        self.source = source
        self.context = context if context is not None else self._snapshot_ctx()
        super().__init__(message)

    @staticmethod
    def _snapshot_ctx() -> Any:
        try:
            from uplink_parse.core.ctx import _cv_ctx
            return _cv_ctx.get()
        except Exception:  # noqa
            return None

    def __str__(self) -> str:
        base = self.message or self.__class__.__name__
        if self.source is not None:
            base = f"[{self.source}] {base}"
        if self.context is not None:
            base = f"{base} (ctx={self.context!r})"
        return base


# --------------------------------------------------------------------------- #
# ctx.py — контекст скрапера (contextvars)
# --------------------------------------------------------------------------- #

class ContextError(UplinkParseError, RuntimeError):
    """Ошибки, связанные с ScraperCtx / _cv_ctx / _cv_builder."""


class NoActiveContextError(ContextError):
    """Обращение к ctx-прокси без активного `with ScraperCtx(...)`."""


# --------------------------------------------------------------------------- #
# registry.py — регистрация @field/@fields на классах
# --------------------------------------------------------------------------- #

class RegistryError(UplinkParseError):
    """Ошибки BaseRegistry (регистрация/поиск методов-полей)."""


class NotRegisteredError(RegistryError, LookupError):
    """Запрошенное имя не зарегистрировано у владельца."""

    def __init__(self, message: str = "", *, names: tuple[str, ...] = (), owner: type | None = None, **kwargs):
        self.names = names
        self.owner = owner
        super().__init__(message, **kwargs)


# --------------------------------------------------------------------------- #
# strategy.py / task_strategy.py — выбор стратегии парсинга/выполнения
# --------------------------------------------------------------------------- #

class StrategyError(UplinkParseError):
    """Базовый класс ошибок выбора/исполнения стратегии."""


class StrategyNotFoundError(StrategyError, NotImplementedError):
    """
    Не найдена подходящая стратегия под цель (client / target).
    Наследует NotImplementedError — старый код, ловящий NotImplementedError,
    продолжит работать без изменений.
    """

    def __init__(self, message: str = "", *, target: Any = None, **kwargs):
        self.target = target
        super().__init__(message, **kwargs)


class UnsupportedClientError(StrategyError):
    """У Strategy.funcs_dict нет обработчика для текущего uplink-клиента."""

    def __init__(self, message: str = "", *, client_name: str | None = None, **kwargs):
        self.client_name = client_name
        super().__init__(message, **kwargs)


# --------------------------------------------------------------------------- #
# processor.py / parse.py — извлечение данных
# --------------------------------------------------------------------------- #

class ProcessorError(UplinkParseError):
    """Ошибки BaseProcessor (сбор зарегистрированных полей в target)."""


class PopulateTargetNotImplementedError(ProcessorError, NotImplementedError):
    """Подкласс BaseProcessor не переопределил _populate_target."""


class ParseError(UplinkParseError):
    """Ошибки верхнего уровня: разбор ответа в структуру."""


class ResponseParsingError(ParseError):
    """Стратегия не смогла привести response к нужному виду (BS4/XML/JSON/...)."""


class FieldExtractionError(ParseError):
    """Конкретный @field/@fields callable упал во время извлечения."""

    def __init__(self, message: str = "", *, field_name: str | None = None, **kwargs):
        self.field_name = field_name
        super().__init__(message, **kwargs)

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} [field={self.field_name}]" if self.field_name else base


# --------------------------------------------------------------------------- #
# hooks.py — pre/post/compose/error хуки
# --------------------------------------------------------------------------- #

class HookError(UplinkParseError):
    """Базовый класс ошибок системы хуков."""


class HookExecutionError(HookError):
    """Хук-callable упал во время выполнения (не сам wrapped func)."""

    def __init__(self, message: str = "", *, hook_name: str | None = None, **kwargs):
        self.hook_name = hook_name
        super().__init__(message, **kwargs)

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} [hook={self.hook_name}]" if self.hook_name else base


class AllErrorHooksFailedError(HookError):
    """Ни один обработчик errorhook не смог восстановиться после исключения."""

    def __init__(self, message: str = "", *, original: BaseException | None = None, **kwargs):
        self.original = original
        super().__init__(message, **kwargs)
