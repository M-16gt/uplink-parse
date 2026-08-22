from __future__ import annotations

from typing import Any


class UplinkParseError(Exception):
    """Корень иерархии исключений uplink-parse.
    Любое исключение библиотеки ловится через `except UplinkParseError`.
    Автоматически захватывает активный ScraperCtx, если он есть.
    """

    def __init__(
        self,
        message: str = "",
        *,
        context: Any = None,
        source: Any = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.source = source
        self.details = details or {}
        self.context = context if context is not None else self._capture_context()
        super().__init__(message)

    @staticmethod
    def _capture_context() -> Any:
        """Пытается вытащить текущий ScraperCtxData из contextvars."""
        try:
            from uplink_parse.core.utils.ctx import _cv_ctx

            return _cv_ctx.get()
        except Exception:
            return None

    def __str__(self) -> str:
        base = self.message or self.__class__.__name__

        if self.source is not None:
            base = f"[{self.source}] {base}"

        if self.details:
            detail_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            base = f"{base} | {detail_str}"

        if self.context is not None:
            base = f"{base} (ctx={self.context!r})"

        return base

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"source={self.source!r}, "
            f"details={self.details!r}, "
            f"context={self.context!r})"
        )


# --------------------------------------------------------------------------- #
# ctx.py — контекст скрапера (contextvars)
# --------------------------------------------------------------------------- #


class ContextError(UplinkParseError):
    pass


class NoActiveContextError(ContextError):
    pass


# --------------------------------------------------------------------------- #
# strategy.py — стратегии преобразования ответа
# --------------------------------------------------------------------------- #


class StrategyError(UplinkParseError):
    pass


class UnsupportedClientError(StrategyError):
    pass


class ResponseParsingError(StrategyError):
    pass


# --------------------------------------------------------------------------- #
# task_strategy.py — стратегии выполнения задач (async gen / coro / sync / ...)
# --------------------------------------------------------------------------- #


class TaskStrategyError(UplinkParseError):
    pass


class StrategyNotFoundError(TaskStrategyError):
    pass


# --------------------------------------------------------------------------- #
# processor.py — извлечение данных
# --------------------------------------------------------------------------- #


class ProcessorError(UplinkParseError):
    pass


class ProcessorCacheError(ProcessorError):
    pass
