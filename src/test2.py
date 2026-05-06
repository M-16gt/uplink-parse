import uplink
import aiohttp
import asyncio


# 1. Асинхронный хук
# UpLink передаст сюда объект ответа (aiohttp.ClientResponse)
async def async_response_hook(response):
    print(f"🪝 [Hook] Получен ответ от {response.url}")

    # ВАЖНО: В aiohttp чтение тела - это тоже асинхронная операция!
    # Если вы хотите вернуть данные, вы должны сделать await здесь.
    print(type(await response.text()))
    data = await response.json()

    print(f"🪝 [Hook] Данные: {data.get('title')}")

    # Возвращаем обработанные данные
    return data

def test(response):
    print("да")
    return response

@uplink.headers({'Content-Type': 'application/json'})
class MyAsyncClient(uplink.Consumer):

    @uplink.response_handler(async_response_hook)
    @uplink.get('/posts/1')
    async def get_post(self):
        """
        Обратите внимание: метод async.
        UpLink увидит, что клиент асинхронный, и будет ждать выполнения цепочки.
        """
        pass


async def main():
    # Создаем сессию явно, чтобы управлять её жизненным циклом
    async with aiohttp.ClientSession() as session:
        client = MyAsyncClient(
            base_url="https://jsonplaceholder.typicode.com",
            client=uplink.clients.AiohttpClient(session=session)
        )

        # Вызываем метод.
        # Внутри uplink:
        # 1. Выполнит запрос через aiohttp.
        # 2. Получит ClientResponse.
        # 3. Передаст его в async_response_hook.
        # 4. Сделает await async_response_hook(response).
        # 5. Вернет результат хука.
        result = await client.get_post()

        print(f"✅ Финальный результат в коде: {result}")
        print(f"📦 Тип результата: {type(result)}")


if __name__ == "__main__":
    asyncio.run(main())