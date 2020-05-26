import json
from web3 import Web3

# ABIの読み込み
with open('abi/Bridge.json', 'rt') as file:
    BRIDGE_ABI = json.loads(file.read())


def apply_relay(provider, contract_address, private_key, sender,
                recipient, amount, txHash, gas, gas_price, max_gas_price,
                nonce):
    """ applyRelayの実行
    """
    if BRIDGE_ABI is None:
        raise Exception("Bridge ABI parse error.")

    web3 = Web3(provider)

    contract = web3.eth.contract(
        web3.toChecksumAddress(contract_address), abi=BRIDGE_ABI)

    if len(gas_price) <= 0:
        gas_price = min(web3.eth.gasPrice, int(max_gas_price))

    transaction = contract.functions.applyRelay(
        web3.toChecksumAddress(sender),
        web3.toChecksumAddress(recipient),
        amount, txHash).buildTransaction({
            'nonce': nonce,
            'gas': hex(int(gas)),
            'gasPrice': hex(int(gas_price))
        })

    signed_transaction = web3.eth.account.signTransaction(
        transaction, private_key=private_key)

    return web3.eth.sendRawTransaction(
        signed_transaction.rawTransaction).hex()


def get_relay_event_logs(provider, contract_address,
                         from_block, to_block="latest"):
    """ Relayイベントの取得
    """
    web3 = Web3(provider)

    event_signature_hash = web3.sha3(
        text="Relay(address,address,uint256,uint256,uint256)").hex()

    return web3.eth.getLogs(
        {'fromBlock': from_block, 'toBlock': to_block,
         'address': web3.toChecksumAddress(contract_address),
         'topics': [event_signature_hash]})


def get_relay_event_log_by_tx_hash(provider, relay_transaction_hash):
    """ トランザクションハッシュを指定してRelayイベントを取得
    """
    web3 = Web3(provider)

    return web3.eth.getTransactionReceipt(
        relay_transaction_hash)['logs'][1]


def get_apply_relay_event_logs(provider, contract_address,
                               from_block, to_block="latest"):
    """ ApplyRelayイベントの取得
    """
    web3 = Web3(provider)

    event_signature_hash = web3.sha3(
        text="ApplyRelay(address,address,uint256,bytes32)").hex()

    return web3.eth.getLogs(
        {'fromBlock': from_block, 'toBlock': to_block,
         'address': web3.toChecksumAddress(contract_address),
         'topics': [event_signature_hash]})


def parse_relay_event_log(relay_event_log):
    """ Relayイベントのパース
    """
    return {
        "sender": "0x" + relay_event_log['topics'][1].hex()[-40:],
        "recipient": "0x" + relay_event_log['topics'][2].hex()[-40:],
        "amount": int(relay_event_log['data'][2:66], 16),
        "fee": int(relay_event_log['data'][66:130], 16),
        "timestamp": int(relay_event_log['data'][130:194], 16),
        "txHash": relay_event_log['transactionHash'].hex(),
        "blockNumber": relay_event_log['blockNumber']
    }


def parse_apply_relay_event_log(apply_relay_event_log):
    """ ApplyRelayイベントのパース
    """
    return {
        "relayTxHash": "0x" + apply_relay_event_log['data'][-64:]
    }
