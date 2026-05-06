from __future__ import annotations

import functools
from typing import Callable



def compose(main_func, *functions): # noqa
    functions = list(reversed(functions))
    def composed(*args, **kwargs):
        for i in range(len(functions)):
            if "ctx" in functions[i].__code__.co_varnames:
                functions[i] = functools.partial(functions[i], ctx=locals()) # noqa

        res = functions[0](*args, **kwargs)
        for f in functions[1:]:
            res = f(res)
        return res
    return composed


class _Transform:
    _MARKER = "feature_func"

    def __init__(
            self,
            *transforms: Callable,
            post_mutation: list[Callable] | None = None,
    ) -> None:
        chain = list(transforms) + [self._MARKER]

        for mut in (post_mutation or []):
            mut(chain)


        self._template = tuple(chain)

        self._base_mutations = post_mutation or []

    def __call__(
            self,
            func: Callable,
            post_mutation: list[Callable] | None = None
    ) -> Callable:

        chain = list(self._template)

        for mut in post_mutation or []:
            mut(chain)

        final_chain = tuple(f if f != self._MARKER else func for f in chain)

        return compose(func, *final_chain)

    def branch(self, *new_transforms: Callable) -> "_Transform":
        return _Transform(
            *new_transforms,
            post_mutation=self._base_mutations
        )


def transform(*args, **kwargs) -> _Transform:
    return _Transform(*args, **kwargs)

