#!/usr/bin/env python3
"""Enhanced test script to study vkpymusic integration."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv


def explore_vkpymusic_api():
    """Explore vkpymusic TokenReceiver API to understand handler integration."""
    print("=== Exploring VKPyMusic TokenReceiver API ===")

    try:
        import vkpymusic

        print("🔍 TokenReceiver methods:")
        token_receiver_methods = [
            method
            for method in dir(vkpymusic.TokenReceiver)
            if not method.startswith("_")
        ]
        for method in token_receiver_methods:
            print(f"   - {method}")

        print("\n🔍 Creating TokenReceiver instance...")
        token_receiver = vkpymusic.TokenReceiver("test", "test")

        print("🔍 Instance methods and attributes:")
        for attr in dir(token_receiver):
            if not attr.startswith("_"):
                try:
                    value = getattr(token_receiver, attr)
                    attr_type = type(value).__name__
                    print(f"   - {attr}: {attr_type}")
                except Exception as e:
                    print(f"   - {attr}: <error: {e}>")

        # Check constructor parameters
        print("\n🔍 TokenReceiver constructor signature:")
        import inspect

        sig = inspect.signature(vkpymusic.TokenReceiver.__init__)
        print(f"   {sig}")

        # Check auth method signature
        print("\n🔍 auth method signature:")
        sig = inspect.signature(token_receiver.auth)
        print(f"   {sig}")

        return True

    except Exception as e:
        print(f"❌ Error exploring API: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_handler_integration():
    """Test different approaches to handler integration."""
    print("\n=== Testing Handler Integration Approaches ===")

    load_dotenv()
    login = os.getenv("VK_TEST_LOGIN")
    password = os.getenv("VK_TEST_PASSWORD")

    if not login or not password:
        print("❌ Credentials not found")
        return False

    try:
        import vkpymusic
        from mopidy_vkm.auth.handlers import get_global_auth_handlers

        auth_handlers = get_global_auth_handlers()

        # Approach 1: Try to pass handlers to constructor
        print("\n🔄 Approach 1: Pass handlers to constructor")
        try:
            # Note: TokenReceiver constructor doesn't accept captcha_handler/two_factor_handler parameters
            # These should be passed to auth() method instead (see test_vk_correct_integration.py)
            token_receiver = vkpymusic.TokenReceiver(login, password)
            print("⚠️  Constructor doesn't accept handler parameters")
            print("💡 Handlers should be passed to auth() method")

            # Try auth
            print("🔐 Attempting authentication...")
            result = token_receiver.auth()
            print(f"📊 Result: {result}")

        except Exception as e:
            print(f"❌ Constructor approach failed: {type(e).__name__}: {e}")

        # Approach 2: Try to set handlers as attributes
        print("\n🔄 Approach 2: Set handlers as attributes")
        try:
            token_receiver = vkpymusic.TokenReceiver(login, password)
            # Note: TokenReceiver doesn't have captcha_handler/two_factor_handler attributes
            # These need to be passed to auth() method instead
            print("⚠️  TokenReceiver doesn't support handler attributes")
            print("💡 Use test_vk_correct_integration.py for proper approach")

            # Try auth
            print("🔐 Attempting authentication...")
            result = token_receiver.auth()
            print(f"📊 Result: {result}")

        except Exception as e:
            print(f"❌ Attribute approach failed: {type(e).__name__}: {e}")

        # Approach 3: Try method-based approach
        print("\n🔄 Approach 3: Check for handler methods")
        try:
            token_receiver = vkpymusic.TokenReceiver(login, password)

            # Look for potential handler methods
            handler_methods = []
            for method_name in dir(token_receiver):
                if (
                    "handler" in method_name.lower()
                    or "captcha" in method_name.lower()
                    or "two_factor" in method_name.lower()
                ):
                    handler_methods.append(method_name)

            print(f"🔍 Potential handler methods: {handler_methods}")

            # Try auth
            print("🔐 Attempting authentication...")
            result = token_receiver.auth()
            print(f"📊 Result: {result}")

        except Exception as e:
            print(f"❌ Method approach failed: {type(e).__name__}: {e}")

        return True

    except Exception as e:
        print(f"❌ Error in handler integration: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_manual_2fa():
    """Test manual 2FA flow simulation."""
    print("\n=== Testing Manual 2FA Flow ===")

    load_dotenv()
    login = os.getenv("VK_TEST_LOGIN")
    password = os.getenv("VK_TEST_PASSWORD")

    if not login or not password:
        print("❌ Credentials not found")
        return False

    try:
        import vkpymusic

        # Enable debug logging for vkpymusic
        import logging

        logging.getLogger("vkpymusic").setLevel(logging.DEBUG)

        print("🔐 Attempting authentication with debug logging...")
        token_receiver = vkpymusic.TokenReceiver(login, password)

        print("📊 Starting auth process...")
        result = token_receiver.auth()

        print(f"📊 Final result: {result}")

        if result:
            token = token_receiver.get_token()
            print(f"🎫 Token: {token[:50]}..." if token else "❌ No token")
        else:
            print("❌ Authentication failed - checking for additional requirements...")

            # Check if there are any pending challenges
            # Note: TokenReceiver doesn't have needs_captcha/needs_two_factor attributes
            # Challenge status is handled via callbacks in auth() method
            print("⚠️  TokenReceiver doesn't expose challenge status attributes")
            print("💡 Challenge status handled via callbacks passed to auth() method")

        return result

    except Exception as e:
        print(f"❌ Error in manual 2FA: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting enhanced VK integration diagnostics...\n")

    # Step 1: Explore API
    api_success = explore_vkpymusic_api()

    # Step 2: Test handler integration
    integration_success = test_handler_integration()

    # Step 3: Test manual 2FA
    manual_success = test_manual_2fa()

    print(f"\n📋 Results:")
    print(f"   API exploration: {'✅' if api_success else '❌'}")
    print(f"   Handler integration: {'✅' if integration_success else '❌'}")
    print(f"   Manual 2FA: {'✅' if manual_success else '❌'}")

    if not any([api_success, integration_success, manual_success]):
        print(
            "\n💡 All approaches failed - need to investigate vkpymusic source or documentation"
        )
    elif manual_success:
        print("\n🎉 Manual authentication works - focus on handler integration")
    else:
        print("\n🔧 Partial success - need to refine approach")
