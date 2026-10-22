from pydantic import BaseModel, Field


class UrlItem(BaseModel):
    """Pydantic model representing a single URL item extracted from a web page.

    Attributes:
        url (str): URL to an article card or pagination link.
        ttype (str): Type of the URL. Must be equal to `link` if the URL points to an article card, otherwise `PAG`.
    """
    url: str = Field(description="Url to article card or pagination link")
    ttype: str = Field(description="Must be equal `link` if url is link to article card else PAG")


class URLList(BaseModel):
    """Pydantic model representing a collection of URL items.

    Attributes:
        items (list[UrlItem]): A list of UrlItem instances containing the extracted URLs and their types.
    """
    items: list[UrlItem]