import xml.etree.ElementTree as Tree

from uplink_parse.core.strategy import Strategy

XMLResult = Tree.Element

class XMLStrategy(Strategy):
    """Strategy for parsing XML content from HTTP response.

    This strategy parses the response text as XML and returns an
    ElementTree Element object. Uses Python's built-in xml.etree.ElementTree
    module for XML parsing.

    The strategy is suitable for processing XML responses from REST APIs,
    RSS feeds, or any XML-formatted data.

    Attributes:
        None

    Methods:
        __call__(response): Parses response text as XML and returns
                           an Element object.

    Example:
        >>> strategy = XMLStrategy()
        >>> root = strategy(response)
        >>> for item in root.findall('.//item'):
        ...     title = item.find('title').text

    Raises:
        xml.etree.ElementTree.ParseError: If the response content is not
                                         valid XML.
    """

    def __call__(self, response) -> XMLResult:
        """Parse XML content from HTTP response into ElementTree Element.

        Args:
            response: HTTP response object (similar to requests.Response)
                     containing XML data to parse.

        Returns:
            xml.etree.ElementTree.Element: Root element of the parsed
                                          XML document.

        Raises:
            ParseError: If the response content is malformed or not valid XML.
        """
        return Tree.fromstring(response.text)