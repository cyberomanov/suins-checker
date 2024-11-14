import time

from loguru import logger
from pysui.abstracts import SignatureScheme
from pysui.sui.sui_clients.common import handle_result
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_config import SuiConfig
from pysui.sui.sui_txn import SyncTransaction
from pysui.sui.sui_txresults.single_tx import SuiCoinObjects, SuiCoinObject
from pysui.sui.sui_types import SuiString, ObjectID
from pysui.sui.sui_types.address import SuiAddress

from data.constants import *
from datatypes.sui import SuiTxResult, SuiBalance, SuiTransferConfig, SuiTx
from tools.other_utils import short_address
from user_data.config import sui_rpc


def get_list_of_sui_configs(mnemonics: list[str]) -> list[SuiConfig]:
    list_of_sui_configs = []

    for mnemonic in mnemonics:
        sui_config = SuiConfig.user_config(rpc_url=sui_rpc)
        if '0x' in mnemonic:
            sui_config.add_keypair_from_keystring(keystring={
                'wallet_key': mnemonic,
                'key_scheme': SignatureScheme.ED25519
            })
        else:
            sui_config.recover_keypair_and_address(
                scheme=SignatureScheme.ED25519,
                mnemonics=mnemonic,
                derivation_path=SUI_DEFAULT_DERIVATION_PATH
            )
        sui_config.set_active_address(address=SuiAddress(sui_config.addresses[0]))
        list_of_sui_configs.append(sui_config)

    return list_of_sui_configs


def get_sui_config(mnemonic: str) -> SuiConfig:
    sui_config = SuiConfig.user_config(rpc_url=sui_rpc)

    if '0x' in mnemonic:
        sui_config.add_keypair_from_keystring(keystring={
            'wallet_key': mnemonic,
            'key_scheme': SignatureScheme.ED25519
        })
    else:
        sui_config.recover_keypair_and_address(
            scheme=SignatureScheme.ED25519,
            mnemonics=mnemonic,
            derivation_path=SUI_DEFAULT_DERIVATION_PATH
        )
    sui_config.set_active_address(address=SuiAddress(sui_config.addresses[0]))

    return sui_config


def get_list_of_transfer_configs(mnemonics: list[str]) -> list[SuiTransferConfig]:
    list_of_sui_configs = []

    for mnemonic_line in mnemonics:
        mnemonic = mnemonic_line.split(':')[0]
        address = mnemonic_line.split(':')[1]
        sui_config = SuiConfig.user_config(rpc_url=sui_rpc)
        if '0x' in mnemonic:
            sui_config.add_keypair_from_keystring(keystring={
                'wallet_key': mnemonic,
                'key_scheme': SignatureScheme.ED25519
            })
        else:
            sui_config.recover_keypair_and_address(
                scheme=SignatureScheme.ED25519,
                mnemonics=mnemonic,
                derivation_path=SUI_DEFAULT_DERIVATION_PATH
            )
        sui_config.set_active_address(address=SuiAddress(sui_config.addresses[0]))
        list_of_sui_configs.append(SuiTransferConfig(config=sui_config, address=address))

    return list_of_sui_configs


def get_sui_balance(sui_config: SuiConfig, coin_type: SuiString = None, denomination: int = None) -> SuiBalance:
    tries = 0
    while True:
        tries += 1
        try:
            client = SuiClient(config=sui_config)
            if coin_type:
                coin_objects: SuiCoinObjects = client.get_coin(coin_type=coin_type, address=sui_config.active_address,
                                                               fetch_all=True).result_data
            else:
                coin_objects: SuiCoinObjects = client.get_gas(address=sui_config.active_address,
                                                              fetch_all=True).result_data

            balance = 0
            for obj in list(coin_objects.data):
                balance += int(obj.balance)

            if denomination:
                return SuiBalance(
                    int=balance,
                    float=round(balance / 10 ** denomination, 2)
                )
            else:
                return SuiBalance(
                    int=balance,
                    float=round(balance / 10 ** SUI_DENOMINATION, 2)
                )
        except:
            if tries <= 5:
                time.sleep(3)
            else:
                logger.error(f'{str(sui_config.active_address)}: bad response from rpc, try to get a new one.')
                return SuiBalance(
                    int=0,
                    float=0
                )


def init_transaction(sui_config: SuiConfig, merge_gas_budget: bool = False) -> SyncTransaction:
    return SyncTransaction(
        client=SuiClient(sui_config),
        initial_sender=sui_config.active_address,
        merge_gas_budget=merge_gas_budget
    )


def build_and_execute_tx(sui_config: SuiConfig,
                         transaction: SyncTransaction,
                         gas_object: ObjectID = None) -> SuiTxResult:
    build = transaction.inspect_all()
    gas_used = build.effects.gas_used
    gas_budget = int((int(gas_used.computation_cost) + int(gas_used.non_refundable_storage_fee) +
                      abs(int(gas_used.storage_cost) - int(gas_used.storage_rebate))) * 1.1)

    if build.error:
        return SuiTxResult(
            address=str(sui_config.active_address),
            digest='',
            reason=build.error
        )
    else:
        try:
            if gas_object:
                rpc_result = transaction.execute(use_gas_object=gas_object, gas_budget=str(gas_budget))
            else:
                rpc_result = transaction.execute(gas_budget=str(gas_budget))
            if rpc_result.result_data:
                if rpc_result.result_data.status == 'success':
                    return SuiTxResult(
                        address=str(sui_config.active_address),
                        digest=rpc_result.result_data.digest
                    )
                else:
                    return SuiTxResult(
                        address=str(sui_config.active_address),
                        digest=rpc_result.result_data.digest,
                        reason=rpc_result.result_data.status
                    )
            else:
                return SuiTxResult(
                    address=str(sui_config.active_address),
                    digest='',
                    reason=str(rpc_result.result_string)
                )
        except Exception as e:
            logger.exception(e)


