import json
from typing import Any
from xml.etree import ElementTree as ET

import pytest

from uplink_parse.core._dataclasses import ParseConfig
from uplink_parse.core.parse import BytesParse, JSONParse, TextParse, XMLParse
from uplink_parse.decorators import field


class Response:
    """Как aiohttp: ``text``/``json``/``read`` — методы с параметрами."""

    status_code = 200
    url = "https://site.example/"

    def __init__(self, body: bytes) -> None:
        self.body = body
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def text(self, encoding: str = "utf-8") -> str:
        self.calls.append(("text", {"encoding": encoding}))
        return self.body.decode(encoding)

    def json(self, **kwargs: Any) -> Any:
        self.calls.append(("json", kwargs))
        return json.loads(self.body, **kwargs)

    def read(self, n: int = -1) -> bytes:
        self.calls.append(("read", {"n": n}))
        return self.body[:n] if n >= 0 else self.body


class PropertyResponse:
    """Как requests/httpx: ``text`` — свойство, вызвать его с аргументами нельзя."""

    status_code = 200
    url = "https://site.example/"
    text = "plain"


def run(parser: Any, response: Any) -> Any:
    return parser(response)


class Echo(TextParse):
    @field
    def value(self) -> str:
        return self.response


def test_read_params_reach_the_callable_of_a_base_strategy() -> None:
    response = Response("привет".encode("cp1251"))

    result = run(Echo(is_decorator=False, read_params={"encoding": "cp1251"}), response)

    assert result == {"value": "привет"}
    assert response.calls == [("text", {"encoding": "cp1251"})]


def test_read_params_work_for_json_and_bytes() -> None:
    class Data(JSONParse):
        @field
        def value(self) -> Any:
            return self.response

    class Raw(BytesParse):
        @field
        def value(self) -> bytes:
            return self.response

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        return {k.upper(): v for k, v in pairs}

    body = b'{"a": 1}'
    assert run(
        Data(is_decorator=False, read_params={"object_pairs_hook": hook}),
        Response(body),
    ) == {"value": {"A": 1}}
    assert run(Raw(is_decorator=False, read_params={"n": 3}), Response(body)) == {
        "value": b'{"a'
    }


def test_no_params_keeps_calling_without_arguments() -> None:
    response = Response(b"hi")

    run(Echo(is_decorator=False), response)

    assert response.calls == [("text", {"encoding": "utf-8"})]


def test_read_params_are_ignored_for_non_callable_attribute() -> None:
    parser = Echo(is_decorator=False, read_params={"encoding": "cp1251"})

    assert run(parser, PropertyResponse()) == {"value": "plain"}


def test_response_info_is_empty_when_response_has_no_url_or_status() -> None:
    class Info(TextParse):
        @field
        def info(self) -> Any:
            return self.response_info

    info = run(Info(is_decorator=False), "payload")["info"]

    assert info.url is None
    assert info.status_code is None


def test_property_attribute_still_works_without_read_params() -> None:
    assert run(Echo(is_decorator=False), PropertyResponse()) == {"value": "plain"}


def test_strategy_params_go_to_transform_and_read_params_to_the_read_call() -> None:
    bs4 = pytest.importorskip("bs4")
    from uplink_parse.core.parse.bs4 import BS4Parse

    seen: dict[str, Any] = {}

    class Page(BS4Parse):
        @field
        def title(self) -> str:
            seen["response"] = self.response
            return self.response.h1.get_text()

    response = Response("<h1>привет</h1><p>x</p>".encode("cp1251"))
    parser = Page(
        is_decorator=False,
        strategy_params={"parse_only": bs4.SoupStrainer("h1")},
        read_params={"encoding": "cp1251"},
    )

    assert run(parser, response) == {"title": "привет"}
    assert response.calls == [("text", {"encoding": "cp1251"})]
    assert seen["response"].p is None  # parse_only дошёл до BeautifulSoup


def test_bs4_keeps_default_parser_when_only_other_params_given() -> None:
    bs4 = pytest.importorskip("bs4")
    from uplink_parse.core.strategies.bs4 import BS4Strategy

    soup = BS4Strategy().transform("<h1>a</h1>", parse_only=bs4.SoupStrainer("h1"))

    assert soup.builder.NAME == "html.parser"


def test_xml_strategy_params_reach_the_parser() -> None:
    class Doc(XMLParse):
        @field
        def tag(self) -> str:
            return self.response.tag

    parser = Doc(
        is_decorator=False, strategy_params={"parser": ET.XMLParser(encoding="utf-8")}
    )

    assert run(parser, Response(b"<root/>")) == {"tag": "root"}


def test_config_object_and_shortcuts_are_merged_with_shortcuts_winning() -> None:
    config = ParseConfig(
        read_params={"encoding": "cp1251", "errors": "strict"},
        strategy_params={"features": "html.parser"},
        batch_size=10,
    )

    storage = Echo(
        is_decorator=False, config=config, read_params={"errors": "ignore"}
    ).storage

    assert storage.config.read_params == {"encoding": "cp1251", "errors": "ignore"}
    assert storage.config.strategy_params == {"features": "html.parser"}
    assert storage.config.batch_size == 10
    assert storage.task_runner.batch_size == 10
    assert config.read_params["errors"] == "strict"  # исходный конфиг не тронут


def test_task_runner_settings_come_from_config() -> None:
    storage = Echo(
        is_decorator=False, config=ParseConfig(use_thread_for_sync=False)
    ).storage

    assert storage.task_runner.use_thread_for_sync is False
    assert storage.task_runner.batch_size == 200


def test_config_copies_params_and_validates() -> None:
    params = {"encoding": "utf-8"}
    config = ParseConfig(read_params=params)
    params["encoding"] = "cp1251"

    assert config.read_params == {"encoding": "utf-8"}
    with pytest.raises(ValueError):
        ParseConfig(batch_size=0)


def test_instances_do_not_share_config() -> None:
    first = Echo(is_decorator=False, read_params={"encoding": "cp1251"})
    second = Echo(is_decorator=False)

    assert first.storage.config.read_params == {"encoding": "cp1251"}
    assert second.storage.config.read_params == {}
