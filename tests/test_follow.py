from dataclasses import dataclass
from typing import Any

from uplink_parse.core.parse.text import TextParse
from uplink_parse.decorators import field


@dataclass
class Response:
    url: str
    text: str
    status_code: int = 200


class Consumer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, url: str, **options: Any) -> Response:
        self.calls.append((method, url, options))
        return Response(url, "next page")


class AsyncConsumer(Consumer):
    async def request(self, method: str, url: str, **options: Any) -> Response:
        return super().request(method, url, **options)


class Page(TextParse):
    @field
    def value(self) -> Any:
        if self.response_raw.url.endswith("/next"):
            return self.response
        return self.follow("/next")


class Body(TextParse):
    @field
    def value(self) -> str:
        return self.response


class SyncGenerator(TextParse):
    @field
    def values(self) -> Any:
        yield self.response
        yield self.follow(
            url="https://cdn.example/image", callback=Body(is_decorator=False)
        )


class AsyncField(TextParse):
    @field
    async def value(self) -> Any:
        return await self.follow(
            "image.jpg",
            url="https://cdn.example/photos/",
            callback=Body(is_decorator=False),
            method="POST",
            json={"size": "small"},
        )


def test_sync_field_can_return_follow() -> None:
    consumer = AsyncConsumer()

    result = Page(is_decorator=False)(
        consumer, Response("https://site.example/a", "first")
    )

    assert result == {"value": {"value": "next page"}}
    assert consumer.calls == [("GET", "https://site.example/next", {})]


def test_sync_generator_can_yield_follow_with_full_url() -> None:
    consumer = Consumer()

    result = SyncGenerator(is_decorator=False)(
        consumer, Response("https://site.example/a", "first")
    )

    assert result == {"values": ["first", {"value": "next page"}]}
    assert consumer.calls == [("GET", "https://cdn.example/image", {})]


def test_async_field_can_await_follow_with_custom_base() -> None:
    consumer = AsyncConsumer()

    result = AsyncField(is_decorator=False)(
        consumer, Response("https://site.example/a", "first")
    )

    assert result == {"value": {"value": "next page"}}
    assert consumer.calls == [
        ("POST", "https://cdn.example/photos/image.jpg", {"json": {"size": "small"}})
    ]
