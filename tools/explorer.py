import json

import requests
from loguru import logger

from data.constants import SUINS_NFT_ADDRESS
from datatypes.airdrop import ExplorerResponse
from tools.change_ip import execute_change_ip
from user_data.config import change_ip_url


def get_suins_airdrop_item(index: int, address: str, session: requests.Session()) -> ExplorerResponse:
    change_ip = execute_change_ip(change_ip_url=change_ip_url)
    if change_ip:
        logger.info(f"{index} | {address} | ip has been changed.")

    url = "https://fullnode.mainnet.sui.io/"
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "suix_getOwnedObjects",
        "params": [
            address, {
                "filter":
                    {"MatchAny":
                        [{
                            "StructType": SUINS_NFT_ADDRESS
                        }]},
                "options":
                    {
                        "showType": True,
                        "showContent": True,
                        "showDisplay": True
                    }
            },
            None,
            50]
    }

    response = session.post(url=url, json=data)
    return ExplorerResponse.parse_obj(json.loads(response.content))
