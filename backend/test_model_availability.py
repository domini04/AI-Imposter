"""Test script to verify GPT-5 model availability with OpenAI and LangChain.

This script tests:
1. What models are available from OpenAI API
2. If 'gpt-5' is a valid model name
3. If LangChain can use it
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from app.core import config

import os
from openai import OpenAI
from langchain_openai import ChatOpenAI

def test_openai_models():
    """Test what models are available directly from OpenAI API."""
    print("=" * 70)
    print("Test 1: OpenAI API - Available Models")
    print("=" * 70)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("✗ OPENAI_API_KEY not found")
        return False

    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()

        # Filter for GPT models
        gpt_models = [m for m in models.data if 'gpt' in m.id.lower()]

        print(f"\nFound {len(gpt_models)} GPT models:")
        print()

        # Look for GPT-5 specifically
        gpt5_models = [m for m in gpt_models if 'gpt-5' in m.id or 'gpt5' in m.id]
        gpt4_models = [m for m in gpt_models if 'gpt-4' in m.id or 'gpt4' in m.id]

        if gpt5_models:
            print("GPT-5 Models:")
            for model in gpt5_models:
                print(f"  - {model.id}")
        else:
            print("GPT-5 Models: None found")

        print()
        print("GPT-4 Models (latest):")
        for model in sorted(gpt4_models, key=lambda x: x.id)[-5:]:
            print(f"  - {model.id}")

        print()
        print("All GPT models (showing first 10):")
        for model in sorted(gpt_models, key=lambda x: x.id)[:10]:
            print(f"  - {model.id}")

        return True

    except Exception as e:
        print(f"✗ Error listing models: {e}")
        return False


def test_langchain_gpt5():
    """Test if LangChain can use 'gpt-5'."""
    print("\n\n")
    print("=" * 70)
    print("Test 2: LangChain with 'gpt-5'")
    print("=" * 70)

    try:
        llm = ChatOpenAI(model="gpt-5", temperature=0)
        print("✓ ChatOpenAI instance created with model='gpt-5'")

        # Try a simple invocation
        print("\nAttempting API call with 'gpt-5'...")
        response = llm.invoke("Say 'test successful'")

        print(f"✓ Response received: {response.content}")
        return True

    except Exception as e:
        print(f"✗ Error with 'gpt-5': {type(e).__name__}")
        print(f"  Message: {str(e)}")
        return False


def test_langchain_gpt4o():
    """Test if LangChain can use 'gpt-4o'."""
    print("\n\n")
    print("=" * 70)
    print("Test 3: LangChain with 'gpt-4o'")
    print("=" * 70)

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        print("✓ ChatOpenAI instance created with model='gpt-4o'")

        # Try a simple invocation
        print("\nAttempting API call with 'gpt-4o'...")
        response = llm.invoke("Say 'test successful'")

        print(f"✓ Response received: {response.content}")
        return True

    except Exception as e:
        print(f"✗ Error with 'gpt-4o': {type(e).__name__}")
        print(f"  Message: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("#" * 70)
    print("# GPT-5 MODEL AVAILABILITY TEST")
    print("#" * 70)
    print()

    results = []

    # Test 1: Check available models
    results.append(("OpenAI API Models", test_openai_models()))

    # Test 2: Try gpt-5 with LangChain
    results.append(("LangChain with gpt-5", test_langchain_gpt5()))

    # Test 3: Try gpt-4o with LangChain (fallback)
    results.append(("LangChain with gpt-4o", test_langchain_gpt4o()))

    # Summary
    print("\n\n")
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print()
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)

    if results[1][1]:  # gpt-5 works
        print("✓ Use model='gpt-5' - it's available and working!")
    elif results[2][1]:  # gpt-4o works
        print("⚠ GPT-5 not available. Use model='gpt-4o' instead.")
        print("  Update ai_service.py line 246 to use 'gpt-4o'")
    else:
        print("✗ Neither gpt-5 nor gpt-4o working. Check API key and credits.")


if __name__ == "__main__":
    main()
