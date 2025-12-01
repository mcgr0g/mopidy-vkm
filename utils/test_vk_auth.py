#!/usr/bin/env python3
"""Test script to diagnose vkpymusic authentication flow."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv


def test_basic_vk_auth():
    """Test basic vkpymusic authentication like in documentation."""
    print("=== Testing Basic VKPyMusic Authentication ===")

    # Load credentials from .env
    load_dotenv()
    login = os.getenv("VK_TEST_LOGIN")
    password = os.getenv("VK_TEST_PASSWORD")

    if not login or not password:
        print("❌ VK_TEST_LOGIN or VK_TEST_PASSWORD not found in .env")
        return False

    print(f"📱 Testing with login: {login[:3]}***")

    try:
        import vkpymusic

        # Create token receiver (like in docs)
        print("🔧 Creating TokenReceiver...")
        tokenReceiver = vkpymusic.TokenReceiver(login, password)

        # Try to authenticate
        print("🔐 Attempting authentication...")
        auth_result = tokenReceiver.auth()

        print(f"✅ Authentication result: {auth_result}")

        if auth_result:
            token = tokenReceiver.get_token()
            print(
                f"🎫 Token received: {token[:20]}..."
                if token
                else "❌ No token received"
            )

            # Try to save to config
            print("💾 Saving to config...")
            tokenReceiver.save_to_config("/tmp/test_vk_config.json")
            print("✅ Saved to /tmp/test_vk_config.json")

            # Try to load service
            print("🔄 Loading service...")
            service = vkpymusic.Service.parse_config("/tmp/test_vk_config.json")
            if service:
                print("✅ Service loaded successfully")
                if hasattr(service, "get_user_info"):
                    try:
                        user_info = service.get_user_info()
                        print(f"👤 User info: {user_info}")
                    except Exception as e:
                        print(f"⚠️  Failed to get user info: {e}")
                else:
                    print("⚠️  Service has no get_user_info method")
            else:
                print("❌ Failed to load service")

            return True
        else:
            print("❌ Authentication failed")
            return False

    except Exception as e:
        print(f"❌ Exception during auth: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_with_handlers():
    """Test vkpymusic with our custom handlers."""
    print("\n=== Testing VKPyMusic with Custom Handlers ===")

    load_dotenv()
    login = os.getenv("VK_TEST_LOGIN")
    password = os.getenv("VK_TEST_PASSWORD")

    if not login or not password:
        print("❌ VK_TEST_LOGIN or VK_TEST_PASSWORD not found in .env")
        return False

    try:
        import vkpymusic
        from mopidy_vkm.auth.handlers import get_global_auth_handlers

        # Get our handlers
        auth_handlers = get_global_auth_handlers()
        captcha_handler, two_factor_handler = get_handler_methods(auth_handlers)

        print("📋 Using custom handlers:")
        print(f"   Captcha handler: {captcha_handler}")
        print(f"   2FA handler: {two_factor_handler}")

        # Create token receiver with handlers
        print("🔧 Creating TokenReceiver with handlers...")
        tokenReceiver = vkpymusic.TokenReceiver(login, password)

        # Note: TokenReceiver doesn't have set_captcha_handler/set_two_factor_handler methods
        # These need to be passed directly to auth() method (see test_vk_correct_integration.py)
        print("⚠️  TokenReceiver doesn't support setting handlers as attributes")
        print("💡 Use test_vk_correct_integration.py for proper handler integration")

        # Try to authenticate without handlers (will fail but shows the limitation)
        print("🔐 Attempting authentication without proper handler integration...")
        auth_result = tokenReceiver.auth()

        print(f"✅ Authentication result: {auth_result}")

        # Check handler status
        status = auth_handlers.status
        print(f"📊 Handler status: {status}")

        if hasattr(auth_handlers, "captcha_img") and auth_handlers.captcha_img:
            print(f"🖼️  Captcha URL: {auth_handlers.captcha_img}")

        return auth_result or status.value in [
            "captcha_required",
            "two_factor_required",
        ]

    except Exception as e:
        print(f"❌ Exception with handlers: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def get_handler_methods(handlers):
    """Extract handler methods from AuthHandlers instance."""
    return handlers.captcha_handler, handlers.two_factor_handler


if __name__ == "__main__":
    print("🚀 Starting VK authentication diagnostics...\n")

    # Test 1: Basic flow
    basic_success = test_basic_vk_auth()

    # Test 2: With handlers
    handlers_success = test_with_handlers()

    print(f"\n📋 Results:")
    print(f"   Basic auth: {'✅' if basic_success else '❌'}")
    print(f"   With handlers: {'✅' if handlers_success else '❌'}")

    if not basic_success and not handlers_success:
        print("\n💡 Recommendations:")
        print("   1. Check if VK credentials are correct")
        print("   2. Try accessing VK Music in browser first")
        print("   3. Check if 2FA is enabled on the account")
        print("   4. Verify vkpymusic version compatibility")
    elif not handlers_success:
        print("\n💡 Handler integration issues detected")
        print("   Check TokenReceiver handler integration methods")
    else:
        print("\n🎉 Authentication successful!")
