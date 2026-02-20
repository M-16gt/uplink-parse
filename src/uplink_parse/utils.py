from typing import Optional, Literal
from pathlib import Path

import sys
import importlib
import inspect

from uplink_parse.strategy import Strategy

def _get_strategies() -> dict[Literal["text", "json", "html", "xml", "bytes"], Strategy]:
    dict_ = {}
    for subclass in Strategy.__subclasses__():
        dict_[subclass.__name__.lower().removesuffix("strategy")] = subclass()

    return dict_

def init_strategies(folder, target_globals: Optional[dict] = None) -> None:
    if not target_globals: target_globals = globals()
    sys.path.insert(0, str(Path(folder).resolve()))
    for f in Path(folder).glob("*.py"):
        if f.name == "__init__.py": continue
        m = importlib.import_module(f.stem)
        target_globals.update({k:v for k,v in inspect.getmembers(m) if not k.startswith('_')})

init_strategies("uplink_parse/strategies", target_globals=globals())

strategies = _get_strategies()

def get_strategy_from_content_type(content_type: Optional[str]) -> Strategy:
    if not content_type:
        return strategies["text"]

    type_ = content_type.split(';')[0].strip().lower()

    for name, strategy_ in strategies.items():
        if name in type_:
            return strategy_
    return strategies["bytes"]