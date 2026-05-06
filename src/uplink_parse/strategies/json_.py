from uplink_parse.core.strategy import Strategy

__all__ = ["JSONStrategy"]

JSONResult = dict

class JSONStrategy(Strategy):
    """Strategy for parsing JSON content from HTTP response.

    This strategy extracts and parses JSON data from the response body.
    Uses the built-in `response.json()` method which automatically handles
    content decoding and JSON deserialization.

    Attributes:
        None

    Methods:
        __call__(response): Parses response content as JSON and returns
                           a dictionary.

    Example:
        >>> strategy = JSONStrategy()
        >>> data = strategy(response)  # returns dict
        >>> user_name = data['user']['name']

    Note:
        Relies on the response object's `.json()` method. For requests.Response
        objects, this will raise appropriate exceptions (ValueError, JSONDecodeError)
        if the response is not valid JSON.
    """

    def __call__(self, response) -> JSONResult:
        """Parse HTTP response as JSON and return dictionary.

        Args:
            response: HTTP response object (similar to requests.Response)
                     containing JSON data to parse.

        Returns:
            dict: Parsed JSON data as Python dictionary.

        Raises:
            ValueError: If response body does not contain valid JSON.
            requests.exceptions.JSONDecodeError: If JSON decoding fails
                                                (when using requests library).
        """
        return response.json()