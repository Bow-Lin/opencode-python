"""
Unit tests for LSP Transport class
"""

import json
import subprocess
import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from core.lsp.transport import Transport


class TestTransport:
    """Test cases for Transport class"""

    def _mock_thread_constructor(self):
        """Helper method to create a mock thread constructor that actually runs the target function"""

        def mock_thread_constructor(target=None, daemon=None):
            mock_thread_instance = Mock()
            # Actually run the target function to simulate thread execution
            if target:
                target()
            mock_thread_instance.is_alive.return_value = False
            return mock_thread_instance

        return mock_thread_constructor

    def test_init(self):
        """Test Transport initialization"""
        server_command = ["test-server", "--stdio"]
        transport = Transport(server_command)

        assert transport.server_command == server_command
        assert transport.process is None
        assert transport.request_id == 0
        assert transport.logger is not None

    @patch("subprocess.Popen")
    def test_start_success(self, mock_popen):
        """Test successful server start"""
        mock_process = Mock()
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        result = transport.start()

        assert result is True
        assert transport.process == mock_process
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_start_failure(self, mock_popen):
        """Test failed server start"""
        mock_popen.side_effect = Exception("Process start failed")

        transport = Transport(["test-server"])
        result = transport.start()

        assert result is False
        assert transport.process is None

    def test_stop_no_process(self):
        """Test stop when no process is running"""
        transport = Transport(["test-server"])
        transport.stop()  # Should not raise any exception

    @patch("subprocess.Popen")
    def test_stop_with_process(self, mock_popen):
        """Test stop with running process"""
        mock_process = Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()
        transport.stop()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)

    @patch("subprocess.Popen")
    def test_stop_with_timeout(self, mock_popen):
        """Test stop with process timeout"""
        mock_process = Mock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 5)
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()
        transport.stop()

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    @patch("subprocess.Popen")
    def test_send_request_no_process(self, mock_popen):
        """Test send_request when no process is running"""
        transport = Transport(["test-server"])
        result = transport.send_request("test_method", {"param": "value"})

        assert result is None

    @patch("subprocess.Popen")
    def test_send_request_success(self, mock_popen):
        """Test successful request sending"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock the response reading
        with patch.object(Transport, "_read_response") as mock_read:
            mock_read.return_value = {"result": "success"}

            transport = Transport(["test-server"])
            transport.start()
            result = transport.send_request("test_method", {"param": "value"})

            assert result == {"result": "success"}
            assert transport.request_id == 1
            mock_process.stdin.write.assert_called()
            mock_process.stdin.flush.assert_called()

    @patch("subprocess.Popen")
    def test_send_notification_no_process(self, mock_popen):
        """Test send_notification when no process is running"""
        transport = Transport(["test-server"])
        transport.send_notification("test_method", {"param": "value"})
        # Should not raise any exception

    @patch("subprocess.Popen")
    def test_send_notification_success(self, mock_popen):
        """Test successful notification sending"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()
        transport.send_notification("test_method", {"param": "value"})

        mock_process.stdin.write.assert_called()
        mock_process.stdin.flush.assert_called()

    # @patch("subprocess.Popen")
    # def test_read_response_success(self, mock_popen):
    #     """Test successful response reading"""
    #     mock_process = Mock()
    #     mock_process.stdout = Mock()
    #     mock_popen.return_value = mock_process

    #     # Mock the response data
    #     response_data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
    #     response_json = json.dumps(response_data)
    #     response_content = (
    #         f"Content-Length: {len(response_json)}\r\n\r\n{response_json}"
    #     ).encode("utf-8")

    #     # Mock read to return the binary content in chunks
    #     mock_process.stdout.read.side_effect = [
    #         response_content,  # First read returns the full content
    #         b"",  # Subsequent reads return empty
    #     ]

    #     transport = Transport(["test-server"])
    #     transport.start()

    #     with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
    #         result = transport._read_response()

    #         assert result == response_data
    @patch("subprocess.Popen")
    def test_read_response_success(self, mock_popen):
        mock_process = Mock()
        mock_stdout = Mock()

        mock_stdout.read.side_effect = [
            b"Content-Length: 38\r\n",
            b"\r\n",
            b'{"jsonrpc":"2.0","id":1,"result":"ok"}',
        ]

        mock_process.stdout = mock_stdout
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            result = transport._read_response()
            assert result["result"] == "ok"

    @patch("subprocess.Popen")
    def test_read_response_timeout(self, mock_popen):
        """Test response reading timeout"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()

        # Create a custom thread constructor that keeps thread alive to simulate timeout
        def mock_thread_constructor_timeout(target=None, daemon=None):
            mock_thread_instance = Mock()
            # Don't run the target function to simulate timeout
            mock_thread_instance.is_alive.return_value = True
            return mock_thread_instance

        with patch("threading.Thread", side_effect=mock_thread_constructor_timeout):
            result = transport._read_response()

            assert result is None

    @patch("subprocess.Popen")
    def test_read_response_error(self, mock_popen):
        """Test response reading with error"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock read to raise an exception
        mock_process.stdout.read.side_effect = Exception("Read error")

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            result = transport._read_response()

            assert result is None

    def test_request_id_increment(self):
        """Test that request_id increments properly"""
        transport = Transport(["test-server"])

        assert transport.request_id == 0

        # Simulate sending requests
        transport.request_id += 1
        assert transport.request_id == 1

        transport.request_id += 1
        assert transport.request_id == 2

    @patch("subprocess.Popen")
    def test_json_rpc_format(self, mock_popen):
        """Test that requests are formatted correctly as JSON-RPC"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()

        with patch.object(Transport, "_read_response") as mock_read:
            mock_read.return_value = {"result": "success"}

            transport.send_request("test_method", {"param": "value"})

            # Verify the request was written to stdin
            mock_process.stdin.write.assert_called()
            call_args = mock_process.stdin.write.call_args[0][0]

            # Check that it contains the expected JSON-RPC format (binary data)
            call_args_str = call_args.decode("utf-8")
            assert "Content-Length:" in call_args_str
            assert "jsonrpc" in call_args_str
            assert "test_method" in call_args_str
            assert "param" in call_args_str

    @patch("subprocess.Popen")
    def test_notification_format(self, mock_popen):
        """Test that notifications are formatted correctly"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()

        transport.send_notification("test_notification", {"param": "value"})

        # Verify the notification was written to stdin
        mock_process.stdin.write.assert_called()
        call_args = mock_process.stdin.write.call_args[0][0]

        # Check that it contains the expected format (no id field for notifications)
        call_args_str = call_args.decode("utf-8")
        assert "Content-Length:" in call_args_str
        assert "jsonrpc" in call_args_str
        assert "test_notification" in call_args_str
        assert "param" in call_args_str
        # Notifications should not have an "id" field
        assert "id" not in call_args_str

    @patch("subprocess.Popen")
    def test_send_request_with_params(self, mock_popen):
        """Test send_request with various parameter types"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        with patch.object(Transport, "_read_response") as mock_read:
            mock_read.return_value = {"result": "success"}

            transport = Transport(["test-server"])
            transport.start()

            # Test with different parameter types
            test_params = {
                "string": "test",
                "number": 42,
                "boolean": True,
                "list": [1, 2, 3],
                "dict": {"key": "value"},
                "null": None,
            }

            result = transport.send_request("test_method", test_params)

            assert result == {"result": "success"}
            mock_process.stdin.write.assert_called()
            call_args = mock_process.stdin.write.call_args[0][0]

            # Verify all parameter types are included
            call_args_str = call_args.decode("utf-8")
            for key, value in test_params.items():
                if value is not None:
                    assert str(value) in call_args_str or key in call_args_str

    @patch("subprocess.Popen")
    def test_send_request_without_params(self, mock_popen):
        """Test send_request without parameters"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        with patch.object(Transport, "_read_response") as mock_read:
            mock_read.return_value = {"result": "success"}

            transport = Transport(["test-server"])
            transport.start()

            result = transport.send_request("test_method")

            assert result == {"result": "success"}
            mock_process.stdin.write.assert_called()
            call_args = mock_process.stdin.write.call_args[0][0]

            # Should still contain the method name
            call_args_str = call_args.decode("utf-8")
            assert "test_method" in call_args_str

    @patch("subprocess.Popen")
    def test_multiple_requests(self, mock_popen):
        """Test sending multiple requests and verify request_id increments"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        with patch.object(Transport, "_read_response") as mock_read:
            mock_read.return_value = {"result": "success"}

            transport = Transport(["test-server"])
            transport.start()

            # Send multiple requests
            for i in range(3):
                result = transport.send_request(f"method_{i}")
                assert result == {"result": "success"}
                assert transport.request_id == i + 1

            # Verify request_id is 3 after 3 requests
            assert transport.request_id == 3

    @patch("subprocess.Popen")
    def test_process_error_handling(self, mock_popen):
        """Test error handling when process operations fail"""
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdin.write.side_effect = Exception("Write failed")
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()

        # Should handle write errors gracefully
        result = transport.send_request("test_method")
        assert result is None

    @patch("subprocess.Popen")
    def test_stop_with_exception(self, mock_popen):
        """Test stop method handles exceptions gracefully"""
        mock_process = Mock()
        mock_process.terminate.side_effect = Exception("Terminate failed")
        mock_popen.return_value = mock_process

        transport = Transport(["test-server"])
        transport.start()

        # Should handle terminate errors gracefully
        transport.stop()
        # Should not raise an exception

    @patch("subprocess.Popen")
    def test_read_response_binary_mode(self, mock_popen):
        """Test response reading in binary mode with chunked data"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock the response data
        response_data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        response_json = json.dumps(response_data)

        # Create binary content with headers and body
        header = f"Content-Length: {len(response_json)}\r\n\r\n"
        full_content = (header + response_json).encode("utf-8")

        # Mock read to return content in chunks
        mock_process.stdout.read.side_effect = [
            full_content[:50],  # First chunk
            full_content[50:],  # Second chunk
            b"",  # Empty for subsequent reads
        ]

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            result = transport._read_response()

            assert result == response_data

    @patch("subprocess.Popen")
    def test_read_response_connection_closed(self, mock_popen):
        """Test response reading when connection is closed"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock read to return empty (connection closed)
        mock_process.stdout.read.return_value = b""

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            result = transport._read_response()

            assert result is None

    @patch("subprocess.Popen")
    def test_read_response_missing_content_length(self, mock_popen):
        """Test response reading with missing Content-Length header"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock response with missing Content-Length
        response_content = b"Content-Type: application/json\r\n\r\n"

        mock_process.stdout.read.side_effect = [response_content, b""]

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            result = transport._read_response()

            assert result is None

    @patch("subprocess.Popen")
    def test_read_response_invalid_json(self, mock_popen):
        """Test response reading with invalid JSON content"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock response with invalid JSON
        response_content = b"Content-Length: 10\r\n\r\n{invalid}"

        mock_process.stdout.read.side_effect = [response_content, b""]

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            result = transport._read_response()

            assert result is None

    @patch("subprocess.Popen")
    def test_read_response_unicode_content(self, mock_popen):
        """Test response reading with Unicode content"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock response with Unicode content
        response_data = {"jsonrpc": "2.0", "id": 1, "result": "中文测试"}
        response_json = json.dumps(response_data, ensure_ascii=False)

        header = f"Content-Length: {len(response_json.encode('utf-8'))}\r\n\r\n"
        full_content = (header + response_json).encode("utf-8")

        mock_process.stdout.read.side_effect = [full_content, b""]

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            result = transport._read_response()

            assert result == response_data

    @patch("subprocess.Popen")
    def test_read_response_with_select(self, mock_popen):
        """Test response reading with select support"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock response data
        response_data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        response_json = json.dumps(response_data)
        header = f"Content-Length: {len(response_json)}\r\n\r\n"
        full_content = (header + response_json).encode("utf-8")

        # Mock read to return content in chunks
        mock_process.stdout.read.side_effect = [
            full_content[:30],  # First chunk
            full_content[30:],  # Second chunk
            b"",  # Empty for subsequent reads
        ]

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            # Mock select to return ready
            with patch("select.select") as mock_select:
                mock_select.return_value = ([mock_process.stdout], [], [])

                result = transport._read_response()

                assert result == response_data

    @patch("subprocess.Popen")
    def test_read_response_select_timeout(self, mock_popen):
        """Test response reading with select timeout"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock read to return content eventually
        response_data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        response_json = json.dumps(response_data)
        header = f"Content-Length: {len(response_json)}\r\n\r\n"
        full_content = (header + response_json).encode("utf-8")

        mock_process.stdout.read.side_effect = [full_content, b""]

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            # Mock select to return not ready initially, then ready
            with patch("select.select") as mock_select:
                mock_select.side_effect = [
                    ([], [], []),  # First call: not ready
                    ([mock_process.stdout], [], []),  # Second call: ready
                ]

                result = transport._read_response()

                assert result == response_data

    @patch("subprocess.Popen")
    def test_read_response_header_timeout(self, mock_popen):
        """Test response reading timeout while reading header"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock read to return empty (no data available)
        mock_process.stdout.read.return_value = b""

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            # Mock time.time to simulate timeout
            with patch("time.time") as mock_time:
                mock_time.side_effect = [
                    0,
                    11,
                    12,
                    13,
                ]  # Start time, then timeout, and more calls

                result = transport._read_response()

                assert result is None

    @patch("subprocess.Popen")
    def test_read_response_content_timeout(self, mock_popen):
        """Test response reading timeout while reading content"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_popen.return_value = mock_process

        # Mock response with partial content
        response_data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        response_json = json.dumps(response_data)
        header = f"Content-Length: {len(response_json)}\r\n\r\n"
        partial_content = (header + response_json[:10]).encode(
            "utf-8"
        )  # Partial content

        mock_process.stdout.read.side_effect = [
            partial_content,  # Header + partial content
            b"",  # No more data
        ]

        transport = Transport(["test-server"])
        transport.start()

        with patch("threading.Thread", side_effect=self._mock_thread_constructor()):
            # Mock time.time to simulate timeout during content reading
            with patch("time.time") as mock_time:
                mock_time.side_effect = [
                    0,
                    5,
                    11,
                    12,
                    13,
                ]  # Start, during content, timeout, and more calls

                result = transport._read_response()

                assert result is None
