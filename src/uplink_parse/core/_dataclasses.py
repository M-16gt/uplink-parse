from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from enum import Enum
from types import MethodType
from typing import TYPE_CHECKING, Any, TypeVar

import attrs

from uplink_parse.core.utils.markers import Markers

if TYPE_CHECKING:
    from uplink_parse.core.tasks.task_runner import TaskRunner

#: ``populate(result, target) -> target`` — как влить результат группы полей
#: (``{имя_поля: значение}``) в итоговый словарь.
PopulateFunc = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class HookPoint(str, Enum):
    """Точки, куда можно повесить хук. Значение = имя поля в ``HookSpec``."""

    PRE = "pre"
    PARAMS = "params"
    POST = "post"
    ERROR = "error"


@attrs.define
class HookSpec:
    pre: list[Callable[..., Any]] = attrs.field(factory=list)
    params: list[Callable[..., Any]] = attrs.field(factory=list)
    post: list[Callable[..., Any]] = attrs.field(factory=list)
    error: list[Callable[..., Any]] = attrs.field(factory=list)

    def of(self, point: HookPoint) -> list[Callable[..., Any]]:
        return getattr(self, point.value)  # type: ignore[no-any-return]

    def is_empty(self) -> bool:
        return not any(self.of(p) for p in HookPoint)

    def __add__(self, other: HookSpec) -> HookSpec:
        return HookSpec(**{p.value: self.of(p) + other.of(p) for p in HookPoint})


@attrs.define(eq=False)
class FuncMeta:
    """Всё, что известно о поле парсера.

    Создаётся декораторами прямо на функции (``func.__parse_meta__``) и
    заполняется по мере применения декораторов, ``name`` дописывает
    ``Parseable.__init_subclass__``. Этот объект общий для всех экземпляров
    класса, поэтому ``func`` в нём — обычная функция; в ``BaseParse.__new__``
    для каждого экземпляра делается копия, где ``func`` привязан к нему.
    """

    func: Callable[..., Any]
    name: str = ""
    populate: PopulateFunc | None = None
    strategy: Any = None
    hooks: HookSpec = attrs.field(factory=HookSpec)


F = TypeVar("F", bound=Callable[..., Any])

#: Поля парсера, сгруппированные по ``populate``.
ParseMeta = dict[PopulateFunc, list[FuncMeta]]


def get_func_meta(func: Any) -> FuncMeta:
    """Вернуть ``FuncMeta`` функции, создав её при первом обращении."""
    meta = getattr(func, Markers.META, None)
    if meta is None:
        meta = FuncMeta(func=func)
        setattr(func, Markers.META, meta)
    return meta


def meta_decorator(update: Callable[[FuncMeta], None]) -> Callable[[F], F]:
    """Декоратор, который что-то дописывает в ``FuncMeta`` функции и возвращает
    её же. Единая основа для ``processor``, ``prehook`` и будущих расширений."""

    def decorator(func: F) -> F:
        update(get_func_meta(func))
        return func

    return decorator


def build_parse_meta(owner: Any) -> ParseMeta:
    """Поля ``owner`` для конкретного экземпляра: у каждого ``func`` привязан
    к ``owner`` (на копии, общие меты класса не трогаем), группировка по
    ``populate``."""
    groups: ParseMeta = {}
    for meta in owner.parse_fields:
        local = copy.copy(meta)
        local.func = MethodType(meta.func, owner)
        groups.setdefault(local.populate, []).append(local)
    return groups


@attrs.define(slots=False)
class ScraperCtxData:
    response: Any | None = None
    response_raw: Any | None = None
    response_info: Any | None = None
    consumer: Any | None = None
    scraper: Any | None = None
    request: Any | None = None


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
