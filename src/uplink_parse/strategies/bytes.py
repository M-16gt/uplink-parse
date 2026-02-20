from uplink_parse.strategy import Strategy

class BytesStrategy(Strategy):
    def __call__(self, response) -> bytes:
        return response.content