from web3 import Web3
from unittest import TestCase
from unittest.mock import patch
from src.services.helpers import contract
from tests import helper
from tests.mock_data import mock_relay_log
from tests.mock_data import mock_apply_relay_log
from tests.mock_data import mock_relay_transaction_receipt


class TestContract(TestCase):

    @patch('web3.eth.Account.signTransaction')
    @patch('web3.eth.Eth.sendRawTransaction')
    @patch('web3.eth.Eth.contract')
    def test_ok_apply_relay(self, mock_applyRelay,
                            mock_sendRawTransaction,
                            mock_signTransaction):
        provider = Web3.HTTPProvider('http://example.com')
        contract_address = helper.CHAIN_CONFIG['bridgeContractAddressTo']
        private_key = helper.PRIVATE_KEY
        sender = '0x' + 'a' * 40
        recipient = '0x' + 'b' * 40
        amount = 100
        tx_hash = '0x' + 'c' * 64
        gas = '5500000'
        gas_price = '1000000000'
        max_gas_price = '5000000000'
        nonce = 10
        web3 = Web3(provider)

        # Execute apply_relay
        contract.apply_relay(provider, contract_address, private_key,
                             sender, recipient, amount, tx_hash,
                             gas, gas_price, max_gas_price, nonce)

        # Assert call
        mock_applyRelay.return_value \
            .functions.applyRelay.assert_called_once_with(
                web3.toChecksumAddress(sender),
                web3.toChecksumAddress(recipient),
                amount,
                tx_hash
            )

        mock_applyRelay.return_value.functions \
            .applyRelay.return_value.buildTransaction.assert_called_once_with({
                'nonce': nonce,
                'gas': hex(int(gas)),
                'gasPrice': hex(int(gas_price))
            })

        mock_sendRawTransaction.assert_called()

    @patch('web3.eth.Account.signTransaction')
    @patch('web3.eth.Eth.sendRawTransaction')
    @patch('web3.eth.Eth.contract')
    @patch('web3.eth.Eth.gasPrice', 9999)
    def test_correct_gas_price_when_gas_price_not_specified(
            self, mock_contract, mock_sendRawTransaction,
            mock_signTransaction):
        gas = '5500000'
        nonce = 10

        # Execute apply_relay
        contract.apply_relay(
            Web3.HTTPProvider('http://example.com'),
            helper.CHAIN_CONFIG['bridgeContractAddressTo'],
            helper.PRIVATE_KEY,
            '0x' + 'a' * 40,
            '0x' + 'b' * 40,
            100,
            '0x' + 'c' * 64,
            gas,
            '',  # Gas Price
            '10000',  # Max Gas Price
            nonce)

        # Assert call
        mock_contract.return_value.functions \
            .applyRelay.return_value.buildTransaction.assert_called_once_with({
                'nonce': nonce,
                'gas': hex(int(gas)),
                'gasPrice': hex(9999)
            })

    @patch('web3.eth.Account.signTransaction')
    @patch('web3.eth.Eth.sendRawTransaction')
    @patch('web3.eth.Eth.contract')
    @patch('web3.eth.Eth.gasPrice', 10001)
    def test_correct_gas_price_when_gas_price_over_max_value(
            self, mock_contract, mock_sendRawTransaction,
            mock_signTransaction):
        gas = '5500000'
        nonce = 10

        # Execute apply_relay
        contract.apply_relay(
            Web3.HTTPProvider('http://example.com'),
            helper.CHAIN_CONFIG['bridgeContractAddressTo'],
            helper.PRIVATE_KEY,
            '0x' + 'a' * 40,
            '0x' + 'b' * 40,
            100,
            '0x' + 'c' * 64,
            gas,
            '',  # Gas Price
            '10000',  # Max Gas Price
            nonce)

        # Assert call
        mock_contract.return_value.functions \
            .applyRelay.return_value.buildTransaction.assert_called_once_with({
                'nonce': nonce,
                'gas': hex(int(gas)),
                'gasPrice': hex(10000)
            })

    @patch('web3.eth.Eth.getLogs')
    def test_ok_get_relay_event_logs(self, mock_getLogs):
        provider = Web3.HTTPProvider('http://example.com')
        web3 = Web3(provider)
        contract_address = '0x' + 'a' * 40
        from_block = 10
        to_block = 100

        # Execute get_relay_event_logs
        contract.get_relay_event_logs(
            provider,
            contract_address,
            from_block, to_block
        )

        # Assert call
        mock_getLogs.assert_called_with({
            'fromBlock': from_block, 'toBlock': to_block,
            'address': web3.toChecksumAddress(contract_address),
            'topics': [web3.sha3(
                text='Relay(address,address,uint256,uint256,uint256)').hex()]
        })

    @patch('web3.eth.Eth.getTransactionReceipt')
    def test_ok_get_relay_event_log_by_tx_hash(self,
                                               mock_getTransactionReceipt):
        provider = Web3.HTTPProvider('http://example.com')
        web3 = Web3(provider)

        # Setup mock
        mock_getTransactionReceipt.return_value \
            = mock_relay_transaction_receipt.data

        # Execute get_relay_event_log_by_tx_hash
        log = contract.get_relay_event_log_by_tx_hash(
            provider,
            mock_relay_transaction_receipt.data['transactionHash'].hex())

        # Assert return value
        self.assertEqual(log['topics'][0].hex(), web3.sha3(
            text='Relay(address,address,uint256,uint256,uint256)').hex())

    @patch('web3.eth.Eth.getLogs')
    def test_ok_get_apply_relay_event_logs(self, mock_getLogs):
        provider = Web3.HTTPProvider('http://example.com')
        web3 = Web3(provider)
        contract_address = '{:#042x}'.format(100)
        from_block = 10
        to_block = 100

        # Execute get_relay_event_logs
        contract.get_apply_relay_event_logs(
            provider,
            contract_address,
            from_block, to_block
        )

        # Assert call
        mock_getLogs.assert_called_with({
            'fromBlock': from_block, 'toBlock': to_block,
            'address': web3.toChecksumAddress(contract_address),
            'topics': [web3.sha3(
                text='ApplyRelay(address,address,uint256,bytes32)').hex()]
        })

    def test_ok_parse_relay_event_log(self):
        # Execute get_relay_event_logs
        parsed_log = contract.parse_relay_event_log(mock_relay_log.data[0])

        # Assert return value
        self.assertEqual(parsed_log, {
            "sender": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "recipient": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "amount": 10,
            "fee": 100,
            "timestamp": 0x5ca5a633,
            "txHash": ("0x85af52eb9d1420e2fb96e970da8945f1"
                       "66952927f16656427557b5cf0d890a09"),
            "blockNumber": 5337358
        })

    def test_ok_parse_apply_relay_event_log(self):
        # Execute get_relay_event_logs
        parsed_log = contract.parse_apply_relay_event_log(
            mock_apply_relay_log.data[0])

        # Assert return value
        self.assertEqual(parsed_log, {
            "relayTxHash": ("0x85af52eb9d1420e2fb96e970da8945f1"
                            "66952927f16656427557b5cf0d890a09")
        })
