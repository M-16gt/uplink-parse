from uplink_parse.core.ctx import ctx
from uplink_parse.core.singleton import Singleton
from uplink_parse.core._generics import StrategyGeneric, output_data_from_func
from uplink_parse.core.utils import _name
from uplink_parse.core.exceptions import UnsupportedClientError


class Strategy(StrategyGeneric[output_data_from_func], Singleton):
    funcs_dict = {}

    def __call__(self, response) -> output_data_from_func:
        client_name = _name(ctx.consumer._Consumer__client.__class__)  # noqa
        try:
            return self.funcs_dict[client_name](response)
        except KeyError:
            raise UnsupportedClientError(
                f"{self.__class__.__name__} has no handler for client '{client_name}'.",
                client_name=client_name,
                source=self.__class__.__name__,
            ) from None