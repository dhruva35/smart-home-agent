"""
Quick diagnostic: tests whether the Gemini API key and model are working.
Run from the project root:
    python scripts/check_llm.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY", "")
model = os.getenv("CHAT_MODEL", "gemini-3.6-flash")

print(f"GOOGLE_API_KEY present: {bool(api_key)}")
print(f"GOOGLE_API_KEY starts with: {api_key[:10]}..." if api_key else "GOOGLE_API_KEY is EMPTY")
print(f"CHAT_MODEL: {model}")
print()

if not api_key:
    print("ERROR: GOOGLE_API_KEY is not set. Check your .env file.")
    sys.exit(1)

print("Attempting LLM call with tool calling (same as agent will use)...")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    from langchain_core.tools import tool

    @tool
    def say_hi(name: str) -> str:
        """Say hi to someone."""
        return f"Hi {name}!"

    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0,
    )
    # Test plain call
    result = llm.invoke([HumanMessage(content="Say the word HELLO and nothing else.")])
    content_str = result.content if isinstance(result.content, str) else str(result.content)
    print(f"SUCCESS - Plain call: {content_str}")

    # Test tool binding (what the agent uses)
    llm_with_tools = llm.bind_tools([say_hi])
    result2 = llm_with_tools.invoke([HumanMessage(content="Say hi to Alice using the say_hi tool.")])
    print(f"SUCCESS - Tool call response type: {type(result2).__name__}")
    print()
    print("Everything is working. You can now run the red-team suite.")

except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    sys.exit(1)
