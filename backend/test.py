import os
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

try:
    print("API Key exists:", bool(os.environ.get("GEMINI_API_KEY")))
    
    agent = LlmAgent(
        name="test_agent",
        model=Gemini(model="gemini-3-pro"),
        instruction="Say hi."
    )
    result = agent.run(input="Hello")
    print("Result type:", type(result))
    print("Result:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
