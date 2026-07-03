import os
from google import genai
from google.genai import types

class DebateOrchestrator:
    def __init__(self):
        self.state = {}

    def process_turn(self, user_input: str, persona: str, difficulty: str, history: list = []):
        # We use the standard GenAI SDK to make it easy to run on FastAPI
        client = genai.Client()
        
        # =====================================================================
        # AGENT 1: The Socratic Coach (Opponent)
        # ---------------------------------------------------------------------
        # This agent acts as the primary conversational interface. It uses 
        # Gemini 2.5 Flash to rapidly generate a counter-argument based on 
        # the user's selected persona (e.g., Devil's Advocate, Philosopher).
        # =====================================================================
        formatted_history = ""
        for msg in history:
            if msg["sender"] == "user":
                formatted_history += f"\nUser: {msg['text']}"
            elif msg["sender"] == "opponent":
                formatted_history += f"\nOpponent: {msg['text']}"

        opponent_prompt = f"""You are the Opponent Agent in a debate. 
Your job is to provide strong, factual counter-arguments.
Debate style to adopt: {persona}

Previous Conversation History:
{formatted_history}

Current User argument: {user_input}"""
        
        opponent_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=opponent_prompt,
        ).text

        # =====================================================================
        # AGENT 2: The Referee Agent (Evaluator)
        # ---------------------------------------------------------------------
        # This secondary agent runs in parallel (or immediately after) to 
        # evaluate the user's argument for logical fallacies. We utilize 
        # Gemini 2.5 Flash's structured JSON output capabilities (response_mime_type)
        # to guarantee the output matches our UI components exactly.
        # =====================================================================
        strictness_prompt = ""
        if difficulty == "Hardcore":
            strictness_prompt = "Be extremely strict. Flag every single cognitive bias, minor logical leap, emotional appeal, or slightly unsupported claim."
        else:
            strictness_prompt = "Be casual. Only flag major, obvious logical fallacies (like blatant Ad Hominem or Strawman). Ignore minor rhetoric."

        referee_prompt = f"""You are the Referee Agent in a debate.
{strictness_prompt}
Evaluate the following argument for logical fallacies and factual inaccuracies.
Provide a score out of 10 for Argument Strength.
Output your evaluation as JSON matching this A2UI scorecard format:
{{
  "version": "v0.9",
  "components": [
    {{ "id": "score", "component": "ProgressBar", "value": 4, "max": 10, "label": "Argument Strength" }},
    {{ "id": "fallacy", "component": "WarningCard", "title": "Fallacy Name", "message": "Explanation of fallacy." }}
  ]
}}

User argument: {user_input}"""

        referee_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=referee_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        ).text

        # Parse JSON
        import json
        try:
            referee_data = json.loads(referee_response)
        except json.JSONDecodeError:
            referee_data = {"error": "Failed to parse referee scorecard."}

        # 3. Combine responses
        # The orchestrator merges the outputs from both the Socratic Coach and 
        # the Referee Agent into a single unified payload for the frontend.
        return {
            "opponent_response": opponent_response,
            "referee_scorecard": referee_data
        }

    def generate_report(self, history: list):
        client = genai.Client()
        formatted_history = ""
        for msg in history:
            if msg["sender"] == "user":
                formatted_history += f"\nUser: {msg['text']}"
            elif msg["sender"] == "opponent":
                formatted_history += f"\nOpponent: {msg['text']}"
        
        report_prompt = f"""You are an expert Debate Analyst. Analyze the following debate history between a User and an Opponent.
Provide a comprehensive Report Card for the User.
Your output must be JSON matching this format:
{{
  "logical_consistency_score": "85/100",
  "frequent_fallacies": ["Ad Hominem", "Strawman"],
  "summary": "Overall summary of the user's performance...",
  "improvement_tips": ["Tip 1", "Tip 2"]
}}

Debate History:
{formatted_history}"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=report_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        ).text
        
        import json
        try:
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            return json.loads(clean_response.strip())
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse report card: {str(e)}", "raw": response}

orchestrator = DebateOrchestrator()
