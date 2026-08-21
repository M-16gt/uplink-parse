import time

import repath
from werkzeug.routing import Map, Rule

# ==============================================================================
# 1. Реализации для теста
# ==============================================================================


class WerkzeugRouter:
    def __init__(self):
        self._map = Map()
        self._cache = {}

    def add_pattern(self, pattern: str):
        # Нормализуем {name} в <name> для Werkzeug
        normalized = pattern.replace("{", "<").replace("}", ">")
        self._map.add(Rule(normalized, endpoint="match"))
        # Пересоздаем адаптер (в реальном use-case это делается один раз после всех add)
        self._adapter = self._map.bind("")
        self._cache.clear()

    def match(self, template: str) -> bool:
        if template in self._cache:
            return self._cache[template]
        try:
            self._adapter.match(template)
            self._cache[template] = True
            return True
        except Exception:
            self._cache[template] = False
            return False


class RepathRouter:
    def __init__(self):
        self._compiled = {}
        self._cache = {}

    def add_pattern(self, pattern: str):
        # repath нативно поддерживает синтаксис {name}
        self._compiled[pattern] = repath.compile(pattern)
        self._cache.clear()

    def match(self, template: str) -> bool:
        if template in self._cache:
            return self._cache[template]

        for compiled in self._compiled.values():
            if compiled.match(template) is not None:
                self._cache[template] = True
                return True

        self._cache[template] = False
        return False


# ==============================================================================
# 2. Сценарий тестирования
# ==============================================================================


def run_benchmark(num_routes: int, num_iterations: int):
    print(f"\n{'=' * 60}")
    print(f"ТЕСТ: {num_routes} маршрутов, {num_iterations} итераций матчинга")
    print(f"{'=' * 60}")

    # Генерируем тестовые данные
    routes = [f"/api/v1/resource_{i}/item/{{id}}" for i in range(num_routes)]
    target_hit = f"/api/v1/resource_{num_routes // 2}/item/{{id}}"  # Должен совпасть
    target_miss = "/api/v1/other_resource/{id}"  # Не должен совпасть

    # --- WERKZEUG ---
    wz_router = WerkzeugRouter()

    start = time.perf_counter()
    for r in routes:
        wz_router.add_pattern(r)
    wz_setup_time = time.perf_counter() - start

    # Холодный матч (первый раз, без кэша)
    start = time.perf_counter()
    for _ in range(100):  # 100 раз для холодного, чтобы было видно
        wz_router.match(target_hit)
    wz_cold_time = (time.perf_counter() - start) / 100

    # Горячий матч (из кэша)
    start = time.perf_counter()
    for _ in range(num_iterations):
        wz_router.match(target_hit)
        wz_router.match(target_miss)
    wz_hot_time = (time.perf_counter() - start) / (num_iterations * 2)

    # --- REPATH ---
    rp_router = RepathRouter()

    start = time.perf_counter()
    for r in routes:
        rp_router.add_pattern(r)
    rp_setup_time = time.perf_counter() - start

    # Холодный матч
    start = time.perf_counter()
    for _ in range(100):
        rp_router.match(target_hit)
    rp_cold_time = (time.perf_counter() - start) / 100

    # Горячий матч
    start = time.perf_counter()
    for _ in range(num_iterations):
        rp_router.match(target_hit)
        rp_router.match(target_miss)
    rp_hot_time = (time.perf_counter() - start) / (num_iterations * 2)

    # --- ВЫВОД ---
    print(f"{'Метрика':<25} | {'Werkzeug':<15} | {'Repath':<15} | {'Победитель'}")
    print(f"{'-' * 65}")
    print(
        f"{'Инициализация (Setup)':<25} | {wz_setup_time * 1000:>6.3f} ms    | {rp_setup_time * 1000:>6.3f} ms    | {'Repath' if rp_setup_time < wz_setup_time else 'Werkzeug'}"
    )
    print(
        f"{'Холодный матч (Cold)':<25} | {wz_cold_time * 1000:>6.3f} ms    | {rp_cold_time * 1000:>6.3f} ms    | {'Repath' if rp_cold_time < wz_cold_time else 'Werkzeug'}"
    )
    print(
        f"{'Горячий матч (Hot, кэш)':<25} | {wz_hot_time * 1000:>6.3f} ms | {rp_hot_time * 1000:>6.3f} ms | {'Ничья (словарь)' if abs(wz_hot_time - rp_hot_time) < 0.0001 else ('Repath' if rp_hot_time < wz_hot_time else 'Werkzeug')}"
    )


# Запускаем тесты
if __name__ == "__main__":
    # Сценарий 1: Реалистичный для парсера (мало маршрутов, много запросов)
    run_benchmark(num_routes=15, num_iterations=100_000)

    # Сценарий 2: Стресс-тест (много маршрутов)
    run_benchmark(num_routes=1000, num_iterations=100_000)
