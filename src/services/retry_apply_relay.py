from web3 import Web3
from eth_account import Account
from src.services.helpers import contract
from src.services.helpers.logger import logger


def execute(chain_config, private_key, relay_transactions):
    """ Relayイベントのトランザクションハッシュを指定して入出金処理を実行(未完了の入出金処理をリトライする際に利用)
    """
    # Web3プロバイダーの生成
    provider_from = Web3.HTTPProvider(chain_config['chainRpcUrlFrom'])
    provider_to = Web3.HTTPProvider(chain_config['chainRpcUrlTo'])

    # nonce設定のためトランザクション数の取得
    nonce = _get_transaction_count(
        provider_to, Account.privateKeyToAccount(private_key).address)

    # 各Relayイベントに対して、applyRelay処理を実行
    for relay_transaction in relay_transactions:
        # トランザクションハッシュからRelayイベントを取得
        relay_event_log = contract.get_relay_event_log_by_tx_hash(
            provider_from, relay_transaction)

        parsed_event = contract.parse_relay_event_log(relay_event_log)

        logger.info(
            '[RelayEvent] timestamp={timestamp}, blockNum={blockNumber}, '
            'txHash={txHash}, sender={sender}, recipient={recipient}, '
            'amount={amount}, fee={fee}'
            .format(**parsed_event))

        try:
            # applyRelay処理を実行
            response = contract.apply_relay(
                provider_to, chain_config['bridgeContractAddressTo'],
                private_key,
                parsed_event['sender'], parsed_event['recipient'],
                parsed_event['amount'], parsed_event['txHash'],
                chain_config['gas'], chain_config['gasPrice'],
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

    logger.info('Finished')


def _get_transaction_count(provider, account):
    """ トランザクション数の取得
    """
    web3 = Web3(provider)
    return web3.eth.getTransactionCount(web3.toChecksumAddress(account))
