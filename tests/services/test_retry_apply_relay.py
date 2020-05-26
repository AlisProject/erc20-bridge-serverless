from unittest import TestCase
from unittest.mock import patch, call, ANY
from src.services import retry_apply_relay
from tests import helper
from tests.mock_data import mock_relay_log


class TestRetryApplyRelay(TestCase):

    @patch('src.services.helpers.contract.get_relay_event_log_by_tx_hash')
    @patch('src.services.helpers.contract.apply_relay')
    @patch('web3.eth.Eth.getTransactionCount')
    def test_ok_retry_apply_relay(self, mock_get_transaction_count,
                                  mock_apply_relay,
                                  mock_get_relay_event_log_by_tx_hash):
        # Constants
        TRANSACTION_COUNT = 10

        # Setup mock
        mock_apply_relay.return_value = '0x' + 'a' * 64
        mock_get_transaction_count.return_value = TRANSACTION_COUNT

        def relay_event_log_side_effect(provider, hash):
            for log in mock_relay_log.data:
                if log['transactionHash'].hex() == hash:
                    return log
            return None
        mock_get_relay_event_log_by_tx_hash.side_effect \
            = relay_event_log_side_effect

        # Execute
        relay_transactions = [log['transactionHash'].hex()
                              for log in mock_relay_log.data]
        retry_apply_relay.execute(
            helper.CHAIN_CONFIG, helper.PRIVATE_KEY, relay_transactions)

        # Assert call count
        self.assertEqual(
            mock_apply_relay.call_count, len(mock_relay_log.data))

        # Assert parameters
        nonce = TRANSACTION_COUNT
        apply_relay_calls = []
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
