import pytest

from uplink_parse.core.hooks import SKIP, UNHANDLED
from uplink_parse.core.parse.text import TextParse
from uplink_parse.core.utils.ctx import ctx
from uplink_parse.decorators import (
    errorhook,
    field,
    paramshook,
    posthook,
    prehook,
)


def run(parser_type, response="payload"):
    return parser_type(is_decorator=False)(response)


def test_class_and_field_hooks_run_in_order_and_field_params_win():
    calls = []

    async def class_pre(meta):
        calls.append("class pre")
        return True

    @prehook(class_pre)
    @paramshook(lambda meta: calls.append("class params") or {"name": "class"})
    @posthook(lambda value, meta: calls.append("class post") or value + " class")
    class Page(TextParse):
        @field
        @prehook(lambda meta: calls.append("field pre") or True)
        @paramshook(lambda meta: calls.append("field params") or {"name": ctx.response})
        @posthook(lambda value, meta: calls.append("field post") or value + " field")
        def title(self, name):
            calls.append("field call")
            return name

    assert run(Page, "local") == {"title": "local field class"}
    assert calls == [
        "class pre",
        "field pre",
        "class params",
        "field params",
        "field call",
        "field post",
        "class post",
    ]


def test_skip_and_replacement_bypass_params_and_field_call():
    @prehook(lambda meta: SKIP if meta.name == "ignored" else None)
    @paramshook(lambda meta: pytest.fail("params should not run"))
    class Page(TextParse):
        @field
        def ignored(self):
            pytest.fail("skipped field should not run")

        @field
        @posthook(lambda value, meta: ("replacement", value))
        def replacement(self):
            pytest.fail("replaced field should not run")

    assert run(Page) == {"replacement": ("replacement", None)}


def test_error_hook_fallback_and_valid_none():
    @errorhook(lambda exc, meta: f"class fallback: {exc}")
    class Page(TextParse):
        @field
        @errorhook(lambda exc, meta: UNHANDLED)
        def fallback(self):
            raise ValueError("bad")

        @field
        @errorhook(lambda exc, meta: None)
        def empty(self):
            raise ValueError("bad")

    assert run(Page) == {"fallback": "class fallback: bad", "empty": None}


def test_error_inside_error_hook_is_not_swallowed():
    @errorhook(lambda exc, meta: "class fallback")
    class Page(TextParse):
        @field
        @errorhook(lambda exc, meta: 1 / 0)
        def broken(self):
            raise ValueError("bad")

    with pytest.raises(ZeroDivisionError):
        run(Page)


def test_post_and_error_hooks_can_skip_whole_field():
    class Page(TextParse):
        @field
        @posthook(lambda value, meta: SKIP)
        def post_skipped(self):
            return "value"

        @field
        @errorhook(lambda exc, meta: SKIP)
        def error_skipped(self):
            raise ValueError("bad")

    assert run(Page) == {}


def test_async_generator_post_receives_whole_result():
    @paramshook(lambda meta: {"count": len(ctx.response)})
    class Page(TextParse):
        @field
        @posthook(lambda value, meta: list(reversed(value)))
        async def numbers(self, count):
            for value in range(count):
                yield value

    assert run(Page, "abc") == {"numbers": [2, 1, 0]}


def test_class_hooks_inherit_without_mutating_parent():
    @posthook(lambda value, meta: value + " parent")
    class Parent(TextParse):
        @field
        def title(self):
            return "value"

    @posthook(lambda value, meta: value + " child")
    class Child(Parent):
        pass

    assert run(Parent) == {"title": "value parent"}
    assert run(Child) == {"title": "value child parent"}


def test_params_hook_reads_current_response_after_previous_parse():
    class Response:
        status_code = 200
        text = "first"

    @paramshook(lambda meta: {"value": ctx.response})
    class Page(TextParse):
        @field
        def title(self, value):
            return value

    assert run(Page, Response()) == {"title": "first"}
    assert run(Page, "second") == {"title": "second"}
