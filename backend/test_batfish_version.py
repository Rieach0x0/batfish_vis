#!/usr/bin/env python3
"""
Batfish version diagnostic script.

Tests multiple methods to retrieve Batfish version.
"""

import sys
import requests
from pybatfish.client.session import Session

BATFISH_HOST = "localhost"
BATFISH_PORT = 9996


def test_http_version():
    """Test HTTP version endpoint."""
    print("=" * 60)
    print("Test 1: HTTP GET /v2/version")
    print("=" * 60)

    try:
        url = f"http://{BATFISH_HOST}:{BATFISH_PORT}/v2/version"
        print(f"URL: {url}")

        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Version from HTTP: {data.get('version', 'NOT FOUND')}")
            return data.get('version')
        else:
            print(f"✗ HTTP request failed with status {response.status_code}")
            return None

    except Exception as e:
        print(f"✗ HTTP request error: {type(e).__name__}: {e}")
        return None


def test_session_get_info():
    """Test pybatfish Session.get_info()."""
    print("\n" + "=" * 60)
    print("Test 2: pybatfish Session.get_info()")
    print("=" * 60)

    try:
        print(f"Creating session to {BATFISH_HOST}:{BATFISH_PORT}")
        session = Session(host=BATFISH_HOST, port=BATFISH_PORT)
        print("✓ Session created")

        # Check if get_info exists
        if not hasattr(session, 'get_info'):
            print("✗ Session does not have 'get_info' method")
            print(f"Available methods: {[m for m in dir(session) if not m.startswith('_')]}")
            return None

        print("Calling session.get_info()...")
        info = session.get_info()
        print(f"get_info() returned: {info}")
        print(f"Type: {type(info)}")

        if isinstance(info, dict):
            # Try multiple keys
            version = None
            for key in ["Batfish version", "version", "batfish_version", "Version"]:
                if key in info:
                    version = info[key]
                    print(f"✓ Version from key '{key}': {version}")
                    return version

            print("✗ Version not found in any expected key")
            print(f"Available keys: {list(info.keys())}")
            return None
        else:
            print(f"✗ get_info() returned non-dict type: {type(info)}")
            return None

    except AttributeError as e:
        print(f"✗ AttributeError: {e}")
        return None
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_session_attributes():
    """Check available Session attributes and methods."""
    print("\n" + "=" * 60)
    print("Test 3: Session attributes inspection")
    print("=" * 60)

    try:
        session = Session(host=BATFISH_HOST, port=BATFISH_PORT)

        # Get all non-private attributes
        attrs = [attr for attr in dir(session) if not attr.startswith('_')]

        print("Available public attributes/methods:")
        for attr in sorted(attrs):
            attr_obj = getattr(session, attr)
            attr_type = "method" if callable(attr_obj) else "attribute"
            print(f"  - {attr} ({attr_type})")

        # Check for version-related attributes
        version_attrs = [attr for attr in attrs if 'version' in attr.lower() or 'info' in attr.lower()]
        if version_attrs:
            print(f"\nVersion-related attributes found: {version_attrs}")
        else:
            print("\nNo version-related attributes found")

    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")


def main():
    """Run all diagnostic tests."""
    print("Batfish Version Diagnostic Script")
    print("=" * 60)
    print(f"Target: {BATFISH_HOST}:{BATFISH_PORT}")
    print()

    # Test 1: HTTP endpoint
    http_version = test_http_version()

    # Test 2: Session.get_info()
    session_version = test_session_get_info()

    # Test 3: Inspect session
    test_session_attributes()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if http_version:
        print(f"✓ HTTP endpoint version: {http_version}")
    else:
        print("✗ HTTP endpoint: FAILED")

    if session_version:
        print(f"✓ Session.get_info() version: {session_version}")
    else:
        print("✗ Session.get_info(): FAILED")

    # Recommendation
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)

    if http_version:
        print("✓ Use HTTP endpoint method (most reliable)")
        print(f"  Version: {http_version}")
        return 0
    elif session_version:
        print("✓ Use Session.get_info() method")
        print(f"  Version: {session_version}")
        return 0
    else:
        print("✗ Could not retrieve version from any method")
        print("  Possible causes:")
        print("  1. Batfish container not fully started")
        print("  2. Network connectivity issues")
        print("  3. Incompatible pybatfish version")
        return 1


if __name__ == "__main__":
    sys.exit(main())
