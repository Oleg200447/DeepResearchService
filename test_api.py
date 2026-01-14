"""Simple test script for the Deep Research Agent API."""
import json
import base64
import requests
from datetime import datetime, timedelta


def create_test_jwt() -> str:
    """Create a test JWT token (without signature validation).
    
    Returns:
        Test JWT token string
    """
    # JWT header
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    # JWT payload
    payload = {
        "sub": "test_user_123",
        "nickname": "test_user",
        "role": "user",
        "iss": "test_service",
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    }
    
    # Encode header and payload
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip("=")
    
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")
    
    # Create fake signature (doesn't matter since we don't validate)
    signature = "fake_signature_not_validated"
    
    return f"{header_b64}.{payload_b64}.{signature}"


def test_health_check(base_url: str = "http://localhost:8000"):
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("Testing Health Check Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_endpoint(base_url: str = "http://localhost:8000"):
    """Test the chat endpoint with a test JWT."""
    print("\n" + "="*60)
    print("Testing Chat Endpoint")
    print("="*60)
    
    # Create test JWT
    jwt_token = create_test_jwt()
    print(f"Test JWT created: {jwt_token[:50]}...")
    
    # Prepare request
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "Hello! This is a test message. Can you respond?"
    }
    
    print(f"\nSending request to {base_url}/api/v1/chat")
    print(f"Question: {data['question']}")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            headers=headers,
            json=data,
            timeout=60
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Chat endpoint test passed!")
            return True
        else:
            print("❌ Chat endpoint test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_missing_jwt(base_url: str = "http://localhost:8000"):
    """Test that missing JWT returns 401."""
    print("\n" + "="*60)
    print("Testing Missing JWT (Should Return 401)")
    print("="*60)
    
    data = {
        "question": "This should fail without JWT"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/chat",
            json=data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected request without JWT!")
            return True
        else:
            print("❌ Should have returned 401!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("DEEP RESEARCH AGENT API - TEST SUITE")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    print(f"\nTesting API at: {base_url}")
    print("\nMake sure the service is running before running tests!")
    print("Start service with: python -m scr.main")
    
    input("\nPress Enter to continue...")
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health_check(base_url)))
    results.append(("Missing JWT", test_missing_jwt(base_url)))
    results.append(("Chat Endpoint", test_chat_endpoint(base_url)))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
