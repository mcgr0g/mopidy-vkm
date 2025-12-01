#!/usr/bin/env python3
"""Correct VK integration test with proper handler callbacks."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv


def test_correct_handler_integration():
    """Test correct handler integration using auth method callbacks."""
    print("=== Testing Correct Handler Integration ===")

    load_dotenv()
    login = os.getenv("VK_TEST_LOGIN")
    password = os.getenv("VK_TEST_PASSWORD")

    if not login or not password:
        print("❌ Credentials not found")
        return False

    try:
        import vkpymusic

        print(f"📱 Testing with login: {login[:3]}***")

        # Create token receiver
        print("🔧 Creating TokenReceiver...")
        token_receiver = vkpymusic.TokenReceiver(login, password)

        # Define handler functions
        def on_captcha_handler(captcha_url):
            print(f"🖼️  Captcha required: {captcha_url}")
            # For testing, return empty string to fail
            return ""

        def on_2fa_handler():
            print("🔐 Two-factor authentication required")
            # For testing, return empty string to fail
            return ""

        def on_invalid_client_handler():
            print("❌ Invalid client error")
            return None

        def on_critical_error_handler(*args, **kwargs):
            print(f"🚨 Critical error: {args}, {kwargs}")
            return None

        print("🔐 Attempting authentication with proper callbacks...")
        result = token_receiver.auth(
            on_captcha=on_captcha_handler,
            on_2fa=on_2fa_handler,
            on_invalid_client=on_invalid_client_handler,
            on_critical_error=on_critical_error_handler,
        )

        print(f"📊 Authentication result: {result}")

        if result:
            token = token_receiver.get_token()
            print(f"🎫 Token received: {token[:50]}..." if token else "❌ No token")

            # Save and test service
            print("💾 Saving token...")
            token_receiver.save_to_config("/tmp/correct_test_config.json")

            service = vkpymusic.Service.parse_config("/tmp/correct_test_config.json")
            if service:
                print("✅ Service loaded successfully")
                return True
            else:
                print("❌ Failed to load service")
                return False
        else:
            print("❌ Authentication failed")
            return False

    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_with_our_handlers():
    """Test with our actual AuthHandlers."""
    print("\n=== Testing with Our AuthHandlers ===")

    load_dotenv()
    login = os.getenv("VK_TEST_LOGIN")
    password = os.getenv("VK_TEST_PASSWORD")

    if not login or not password:
        print("❌ Credentials not found")
        return False

    try:
        import vkpymusic
        from mopidy_vkm.auth.handlers import get_global_auth_handlers

        # Get our handlers
        auth_handlers = get_global_auth_handlers()

        print("🔧 Creating TokenReceiver...")
        token_receiver = vkpymusic.TokenReceiver(login, password)

        print("🔐 Attempting authentication with our handlers...")
        result = token_receiver.auth(
            on_captcha=auth_handlers.captcha_handler,
            on_2fa=auth_handlers.two_factor_handler,
        )

        print(f"📊 Authentication result: {result}")

        # Check handler status
        status = auth_handlers.status
        print(f"📊 Handler status: {status}")

        if hasattr(auth_handlers, "captcha_img") and auth_handlers.captcha_img:
            print(f"🖼️  Captcha URL: {auth_handlers.captcha_img}")

        return result or status.value in [
            "captcha_required",
            "two_factor_required",
            "processing",
        ]

    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_interactive_2fa():
    """Test interactive 2FA flow."""
    print("\n=== Testing Interactive 2FA Flow ===")

    load_dotenv()
    login = os.getenv("VK_TEST_LOGIN")
    password = os.getenv("VK_TEST_PASSWORD")

    if not login or not password:
        print("❌ Credentials not found")
        return False

    try:
        import vkpymusic

        print("🔧 Creating TokenReceiver...")
        token_receiver = vkpymusic.TokenReceiver(login, password)

        # Interactive handlers
        def on_captcha_handler(captcha_url):
            print(f"🖼️  Captcha required!")
            print(f"   URL: {captcha_url}")
            print("   Please open the URL and enter the captcha text:")
            captcha_text = input("   Captcha: ").strip()
            return captcha_text

        def on_2fa_handler():
            print("🔐 Two-factor authentication required!")
            print("   Please enter the 2FA code sent to your phone:")
            code = input("   2FA Code: ").strip()
            return code

        print("🔐 Attempting authentication with interactive handlers...")
        result = token_receiver.auth(
            on_captcha=on_captcha_handler, on_2fa=on_2fa_handler
        )

        print(f"📊 Authentication result: {result}")

        if result:
            token = token_receiver.get_token()
            print(f"🎫 Token received: {token[:50]}..." if token else "❌ No token")
            return True
        else:
            print("❌ Authentication failed")
            return False

    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting correct VK integration tests...\n")

    # Test 1: Correct handler integration
    basic_success = test_correct_handler_integration()

    # Test 2: With our handlers
    handlers_success = test_with_our_handlers()

    # Test 3: Interactive (optional)
    interactive_success = False
    if basic_success or handlers_success:
        print("\n" + "=" * 50)
        print("🎯 Testing interactive 2FA (this will prompt for input):")
        interactive_success = test_interactive_2fa()

    print(f"\n📋 Results:")
    print(f"   Correct integration: {'✅' if basic_success else '❌'}")
    print(f"   Our handlers: {'✅' if handlers_success else '❌'}")
    print(f"   Interactive: {'✅' if interactive_success else '❌'}")

    if handlers_success:
        print("\n🎉 Our handler integration works!")
        print("💡 The issue was that we weren't passing handlers to the auth() method")
    elif basic_success:
        print("\n🔧 Basic integration works - need to fix our handler methods")
    else:
        print("\n❌ All approaches failed - check credentials or VK status")
