from uplink_parse.core.strategy import Strategy

TextResult = str

class TextStrategy(Strategy):
    """Strategy for extracting text content from HTTP response.

    This strategy retrieves the response body as a decoded string.
    The encoding is automatically determined from the HTTP headers
    (typically UTF-8) by the underlying response object.

    This is the most basic strategy, suitable for plain text responses,
    source code, or any content where you need the raw string representation.

    Attributes:
        None

    Methods:
        __call__(response): Returns response content as decoded string.

    Example:
        >>> strategy = TextStrategy()
        >>> content = strategy(response)  # returns str
        >>> print(content[:100])  # Print first 100 characters

    Note:
        For requests.Response objects, `.text` automatically handles
        content decoding based on the response's apparent encoding.
    """

    def __call__(self, response) -> TextResult:
        """Extract text content from HTTP response.

        Args:
            response: HTTP response object (similar to requests.Response)
                     containing the response data.

        Returns:
            str: Decoded text content of the response body.
        """
        return response.text