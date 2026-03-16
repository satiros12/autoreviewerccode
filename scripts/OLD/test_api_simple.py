#!/usr/bin/env python3
"""
Simple test to verify API connection works
"""

import os
import json
import requests

# Get API key from environment
API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    print("ERROR: OPENROUTER_API_KEY environment variable not set")
    print("Set it with: export OPENROUTER_API_KEY='your-key-here'")
    exit(1)

print(f"API Key: {API_KEY[:10]}... (truncated for security)")

# Headers for OpenRouter API
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://cexams.local",
    "X-Title": "CExams Test",
}

# Simple test prompt
test_prompt = "What is 2+2? Respond with only a number."

data = {
    "model": "deepseek/deepseek-chat",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": test_prompt},
    ],
    "temperature": 0.1,
    "max_tokens": 50,
}

print("\nTesting API connection to OpenRouter...")
print(f"Using model: {data['model']}")
print(f"Sending prompt: '{test_prompt}'")

try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30,
    )

    print(f"\nResponse status code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        ai_response = result["choices"][0]["message"]["content"]
        print(f"✓ API call successful!")
        print(f"AI Response: {ai_response}")

        # Check if we can parse a simple exam
        print("\nTesting exam file reading...")
        exam_files = [f for f in os.listdir("Exams") if f.endswith(".c")]
        if exam_files:
            test_file = os.path.join("Exams", exam_files[0])
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"✓ Read exam file: {exam_files[0]}")
            print(f"  Length: {len(content)} characters")
            print(f"  First 100 chars: {content[:100]}...")
        else:
            print("✗ No exam files found in Exams/")

    elif response.status_code == 401:
        print("✗ Authentication failed - check your API key")
        print(f"Response: {response.text}")
    elif response.status_code == 429:
        print("✗ Rate limited - try again later")
    else:
        print(f"✗ API error: {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"✗ Request failed: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback

    traceback.print_exc()
