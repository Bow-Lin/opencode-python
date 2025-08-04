"""
LSP transport layer for JSON-RPC communication.
"""

import json
import logging
import subprocess
from typing import Any, Dict, Optional


class Transport:
    """LSP transport layer for JSON-RPC communication."""

    def __init__(self, server_command: list[str]):
        self.server_command = server_command
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.logger = logging.getLogger(__name__)

    def start(self) -> bool:
        """Start the language server process."""
        try:
            # On Windows, use shell=True for commands with arguments
            import platform

            use_shell = platform.system() == "Windows"

            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                shell=use_shell,
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to start language server: {e}")
            return False

    def stop(self):
        """Stop the language server process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                self.logger.error(f"Error stopping server: {e}")

    def send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Send a request to the language server."""
        if not self.process:
            return None

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params,
        }

        try:
            # Send request
            request_json = json.dumps(request)
            self.process.stdin.write(
                f"Content-Length: {len(request_json)}\r\n\r\n{request_json}"
            )
            self.process.stdin.flush()

            # Read response
            response = self._read_response()
            return response
        except Exception as e:
            self.logger.error(f"Error sending request: {e}")
            return None

    def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Send a notification to the language server."""
        if not self.process:
            return

        notification = {"jsonrpc": "2.0", "method": method, "params": params}
        try:
            notification_json = json.dumps(notification)
            self.process.stdin.write(
                f"Content-Length: {len(notification_json)}\r\n\r\n{notification_json}"
            )
            self.process.stdin.flush()
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

    def _read_response(self) -> Optional[Dict[str, Any]]:
        """Read response from the language server."""
        if not self.process:
            return None

        try:
            import threading
            import time

            # Use a timeout mechanism
            response_data = [None]
            error_data = [None]

            def read_response_thread():
                try:
                    # Read headers
                    headers = {}
                    while True:
                        line = self.process.stdout.readline().strip()
                        if not line:
                            break
                        if ":" in line:
                            key, value = line.split(":", 1)
                            headers[key.strip()] = value.strip()

                    # Read content
                    content_length = int(headers.get("Content-Length", 0))
                    if content_length > 0:
                        content = self.process.stdout.read(content_length)
                        response_data[0] = json.loads(content)
                except Exception as e:
                    error_data[0] = e

            # Start reading in a separate thread
            thread = threading.Thread(target=read_response_thread)
            thread.daemon = True
            thread.start()

            # Wait for response with timeout
            timeout = 10.0  # 10 seconds timeout
            start_time = time.time()

            while thread.is_alive() and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if thread.is_alive():
                self.logger.warning("Timeout waiting for response from language server")
                return None

            if error_data[0]:
                raise error_data[0]

            return response_data[0]

        except Exception as e:
            self.logger.error(f"Error reading response: {e}")

        return None
