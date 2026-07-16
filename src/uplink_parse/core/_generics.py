from typing import TypeVar

from uplink_parse.core.generic_base import GenericBase

strategy = TypeVar("strategy")
strategy_rt = TypeVar("strategy_rt")

class ParseGeneric(GenericBase[strategy, strategy_rt]):
    ...

input_rt_func = TypeVar("input_rt_func")
output_rt_func = TypeVar("output_rt_func")

class RegistryGeneric(GenericBase[input_rt_func, output_rt_func]):
    ...

input_data_from_func = TypeVar("input_data_from_func")
output_data_from_func = TypeVar("output_data_from_func")

class TransformGeneric(GenericBase[input_data_from_func, output_data_from_func]):
    ...

class StrategyGeneric(GenericBase[output_data_from_func]):
    ...