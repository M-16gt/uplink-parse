from uplink_parse.core.strategy import Strategy

BytesResult = bytes

class BytesStrategy(Strategy):
    """Strategy for extracting raw bytes content from HTTP response.

    This strategy retrieves the raw binary content of the response body
    without any parsing or decoding. Useful for handling binary files,
    images, or any content that should remain in its original byte form.

    Attributes:
        None

    Methods:
        __call__(response): Returns response content as bytes.

    Example:
        >>> strategy = BytesStrategy()
        >>> content = strategy(response)  # returns bytes
        >>> isinstance(content, bytes)
        True
    """

    def __call__(self, response) -> BytesResult:
        """Extract raw bytes content from HTTP response.

        Args:
            response: HTTP response object (similar to requests.Response)
                     containing the response data.

        Returns:
            bytes: Raw binary content of the response body.
        """
        return response.content