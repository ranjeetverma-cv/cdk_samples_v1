from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json
import re

def strip_triple_backticks(text):
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text

stay_agent = Agent(
    name="stay_agent",
    model=LiteLlm("openai/gpt-4o"),
    description="Suggests accommodations for the user at a destination.",
    instruction=(
        "Given a destination, dates, and budget, suggest 2-3 suitable accommodation options. "
        "For each, provide a name, a short description, price estimate per night, and location. "
        "Respond in plain English. Keep it concise and well-formatted."
    )
)

session_service = InMemorySessionService()
runner = Runner(
    agent=stay_agent,
    app_name="stay_app",
    session_service=session_service
)
USER_ID = "user_stay"
SESSION_ID = "session_stay"

async def execute(request):
    # Extract A2A input
    input_data = request.get("input", {})
    user_id = request.get("user_id", USER_ID)
    session_id = request.get("session_id", SESSION_ID)
    session_service.create_session(
        app_name="stay_app",
        user_id=user_id,
        session_id=session_id
    )
    prompt = (
        f"{input_data.get("query")}."
        f"Suggest 2-3 options, each with name, description, price per night, and location. "
        f"Respond in JSON format using the key 'stays' with a list of stay objects."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        print(f"I am inside stay_agent........")
        if event.is_final_response():
            response_text = event.content.parts[0].text
            cleaned = strip_triple_backticks(response_text)
            try:
                parsed = json.loads(cleaned)
                if "stays" in parsed and isinstance(parsed["stays"], list):
                    return {
                        "output": {"stays": parsed["stays"]},
                        "status": "success"
                    }
                else:
                    return {
                        "output": {"stays": response_text},
                        "status": "error"
                    }
            except json.JSONDecodeError:
                return {
                    "output": {"stays": response_text},
                    "status": "error"
                }
