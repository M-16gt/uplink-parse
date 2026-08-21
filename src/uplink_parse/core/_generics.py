from typing import TypeVar

from uplink_parse.core.generic_base import make_generic

strategy = TypeVar("strategy")
strategy_rt = TypeVar("strategy_rt")

ParseGeneric = make_generic("ParseGeneric", strategy, strategy_rt)

input_rt_func = TypeVar("input_rt_func")
output_rt_func = TypeVar("output_rt_func")

RegistryGeneric = make_generic("RegistryGeneric", input_rt_func, output_rt_func)

output_data_from_func = TypeVar("output_data_from_func")
attr_name = TypeVar("attr_name")

StrategyGeneric = make_generic("StrategyGeneric", output_data_from_func, attr_name)
