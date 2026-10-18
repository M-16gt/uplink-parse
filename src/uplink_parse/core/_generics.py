from typing import Generic, TypeVar

from uplink_parse.core.generic_base import GenericBase

strategy = TypeVar("strategy")
strategy_rt = TypeVar("strategy_rt")


class ParseGeneric(GenericBase, Generic[strategy, strategy_rt]): ...


output_data_from_func = TypeVar("output_data_from_func")
attr_name = TypeVar("attr_name")


class StrategyGeneric(GenericBase, Generic[output_data_from_func, attr_name]): ...
