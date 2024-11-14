import random
import time

from loguru import logger

from data.constants import EXPLORER, SUINS_COIN_TYPE, USDC_DENOMINATION
from tools.add_logger import add_logger
from tools.explorer import get_suins_airdrop_item
from tools.other_utils import read_file, get_proxied_session, short_address
from tools.sui import get_sui_config, get_sui_balance, claim_suins, get_suins_obj, transfer_suins_tx
from user_data.config import mobile_proxy, sleep_between_accs, shuffle_accs

if __name__ == '__main__':
    add_logger(version='v1.0')
    try:
        mnemonics = read_file(path='user_data/mnemonic.txt')
        if shuffle_accs:
            random.shuffle(mnemonics)
        session = get_proxied_session(proxy=mobile_proxy)

        for index, mnemonic in enumerate(mnemonics, start=1):
            try:
                if '##' in mnemonic:
                    mnemonic, cex_public = mnemonic.split('##')
                else:
                    cex_public = ""

                sui_config = get_sui_config(mnemonic=mnemonic)
                address = str(sui_config.active_address)
                airdrop = get_suins_airdrop_item(index=index, address=address, session=session)
                if airdrop.result.data:
                    drop_amount = round(int(airdrop.result.data[0].data.content.fields.balance) / 1_000_000)
                    result = claim_suins(sui_config=sui_config, nft_address=airdrop.result.data[0].data.objectId)
                    suins_balance = get_sui_balance(
                        sui_config=sui_config, coin_type=SUINS_COIN_TYPE, denomination=USDC_DENOMINATION
                    )
                    logger.info(
                        f'{index} | {short_address(address)} | suins_claim | {suins_balance.float} $NS on balance '
                        f'| {EXPLORER}/{result.digest}.')
                    time.sleep(random.randint(3, 10))
                else:
                    suins_balance = get_sui_balance(
                        sui_config=sui_config, coin_type=SUINS_COIN_TYPE, denomination=USDC_DENOMINATION
                    )
                    logger.info(f"{index} | {short_address(address)}: nothing to claim | "
                                f"{suins_balance.float} $NS on balance.")

                if suins_balance.int:
                    if cex_public:
                        suins_coin_obj = get_suins_obj(sui_config=sui_config)
                        while suins_coin_obj.data:
                            coin_obj_balance = int(suins_coin_obj.data[0].balance)
                            if coin_obj_balance:
                                result = transfer_suins_tx(
                                    sui_config=sui_config, coin_obj=suins_coin_obj.data[0], recipient=cex_public
                                )
                                transfer_balance = round(
                                    int(suins_coin_obj.data[0].balance) / 10 ** USDC_DENOMINATION, 2
                                )
                                logger.info(
                                    f'{index} | {short_address(address)} | suins_transfer | '
                                    f'{transfer_balance} $NS -> {cex_public} | {EXPLORER}/{result.digest}.'
                                )

                                time.sleep(random.randint(sleep_between_accs[0], sleep_between_accs[1]))
                                suins_coin_obj = get_suins_obj(sui_config=sui_config)
                            else:
                                break
            except Exception as e:
                logger.exception(e)

    except KeyboardInterrupt:
        exit()
    except Exception as e:
        logger.exception(e)
