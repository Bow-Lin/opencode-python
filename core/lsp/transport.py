"""
LSP transport layer for JSON-RPC communication.
"""

import json
import logging
import select
import subprocess
import sys
import time
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
            print(f"use_shell: {use_shell}")
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                bufsize=0,
                shell=use_shell,
            )

            # Check if process started successfully
            if self.process.poll() is not None:
                # Process has already terminated
                stderr_output = self.process.stderr.read()
                print(
                    f"❌ Process failed to start. Exit code: {self.process.returncode}"
                )
                print(f"❌ stderr: {stderr_output}")
                return False

            print(f"✅ Process started with PID: {self.process.pid}")
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
        if not self.process:
            return None

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }

        try:
            message = json.dumps(request)
            content = f"Content-Length: {len(message.encode('utf-8'))}\r\n\r\n{message}"
            print(f"📤 Sending request: {method} (id: {self.request_id})")
            self.process.stdin.write(content.encode("utf-8"))
            self.process.stdin.flush()

            # 循环读取消息直到找到匹配的响应
            while True:
                msg = self._read_response()
                if not msg:
                    return None

                # 检查是否是我们要的响应
                if "id" in msg and msg["id"] == self.request_id:
                    print(f"📨 Got response for request {self.request_id}")
                    return msg
                else:
                    # 这是通知或其他响应，打印出来但继续等待
                    if "id" in msg:
                        print(f"📨 Got response for different request: {msg}")
                    else:
                        print(f"🔔 Got notification: {msg.get('method', 'unknown')}")
                        print(f"   Content: {json.dumps(msg, indent=2)}")

        except Exception as e:
            print(f"Error sending request: {e}")
            import traceback

            traceback.print_exc()
            return None

    def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None):
        """Send a notification to the language server."""
        if not self.process:
            return

        notification = {"jsonrpc": "2.0", "method": method, "params": params}
        try:
            notification_json = json.dumps(notification)
            content = f"Content-Length: {len(notification_json.encode('utf-8'))}\r\n\r\n{notification_json}"
            self.process.stdin.write(content.encode("utf-8"))
            self.process.stdin.flush()
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")

    def _read_response(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        try:
            # 使用缓存读取，避免逐字节读取的性能问题
            buffer = b""
            start_time = time.time()

            # 1. 读取数据直到找到完整的头部分隔符
            while b"\r\n\r\n" not in buffer:
                # 检查超时
                if time.time() - start_time > timeout:
                    print(f"⏰ Timeout waiting for message header")
                    return None

                # 一次读取更多数据，但要处理可能的阻塞
                try:
                    # 在Unix系统上使用select检查是否有数据可读
                    if sys.platform != "win32":
                        ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
                        if not ready:
                            print("⏳ No data available, waiting...")
                            continue
                    print("📖 Attempting to read 4096 bytes...")
                    chunk = self.process.stdout.read(4096)
                    print(f"📦 Received {len(chunk)} bytes: {chunk[:100]}...")
                    if not chunk:
                        print("⚠️ Connection closed while reading header")
                        return None
                    buffer += chunk
                except Exception as e:
                    print(f"❌ Error reading chunk: {e}")
                    return None

            # 2. 分离头部和可能的消息体数据
            header_end = buffer.find(b"\r\n\r\n")
            header_bytes = buffer[:header_end]
            remaining_bytes = buffer[header_end + 4 :]  # +4 for \r\n\r\n

            header_text = header_bytes.decode("utf-8")
            print(f"📥 Raw headers:\n{header_text}")

            # 3. 解析头部
            headers = {}
            for line in header_text.split("\r\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

            content_length = int(headers.get("content-length", "0"))
            if content_length == 0:
                print("⚠️ Content-Length is 0 or missing")
                return None

            print(f"📦 Expecting {content_length} bytes")

            # 4. 读取消息体
            content_bytes = remaining_bytes

            # 如果已有的数据不够，继续读取
            while len(content_bytes) < content_length:
                # 检查超时
                if time.time() - start_time > timeout:
                    print(f"⏰ Timeout waiting for message content")
                    return None

                needed = content_length - len(content_bytes)
                chunk = self.process.stdout.read(needed)
                if not chunk:
                    print("⚠️ Connection closed while reading content")
                    return None
                content_bytes += chunk

            # 5. 只取需要的字节数（可能有多余的）
            message_bytes = content_bytes[:content_length]

            print(
                f"📦 Raw content ({len(message_bytes)} bytes):\n{message_bytes.decode('utf-8')}\n---"
            )

            return json.loads(message_bytes.decode("utf-8"))

        except Exception as e:
            print(f"[LSP] Failed to read message: {e}")
            import traceback

            traceback.print_exc()
            return None
