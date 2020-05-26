from web3 import Web3
from eth_account import Account
from src.services.helpers import contract
from src.services.helpers.logger import logger


def execute(chain_config, dynamo_table, private_key):
    """ 入出金処理の実行
    """
    # Web3プロバイダーの生成
    provider_from = Web3.HTTPProvider(chain_config['chainRpcUrlFrom'])
    provider_to = Web3.HTTPProvider(chain_config['chainRpcUrlTo'])

    # 処理を開始するブロックのオフセットを取得
    relay_block_offset = _get_block_offset(
        chain_config['isDeposit'], dynamo_table)

    # 最新のブロック数を取得
    latest_block_num = _get_latest_block_number(provider_from)

    if latest_block_num < relay_block_offset:
        # 最新のブロックを処理済み
        logger.info('There is no more block. '
                    'latestBlockNum={latest_block_num}, '
                    'blockOffset={relay_block_offset}'
                    .format(latest_block_num=latest_block_num,
                            relay_block_offset=relay_block_offset))
        return

    # nonce設定のためトランザクション数の取得
    nonce = _get_transaction_count(
        provider_to, Account.privateKeyToAccount(private_key).address)

    # Relayイベントを取得
    relay_event_logs = contract.get_relay_event_logs(
        provider_from,
        chain_config['bridgeContractAddressFrom'],
        relay_block_offset,
        latest_block_num)

    logger.info('---------- {num} Relay events '
                'from block {fromBlock} to {toBlock} ----------'
                .format(num=len(relay_event_logs),
                        fromBlock=relay_block_offset,
                        toBlock=latest_block_num))

    # 各Relayイベントに対して、applyRelay処理を実行
    for relay_event_log in relay_event_logs:
        parsed_event = contract.parse_relay_event_log(relay_event_log)
        logger.info(
            '[RelayEvent] timestamp={timestamp}, blockNum={blockNumber}, '
            'txHash={txHash}, sender={sender}, recipient={recipient}, '
            'amount={amount}, fee={fee}'
            .format(**parsed_event))

        try:
            # applyRelay処理を実行
            response = contract.apply_relay(
                provider_to,
                chain_config['bridgeContractAddressTo'],
                private_key,
                parsed_event['sender'],
                parsed_event['recipient'],
                parsed_event['amount'],
                parsed_event['txHash'],
                chain_config['gas'],
                chain_config['gasPrice'],
                chain_config['maxGasPrice'],
                nonce)

            # nonceのカウントアップ
            nonce += 1

            logger.info(
                '[ApplyRelay] txHash={txHash}, '
                'relayEventTxHash={relayEventTxHash}'
                .format(txHash=response,
                        relayEventTxHash=parsed_event['txHash']))
        except Exception as e:
            logger.error('[ApplyRelay] failed. error={error}'.format(error=e))
            continue

    logger.info('Finished.')

    # 次の入出金処理を開始する際のブロックのオフセットを更新
    _update_block_offset(
        chain_config['isDeposit'], dynamo_table, latest_block_num + 1)


def _get_transaction_count(provider, account):
    """ トランザクション数の取得
    """
    web3 = Web3(provider)
    return web3.eth.getTransactionCount(web3.toChecksumAddress(account))


def _get_latest_block_number(provider):
    """ 最新のブロック数の取得
    """
    web3 = Web3(provider)
    return web3.eth.blockNumber


def _get_block_offset(is_deposit, table):
    """ 入出金を開始するブロックのオフセットの取得
    """
    result = table.get_item(Key={
        'key': _get_block_offset_key(is_deposit)
    })

    if result is None or 'Item' not in result:
        return 0

    return int(result['Item']['value'])


def _update_block_offset(is_deposit, table, offset):
    """ 入出金を開始するブロックのオフセットの更新
    """
    table.put_item(Item={
        "key": _get_block_offset_key(is_deposit),
        "value": int(offset)
    })


def _get_block_offset_key(is_deposit):
    """ ブロックオフセットのテーブルのキーの取得
    """
    if is_deposit:
        # 入金時
        return "deposit_offset"
    else:
        # 出金時
        return "withdraw_offset"
