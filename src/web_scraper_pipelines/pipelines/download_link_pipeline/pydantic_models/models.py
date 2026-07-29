from pydantic import (BaseModel,
                      Field)


class UrlItem(BaseModel):
    name: str = Field(description="Article name or 'PAG' if url is pagination link. Don't name article url as Download")
    url: str = Field(description="url to another site page or direct download link or pagination link")
    ttype: str = Field(description='equal "link" if url is link to another page on site or "direct" if url is direct url to download file. You are must be sure what link is direct else write "link"')


class URLList(BaseModel):
    items: list[UrlItem]