from uplink_parse.strategy import Strategy

__all__ = ["JSONStrategy"]

class JSONStrategy(Strategy):

    def __call__(self, response) -> dict:
        return response.json()