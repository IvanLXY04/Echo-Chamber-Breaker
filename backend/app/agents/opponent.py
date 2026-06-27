from google.adk.agents import LlmAgent
from google.adk.models import Gemini

# The Opponent Agent is responsible for providing grounded counter-arguments
opponent_agent = LlmAgent(
    name="opponent_agent",
    model=Gemini(model="gemini-3-pro"),
    instruction="""
    You are the Opponent Agent in a debate. 
    Your job is to provide strong, factual counter-arguments to the user's input.
    Use the `adopt-persona` skill to adjust your debate style.
    Use the Wikipedia MCP tool to ground your claims in reality.
    """
)
