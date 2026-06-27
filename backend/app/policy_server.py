import os
from google.adk.models import Gemini
import jwt # Assuming PyJWT is used for out-of-band token validation

class PolicyServer:
    def __init__(self):
        self.blocked_tools = [] # Add globally blocked tools here

    def validate_identity(self, request_headers: dict) -> bool:
        """
        Validates the OAuth JWT token out-of-band to prevent Confused Deputy attacks.
        Do NOT trust the user_id passed by the LLM.
        """
        auth_header = request_headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False
            
        token = auth_header.split(" ")[1]
        try:
            # In a real app, you would verify the signature using the Identity Provider's public keys
            # decoded = jwt.decode(token, public_key, algorithms=["RS256"], audience="our_client_id")
            # For this prototype, we simulate a successful validation if a token is present
            return True 
        except Exception:
            return False

    def is_tool_allowed(self, tool_name: str, args: dict) -> bool:
        """
        Structural Gating: Check if the tool is allowed.
        """
        if tool_name in self.blocked_tools:
            return False
        return True

policy_server = PolicyServer()
