"""Test GPT-5 with different parameter configurations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from app.core import config

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def test_params():
    """Test different parameter configurations."""

    print("Testing GPT-5 parameter configurations...")
    print()

    # Test 1: With max_tokens=250
    print("Test 1: max_tokens=250")
    try:
        llm = ChatOpenAI(model="gpt-5", temperature=0.8, max_tokens=250)
        response = llm.invoke("What is your favorite hobby? Answer in 2-3 sentences.")
        print(f"  Response: {response.content}")
        print(f"  Length: {len(response.content)} chars")
    except Exception as e:
        print(f"  Error: {e}")

    print()

    # Test 2: Without max_tokens
    print("Test 2: No max_tokens limit")
    try:
        llm = ChatOpenAI(model="gpt-5", temperature=0.8)
        response = llm.invoke("What is your favorite hobby? Answer in 2-3 sentences.")
        print(f"  Response: {response.content}")
        print(f"  Length: {len(response.content)} chars")
    except Exception as e:
        print(f"  Error: {e}")

    print()

    # Test 3: With full prompt template (like our actual use)
    print("Test 3: With ChatPromptTemplate (production-like)")
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are {nickname}, a human player in a game. Answer naturally in 2-5 sentences."),
            ("human", "Question: {question}\n\nYour response:")
        ])
        llm = ChatOpenAI(model="gpt-5", temperature=0.8, max_tokens=250)
        parser = StrOutputParser()

        chain = prompt | llm | parser

        response = chain.invoke({
            "nickname": "Silent Wolf",
            "question": "What is your favorite hobby?"
        })

        print(f"  Response: {response}")
        print(f"  Length: {len(response)} chars")
        print(f"  Type: {type(response)}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    test_params()
