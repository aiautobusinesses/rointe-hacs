#!/usr/bin/env python3
"""
Debug script to test Rointe authentication.
Run this to verify your credentials work.
"""

import asyncio
import aiohttp
import json

FIREBASE_API_KEY = "AIzaSyC0aaLXKB8Vatf2xSn1QaFH1kw7rADZlrY"
SIGNIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

async def test_authentication(email, password):
    """Test authentication with provided credentials."""
    print(f"🧪 Testing authentication for: {email}")
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(SIGNIN_URL, json=payload) as resp:
                print(f"📡 Response status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    print("✅ Authentication successful!")
                    print(f"📋 User ID: {data.get('localId', 'N/A')}")
                    print(f"📋 Refresh Token: {data.get('refreshToken', 'N/A')[:20]}...")
                    print(f"📋 Token expires in: {data.get('expiresIn', 'N/A')} seconds")
                    return True
                else:
                    error_data = await resp.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    print(f"❌ Authentication failed: {error_msg}")
                    
                    if "INVALID_EMAIL" in error_msg or "EMAIL_NOT_FOUND" in error_msg:
                        print("💡 Check your email address")
                    elif "INVALID_PASSWORD" in error_msg or "WRONG_PASSWORD" in error_msg:
                        print("💡 Check your password")
                    elif "USER_DISABLED" in error_msg:
                        print("💡 Your account has been disabled")
                    elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_msg:
                        print("💡 Too many failed attempts. Wait and try again later")
                    
                    return False
                    
    except aiohttp.ClientError as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def main():
    print("🔐 Rointe Authentication Debug Tool")
    print("=" * 40)
    
    email = input("Enter your Rointe email: ").strip()
    password = input("Enter your Rointe password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required")
        return
    
    success = await test_authentication(email, password)
    
    if success:
        print("\n✅ Your credentials are working!")
        print("The issue might be in the Home Assistant integration setup.")
        print("\nNext steps:")
        print("1. Restart Home Assistant")
        print("2. Try adding the integration again")
        print("3. Check HA logs for more details")
    else:
        print("\n❌ Authentication failed!")
        print("Please check your credentials and try again.")

if __name__ == "__main__":
    asyncio.run(main())
