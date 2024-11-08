import time

from loguru import logger

from tools.add_logger import add_logger
from tools.explorer import get_suins_airdrop_item
from tools.other_utils import read_file, get_proxied_session
from user_data.config import mobile_proxy

if __name__ == '__main__':
    add_logger(version='v1.0')
    try:
        addresses = read_file(path='user_data/address.txt')
        session = get_proxied_session(proxy=mobile_proxy)

        eligible_addresses = []
        total_balance = 0
        for index, address in enumerate(addresses, start=1):
            try:
                airdrop = get_suins_airdrop_item(index=index, address=address, session=session)
                if airdrop.result.data:
                    drop_amount = round(int(airdrop.result.data[0].data.content.fields.balance) / 1_000_000)
                    eligible_addresses.append(address)
                    total_balance += drop_amount

                    logger.success(f"{index} | {address}: {drop_amount} $NS.")
                else:
                    logger.info(f"{index} | {address}: not eligible.")
            except Exception as e:
                logger.exception(e)

        logger.info(f'{len(eligible_addresses)}/{len(addresses)} addresses are eligible for {total_balance} $NS:\n')
        time.sleep(3)
        for address in eligible_addresses:
            print(address)

    except KeyboardInterrupt:
        exit()
    except Exception as e:
        logger.exception(e)
