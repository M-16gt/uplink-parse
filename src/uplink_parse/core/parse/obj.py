"""Уровень 1: объект парсера — конфиг, хранилище, сбор полей, создание."""

from __future__ import annotations

from collections.abc import Mapping
from types import MethodType
from typing import TYPE_CHECKING, Any

import attrs

from uplink_parse.core._generics import ParseGeneric, strategy, strategy_rt
from uplink_parse.core.tasks.task_runner import TaskRunner
from uplink_parse.core.utils.ctx import ctx
from uplink_parse.core.utils.markers import Markers
from uplink_parse.decorators.hooks import class_hooks_of
from uplink_parse.decorators.meta import FuncMeta, PopulateFunc

if TYPE_CHECKING:
    from typing_extensions import Self

    from uplink_parse.core.parse.response import ResponseInfo

try:
    from uplink import response_handler
except ImportError:

    def response_handler(handler: Any, requires_consumer: bool = False) -> Any:
        return handler


#: Поля парсера, сгруппированные по ``populate``.
ParseMeta = dict[PopulateFunc, list[FuncMeta]]


def _params(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Копия параметров: конфиг не должен меняться снаружи по ссылке."""
    return dict(value or {})


@attrs.define(frozen=True, kw_only=True)
class ParseConfig:
    """Всё, что можно настроить у парсера. Лежит в ``Storage.config``.

    Неизменяемый: новые значения делаются через :meth:`merged` или
    ``attrs.evolve``, поэтому один конфиг можно безопасно делить между
    парсерами.

    Attributes:
        strategy_params: именованные аргументы для ``Strategy.transform`` —
            то, во что сырой ответ превращается (``features`` у BeautifulSoup,
            ``parser`` у XML и т.п.).
        read_params: именованные аргументы для вызова атрибута ответа, из
            которого стратегия читает данные: ``response.text(encoding=...)``,
            ``response.json(loads=...)``. Если атрибут не вызываемый
            (``requests.Response.text``), параметры игнорируются.
        batch_size: сколько элементов асинхронного генератора копить до
            сброса в результат.
        use_thread_for_sync: выполнять синхронные поля в потоке.
    """

    strategy_params: dict[str, Any] = attrs.field(factory=dict, converter=_params)
    read_params: dict[str, Any] = attrs.field(factory=dict, converter=_params)
    batch_size: int = attrs.field(
        default=200,
        validator=[attrs.validators.instance_of(int), attrs.validators.gt(0)],
    )
    use_thread_for_sync: bool = True

    def merged(
        self,
        *,
        strategy_params: Mapping[str, Any] | None = None,
        read_params: Mapping[str, Any] | None = None,
    ) -> ParseConfig:
        """Копия, где переданные параметры дополняют (и перекрывают) текущие."""
        if not strategy_params and not read_params:
            return self
        return attrs.evolve(
            self,
            strategy_params={**self.strategy_params, **(strategy_params or {})},
            read_params={**self.read_params, **(read_params or {})},
        )


@attrs.define(slots=False)
class Storage:
    parse_funcs_meta: ParseMeta
    task_runner: TaskRunner
    config: ParseConfig

    @classmethod
    def build(cls, owner: Parseable, config: ParseConfig) -> Storage:
        """Хранилище конкретного экземпляра: у каждого поля ``func`` привязан
        к ``owner`` (на копии, общие меты класса не трогаем)."""
        groups: ParseMeta = {}
        for meta in owner.parse_fields:
            local = attrs.evolve(meta, func=MethodType(meta.func, owner))
            groups.setdefault(local.populate, []).append(local)  # type: ignore[arg-type]
        runner = TaskRunner(
            batch_size=config.batch_size,
            use_thread_for_sync=config.use_thread_for_sync,
            class_hooks=class_hooks_of(owner),
        )
        return cls(groups, runner, config)


def _field_meta(value: Any) -> FuncMeta | None:
    meta = getattr(value, Markers.META, None)
    if isinstance(meta, FuncMeta) and meta.populate is not None:
        return meta
    return None


class Parseable:
    """Собирает поля парсера (функции с ``@field``/``@fields``) при создании класса."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        names: set[str] = {
            meta.name
            for base in cls.__bases__
            for meta in getattr(base, Markers.PARSE_FIELDS, ())
        }
        for name, value in cls.__dict__.items():
            if (meta := _field_meta(value)) is not None:
                meta.name = name
                names.add(name)
        setattr(
            cls,
            Markers.PARSE_FIELDS,
            {meta for n in names if (meta := _field_meta(getattr(cls, n, None)))},
        )

    @property
    def parse_fields(self) -> set[FuncMeta]:
        return getattr(self, Markers.PARSE_FIELDS, set())


class _ParseObj(Parseable, ParseGeneric[strategy, strategy_rt]):
    storage: Storage
    scraper: Self
    response: strategy_rt
    response_raw: Any
    response_info: ResponseInfo
    consumer: Any
    request: Any

    def __new__(
        cls,
        *,
        is_decorator: bool = True,
        config: ParseConfig | None = None,
        strategy_params: Mapping[str, Any] | None = None,
        read_params: Mapping[str, Any] | None = None,
    ) -> Any:
        """``config`` — готовый ``ParseConfig``; ``strategy_params`` и
        ``read_params`` — сокращения, которые дополняют его поверх."""
        instance = super().__new__(cls)
        instance.storage = Storage.build(
            instance,
            (config or ParseConfig()).merged(
                strategy_params=strategy_params, read_params=read_params
            ),
        )
        return parse(instance) if is_decorator else instance

    def __getattr__(self, item: str) -> Any:
        return getattr(ctx, item)


def parse(obj: _ParseObj[Any, Any]) -> Any:
    """Превратить парсер в обработчик ответа uplink."""
    return response_handler(obj.__call__, requires_consumer=True)
