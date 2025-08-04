#!/usr/bin/env python3
"""
Simple LSP availability test.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_basic_imports():
    """Test if basic LSP modules can be imported."""
    print("=== Testing Basic Imports ===")

    try:
        from core.lsp.protocol import Position, Range, Location

        print("✓ Protocol models imported successfully")
    except Exception as e:
        print(f"✗ Failed to import protocol models: {e}")
        return False

    try:
        from core.lsp.language import LanguageDetector

        print("✓ Language detector imported successfully")
    except Exception as e:
        print(f"✗ Failed to import language detector: {e}")
        return False

    try:
        from core.lsp.client import LSPClient

        print("✓ LSP client imported successfully")
    except Exception as e:
        print(f"✗ Failed to import LSP client: {e}")
        return False

    try:
        from core.lsp.methods import LSPMethods

        print("✓ LSP methods imported successfully")
    except Exception as e:
        print(f"✗ Failed to import LSP methods: {e}")
        return False

    return True


def test_language_detection():
    """Test language detection."""
    print("\n=== Testing Language Detection ===")

    try:
        from core.lsp.language import LanguageDetector

        detector = LanguageDetector()

        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.html", "html"),
            ("test.css", "css"),
            ("test.json", "json"),
        ]

        for filename, expected in test_cases:
            detected = detector.detect_language(filename)
            status = "✓" if detected == expected else "✗"
            print(f"{status} {filename} -> {detected} (expected: {expected})")

        return True
    except Exception as e:
        print(f"✗ Language detection failed: {e}")
        return False


def test_language_server_availability():
    """Test if common language servers are available."""
    print("\n=== Testing Language Server Availability ===")

    servers_to_test = [
        "pylsp",
        "pyright-langserver",
        "python-lsp-server",
        "typescript-language-server",
        "gopls",
        "rust-analyzer",
        "clangd",
    ]

    available_servers = []

    for server in servers_to_test:
        try:
            result = subprocess.run(
                [server, "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print(f"✓ {server}: Available")
                available_servers.append(server)
            else:
                print(f"✗ {server}: Not available")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"✗ {server}: Not found")

    print(f"\nTotal available servers: {len(available_servers)}")
    return len(available_servers) > 0


def test_lsp_client_creation():
    """Test LSP client creation."""
    print("\n=== Testing LSP Client Creation ===")

    try:
        from core.lsp.client import LSPClient

        client = LSPClient()
        print("✓ LSP client created successfully")

        # Test getting supported languages
        supported = client.get_supported_languages()
        print(f"✓ Supported languages: {supported}")

        # Clean up
        client.stop_all_servers()
        return True
    except Exception as e:
        print(f"✗ LSP client creation failed: {e}")
        return False


def test_lsp_methods():
    """Test LSP methods creation."""
    print("\n=== Testing LSP Methods ===")

    try:
        from core.lsp.methods import LSPMethods
        from core.lsp.transport import Transport

        # Create a mock transport for testing
        class MockTransport:
            def start(self):
                return True

            def stop(self):
                pass

            def send_request(self, method, params=None):
                return {"result": []}

            def send_notification(self, method, params=None):
                pass

        transport = MockTransport()
        methods = LSPMethods(transport)
        print("✓ LSP methods created successfully")

        # Test initialization
        success = methods.initialize("/test/path")
        print(f"✓ Initialization test: {success}")

        return True
    except Exception as e:
        print(f"✗ LSP methods test failed: {e}")
        return False


def test_tools_integration():
    """Test LSP tools integration."""
    print("\n=== Testing LSP Tools Integration ===")

    try:
        from tools.lsp_tools import get_lsp_tools, close_lsp_tools

        # Get LSP tools
        lsp_tools = get_lsp_tools()
        print("✓ LSP tools created successfully")

        # Test basic functionality
        completions = lsp_tools.get_completions("test.py", 1, 5)
        print(f"✓ Completions test: {len(completions)} items")

        # Clean up
        close_lsp_tools()
        return True
    except Exception as e:
        print(f"✗ LSP tools integration failed: {e}")
        return False


def main():
    """Run all tests."""
    print("LSP Availability Test")
    print("=" * 40)

    tests = [
        test_basic_imports,
        test_language_detection,
        test_language_server_availability,
        test_lsp_client_creation,
        test_lsp_methods,
        test_tools_integration,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! LSP is ready to use.")
    else:
        print("✗ Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    main()
