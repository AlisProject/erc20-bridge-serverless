import os
from unittest.mock import patch
from unittest import TestCase
from src.handlers.helpers import helper

os.environ['ALIS_APP_ID'] = 'test'


class TestHelper(TestCase):
    def test_ok_load_chain_config(self):
        os.environ['PUBLIC_CHAIN_RPC_URL'] = 'http://example1.com'
        os.environ['PUBLIC_CHAIN_BRIDGE_CONTRACT_ADDRESS'] = '0x' + 'a' * 40
        os.environ['PUBLIC_CHAIN_GAS'] = '100'
        os.environ['PUBLIC_CHAIN_GAS_PRICE'] = '10000'
        os.environ['PUBLIC_CHAIN_MAX_GAS_PRICE'] = '50000'
        os.environ['PRIVATE_CHAIN_RPC_URL'] = 'http://example2.com'
        os.environ['PRIVATE_CHAIN_BRIDGE_CONTRACT_ADDRESS'] = '0x' + 'b' * 40
        os.environ['PRIVATE_CHAIN_GAS'] = '200'
        os.environ['PRIVATE_CHAIN_GAS_PRICE'] = '20000'
        os.environ['PRIVATE_CHAIN_MAX_GAS_PRICE'] = '60000'

        # Execute load_chain_config (for Deposit)
        deposit_config = helper.load_chain_config(True)

        # Assert return value
        self.assertEqual(deposit_config, {
            'isDeposit': True,
            'chainRpcUrlFrom': os.environ['PUBLIC_CHAIN_RPC_URL'],
            'bridgeContractAddressFrom':
                os.environ['PUBLIC_CHAIN_BRIDGE_CONTRACT_ADDRESS'],
            'chainRpcUrlTo': os.environ['PRIVATE_CHAIN_RPC_URL'],
            'bridgeContractAddressTo':
                os.environ['PRIVATE_CHAIN_BRIDGE_CONTRACT_ADDRESS'],
            'gas': os.environ['PRIVATE_CHAIN_GAS'],
            'gasPrice': os.environ['PRIVATE_CHAIN_GAS_PRICE'],
            'maxGasPrice': os.environ['PRIVATE_CHAIN_MAX_GAS_PRICE']
        })

        # Execute load_chain_config (for Withdraw)
        withdraw_config = helper.load_chain_config(False)

        # Assert return value
        self.assertEqual(withdraw_config, {
            'isDeposit': False,
            'chainRpcUrlFrom': os.environ['PRIVATE_CHAIN_RPC_URL'],
            'bridgeContractAddressFrom':
                os.environ['PRIVATE_CHAIN_BRIDGE_CONTRACT_ADDRESS'],
            'chainRpcUrlTo': os.environ['PUBLIC_CHAIN_RPC_URL'],
            'bridgeContractAddressTo':
                os.environ['PUBLIC_CHAIN_BRIDGE_CONTRACT_ADDRESS'],
            'gas': os.environ['PUBLIC_CHAIN_GAS'],
            'gasPrice': os.environ['PUBLIC_CHAIN_GAS_PRICE'],
            'maxGasPrice': os.environ['PUBLIC_CHAIN_MAX_GAS_PRICE']
        })

    @patch('boto3.client')
    def test_ok_get_private_key_deposit(self, mock_client):
        private_key = '0x' + 'a' * 64

        # Setup mock
        mock_client.return_value.get_parameter.return_value = {
            'Parameter': {
                'Value': private_key
            }
        }

        # Execute get_private_key
        result = helper.get_private_key(True)

        # Assert return value
        self.assertEqual(result, private_key)

        # Assert call
        mock_client.return_value.get_parameter.assert_called_with(
            Name='testssmBridgeOperatorPrivateChainPrivateKey',
            WithDecryption=True
        )

    @patch('boto3.client')
    def test_ok_get_private_key_withdraw(self, mock_client):
        private_key = '0x' + 'a' * 64

        # Setup mock
        mock_client.return_value.get_parameter.return_value = {
            'Parameter': {
                'Value': private_key
            }
        }

        # Execute get_private_key
        result = helper.get_private_key(False)

        # Assert return value
        self.assertEqual(result, private_key)

        # Assert call
        mock_client.return_value.get_parameter.assert_called_with(
            Name='testssmBridgeOperatorPublicChainPrivateKey',
            WithDecryption=True
        )
