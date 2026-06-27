from google.adk.agents import LlmAgent
from google.adk.models import Gemini

# The Referee Agent is responsible for detecting fallacies and rendering the A2UI scorecard
referee_agent = LlmAgent(
    name="referee_agent",
    model=Gemini(model="gemini-3-pro"),
    instruction="""
    You are the Referee Agent in a debate.
    Your job is to evaluate the user's argument for logical fallacies and factual inaccuracies.
    Use the `detect-fallacy` skill to strictly identify fallacies.
    Output your evaluation using the A2UI Scorecard components so the frontend can render it visually.
    """
)
