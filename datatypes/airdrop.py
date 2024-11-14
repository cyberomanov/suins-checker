from typing import List, Optional

from pydantic import BaseModel


class Id(BaseModel):
    id: str


class Fields(BaseModel):
    balance: str
    id: Id


class Content(BaseModel):
    dataType: str
    type: str
    hasPublicTransfer: bool
    fields: Fields


class DisplayData(BaseModel):
    description: str
    image_url: str
    name: str


class Display(BaseModel):
    data: DisplayData
    error: Optional[str]


class DataObject(BaseModel):
    objectId: str
    version: str
    digest: str
    type: str
    display: Display
    content: Content


class ExplorerData(BaseModel):
    data: DataObject


class Result(BaseModel):
    data: List[ExplorerData]
    nextCursor: Optional[str]
    hasNextPage: bool


class ExplorerResponse(BaseModel):
    jsonrpc: str
    result: Result
    id: int
