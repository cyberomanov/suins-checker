from typing import List, Optional

from pydantic import BaseModel


class Fields(BaseModel):
    balance: str


class Content(BaseModel):
    fields: Fields


class DataObject(BaseModel):
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