def independent_merge_sui_coins_tx(sui_config: SuiConfig):
    merge_results = []

    zero_coins, non_zero_coins, richest_coin = get_sui_coin_objects_for_merge(sui_config=sui_config)
    if len(zero_coins) and len(non_zero_coins):
        logger.info(f'{short_address(str(sui_config.active_address))} | trying to merge zero_coins.')
        transaction = init_transaction(sui_config=sui_config)
        transaction.merge_coins(merge_to=transaction.gas, merge_from=zero_coins)
        build_result = build_and_execute_tx(
            sui_config=sui_config,
            transaction=transaction,
            gas_object=ObjectID(richest_coin.object_id)
        )
        if build_result:
            merge_results.append(build_result)
            time.sleep(5)
        zero_coins, non_zero_coins, richest_coin = get_sui_coin_objects_for_merge(sui_config=sui_config)

    if len(non_zero_coins) > 1:
        logger.info(f'{short_address(str(sui_config.active_address))} | trying to merge non_zero_coins.')
        non_zero_coins.remove(richest_coin)

        transaction = init_transaction(sui_config=sui_config)
        transaction.merge_coins(merge_to=transaction.gas, merge_from=non_zero_coins)
        build_result = build_and_execute_tx(
            sui_config=sui_config,
            transaction=transaction,
            gas_object=ObjectID(richest_coin.object_id)
        )
        if build_result:
            merge_results.append(build_result)
            time.sleep(5)

    return merge_results


def get_pre_merged_tx(sui_config: SuiConfig, transaction: SyncTransaction) -> SuiTx:
    merge_count = 0

    zero_coins, non_zero_coins, richest_coin = get_sui_coin_objects_for_merge(sui_config=sui_config)
    if len(zero_coins) and len(non_zero_coins):
        merge_count += 1
        transaction.merge_coins(merge_to=transaction.gas, merge_from=zero_coins)
    if len(non_zero_coins) > 1:
        non_zero_coins.remove(richest_coin)
        merge_count += 1
        transaction.merge_coins(merge_to=transaction.gas, merge_from=non_zero_coins)

    return SuiTx(builder=transaction, gas=ObjectID(richest_coin.object_id), merge_count=merge_count)


def transfer_sui_tx(sui_config: SuiConfig, recipient: str, amount: SuiBalance) -> SuiTxResult:
    tx_object = get_pre_merged_tx(sui_config=sui_config, transaction=init_transaction(sui_config=sui_config))
    transaction = tx_object.builder

    transaction.transfer_sui(
        recipient=SuiAddress(recipient),
        from_coin=transaction.gas,
        amount=amount.int,
    )

    return build_and_execute_tx(sui_config=sui_config, transaction=transaction, gas_object=tx_object.gas)


def merge_sui_coins(sui_config: SuiConfig):
    try:
        results = independent_merge_sui_coins_tx(sui_config=sui_config)
        if results:
            for result in results:
                if result:
                    if result.reason:
                        logger.warning(f'{short_address(result.address)} | MERGE | digest: {result.digest} | '
                                       f'reason: {result.reason}.')
                    else:
                        logger.info(f'{short_address(result.address)} | MERGE | digest: {result.digest}.')
    except:
        pass


def get_sui_coin_objects_for_merge(sui_config: SuiConfig, coin_type: SuiString = None):
    if coin_type:
        gas_coin_objects: SuiCoinObjects = handle_result(SuiClient(sui_config).get_coin(
            coin_type=coin_type,
            address=sui_config.active_address,
            fetch_all=True)
        )
    else:
        gas_coin_objects: SuiCoinObjects = handle_result(SuiClient(sui_config).get_gas(sui_config.active_address,
                                                                                       fetch_all=True))
    zero_coins = [x for x in gas_coin_objects.data if int(x.balance) == 0]
    non_zero_coins = [x for x in gas_coin_objects.data if int(x.balance) > 0]

    richest_coin = max(non_zero_coins, key=lambda x: int(x.balance), default=None)
    return zero_coins, non_zero_coins, richest_coin


def claim_suins(sui_config: SuiConfig, nft_address: str):
    tx_object = get_pre_merged_tx(sui_config=sui_config, transaction=init_transaction(sui_config=sui_config))
    transaction = tx_object.builder

    move_call = transaction.move_call(
        target=SuiString(SUINS_CLAIM_TARGET),
        arguments=[ObjectID(nft_address)]
    )

    transaction.transfer_objects(
        transfers=[move_call],
        recipient=SuiAddress(str(sui_config.active_address))
    )
    return build_and_execute_tx(sui_config=sui_config, transaction=transaction,
                                gas_object=ObjectID(tx_object.gas.object_id))


def transfer_suins_tx(sui_config: SuiConfig, coin_obj: SuiCoinObject, recipient: str):
    tx_object = get_pre_merged_tx(sui_config=sui_config, transaction=init_transaction(sui_config=sui_config))
    transaction = tx_object.builder

    split = transaction.split_coin(
        coin=coin_obj,
        amounts=[int(coin_obj.balance)]
    )

    transaction.transfer_objects(
        transfers=[split],
        recipient=SuiAddress(recipient)
    )
    return build_and_execute_tx(sui_config=sui_config, transaction=transaction,
                                gas_object=ObjectID(tx_object.gas.object_id))


def get_suins_obj(sui_config: SuiConfig, coin_type: SuiString = SUINS_COIN_TYPE):
    client = SuiClient(config=sui_config)
    coin_objects: SuiCoinObjects = client.get_coin(coin_type=coin_type, address=sui_config.active_address,
                                                   fetch_all=True).result_data
    return coin_objects
