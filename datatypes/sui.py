from typing import Optional

from pydantic import BaseModel
from pysui import SuiConfig
from pysui.sui.sui_txn import SyncTransaction
from pysui.sui.sui_types.scalars import ObjectID


class SuiTxResult(BaseModel):
    address: str
    digest: str
    reason: Optional[str]


class SuiBalance(BaseModel):
    int: int
    float: float


class SuiTransferConfig(BaseModel):
    config: SuiConfig
    address: str

    class Config:
        arbitrary_types_allowed = True


class SuiTx(BaseModel):
    builder: SyncTransaction
    gas: ObjectID
    merge_count: Optional[int]

    class Config:
        arbitrary_types_allowed = True
