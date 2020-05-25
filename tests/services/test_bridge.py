from unittest import TestCase
from unittest.mock import patch, call, ANY
from src.services import bridge
from tests import helper
from tests.mock_data import mock_relay_log


class TestBridge(TestCase):
    def setUp(self):
        self.db_table = helper.create_erc20_bridge_info_db_table()

    def tearDown(self):
        self.db_table.delete()

    @patch('src.services.helpers.contract.get_relay_event_logs')
    @patch('src.services.helpers.contract.apply_relay')
    @patch('src.services.bridge._get_latest_block_number')
    @patch('web3.eth.Eth.getTransactionCount')
    def test_ok_bridge(self, mock_get_transaction_count,
                       mock_get_latest_block_number,
                       mock_apply_relay,
                       mock_get_relay_event_logs):

        # constants
        LATEST_BLOCK_NUMBER = 100000
        TRANSACTION_COUNT = 10

        # Setup mock
        mock_get_relay_event_logs.return_value = mock_relay_log.data
        mock_apply_relay.return_value = '0x' + 'a' * 64
        mock_get_latest_block_number.return_value = LATEST_BLOCK_NUMBER
        mock_get_transaction_count.return_value = TRANSACTION_COUNT

        # Execute
        bridge.execute(helper.CHAIN_CONFIG, self.db_table, helper.PRIVATE_KEY)

        # Assert call count
        self.assertEqual(mock_apply_relay.call_count,
                         len(mock_relay_log.data))

        # Assert parameters
        apply_relay_calls = []
        nonce = TRANSACTION_COUNT
        for relay_event_log in mock_relay_log.data:
            apply_relay_calls.append(call(
                ANY,
                helper.CHAIN_CONFIG['bridgeContractAddressTo'],
                helper.PRIVATE_KEY,
                "0x" + relay_event_log['topics'][1].hex()[-40:],
                "0x" + relay_event_log['topics'][2].hex()[-40:],
                int(relay_event_log['data'][2:66], 16),
                relay_event_log['transactionHash'].hex(),
                helper.CHAIN_CONFIG['gas'], helper.CHAIN_CONFIG['gasPrice'],
                helper.CHAIN_CONFIG['maxGasPrice'],
                nonce
            ))
            nonce += 1

        mock_apply_relay.assert_has_calls(apply_relay_calls)

        # Assert DynamoDB's value
        get_item_result = self.db_table.get_item(Key={
            'key': "deposit_offset"
        })
        self.assertEqual(
            int(get_item_result['Item']['value']), LATEST_BLOCK_NUMBER + 1)

    @patch('src.services.helpers.contract.get_relay_event_logs')
    @patch('src.services.helpers.contract.apply_relay')
    @patch('src.services.bridge._get_latest_block_number')
    @patch('web3.eth.Eth.getTransactionCount')
    def test_ok_bridge_when_block_offset_is_not_zero(
            self,
            mock_get_transaction_count,
            mock_get_latest_block_number,
            mock_apply_relay,
            mock_get_relay_event_logs):

        # constants
        LATEST_BLOCK_NUMBER = 100000
        TRANSACTION_COUNT = 10

        # Setup mock
        mock_get_relay_event_logs.return_value = mock_relay_log.data
        mock_apply_relay.return_value = '0x' + 'a' * 64
        mock_get_latest_block_number.return_value = LATEST_BLOCK_NUMBER
        mock_get_transaction_count.return_value = TRANSACTION_COUNT

        # Setup dynamodb
        self.db_table.put_item(Item={
            "key": 'deposit_offset',
            "value": 1000
        })

        # Execute
        bridge.execute(helper.CHAIN_CONFIG, self.db_table, helper.PRIVATE_KEY)

        # Assert call count
        self.assertEqual(mock_apply_relay.call_count,
                         len(mock_relay_log.data))

        # Assert parameters
        apply_relay_calls = []
        nonce = TRANSACTION_COUNT
        for relay_event_log in mock_relay_log.data:
            apply_relay_calls.append(call(
                ANY,
                helper.CHAIN_CONFIG['bridgeContractAddressTo'],
                helper.PRIVATE_KEY,
                "0x" + relay_event_log['topics'][1].hex()[-40:],
                "0x" + relay_event_log['topics'][2].hex()[-40:],
                int(relay_event_log['data'][2:66], 16),
                relay_event_log['transactionHash'].hex(),
                helper.CHAIN_CONFIG['gas'], helper.CHAIN_CONFIG['gasPrice'],
                helper.CHAIN_CONFIG['maxGasPrice'],
                nonce
            ))
            nonce += 1

        mock_apply_relay.assert_has_calls(apply_relay_calls)

        # Assert DynamoDB's value
        get_item_result = self.db_table.get_item(Key={
            'key': "deposit_offset"
        })
        self.assertEqual(
            int(get_item_result['Item']['value']), LATEST_BLOCK_NUMBER + 1)

    @patch('src.services.helpers.contract.get_relay_event_logs')
    @patch('src.services.helpers.contract.apply_relay')
    @patch('src.services.bridge._get_latest_block_number')
    @patch('web3.eth.Eth.getTransactionCount')
    def test_ok_bridge_when_latest_block_was_already_processed(
            self,
            mock_get_transaction_count,
            mock_get_latest_block_number,
            mock_apply_relay,
            mock_get_relay_event_logs):

        # constants
        LATEST_BLOCK_NUMBER = 100000
        TRANSACTION_COUNT = 10

        # Setup mock
        mock_get_relay_event_logs.return_value = mock_relay_log.data
        mock_apply_relay.return_value = '0x' + 'a' * 64
        mock_get_latest_block_number.return_value = LATEST_BLOCK_NUMBER
        mock_get_transaction_count.return_value = TRANSACTION_COUNT

        # Setup dynamodb
        self.db_table.put_item(Item={
            "key": 'deposit_offset',
            "value": LATEST_BLOCK_NUMBER + 1
        })

        # Execute
        bridge.execute(helper.CHAIN_CONFIG, self.db_table, helper.PRIVATE_KEY)

        # Assert call count
        self.assertEqual(mock_apply_relay.call_count, 0)

        # Assert DynamoDB's value
        get_item_result = self.db_table.get_item(Key={
            'key': "deposit_offset"
        })
        self.assertEqual(
            int(get_item_result['Item']['value']), LATEST_BLOCK_NUMBER + 1)

    def test_ok_get_block_offset_key(self):
        deposit_block_offset = bridge._get_block_offset_key(True)
        self.assertEqual(deposit_block_offset, 'deposit_offset')

        withdraw_block_offset = bridge._get_block_offset_key(False)
        self.assertEqual(withdraw_block_offset, 'withdraw_offset')
