import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Test 1: Check if env var is loaded
print("Test 1: Environment Variables")
print(f"GEMINI_API_KEY exists: {bool(os.getenv('GEMINI_API_KEY'))}")
print(f"GOOGLE_API_KEY exists: {bool(os.getenv('GOOGLE_API_KEY'))}")

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("ERROR: No API key found in environment!")
    exit(1)

print(f"API Key (first 10 chars): {api_key[:10]}...")
print(f"API Key length: {len(api_key)}")

# Test 2: Try to create client
print("\nTest 2: Creating Gemini Client")
try:
    client = genai.Client(api_key=api_key)
    print("✓ Client created successfully")
except Exception as e:
    print(f"✗ Client creation failed: {e}")
    exit(1)

# Test 3: Try a simple API call
print("\nTest 3: Making API Call")
try:
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Say 'Hello, API is working!' in one sentence."
    )
    print(f"✓ API Response: {response.text}")
except Exception as e:
    print(f"✗ API call failed: {e}")
    print(f"Error type: {type(e).__name__}")
    exit(1)

print("\n✓ All tests passed! Gemini API is working correctly.")
