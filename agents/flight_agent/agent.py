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

flight_agent = Agent(
    name="flight_agent",
    model=LiteLlm("openai/gpt-4o"),
    description="Finds suitable flights for the user.",
    instruction=(
        "Given a departure location, destination, dates, and budget, suggest 2-3 suitable flight options. "
        "For each flight, provide airline name, flight number, departure and arrival times, price estimate, and duration. "
        "Respond in plain English. Keep it concise and well-formatted."
    )
)

session_service = InMemorySessionService()
runner = Runner(
    agent=flight_agent,
    app_name="flight_app",
    session_service=session_service
)
USER_ID = "user_flight"
SESSION_ID = "session_flight"

async def execute(request):
    # Extract A2A input
    input_data = request.get("input", {})
    user_id = request.get("user_id", USER_ID)
    session_id = request.get("session_id", SESSION_ID)
    session_service.create_session(
        app_name="flight_app",
        user_id=user_id,
        session_id=session_id
    )
    prompt = (
        f"User wants to find flights to {input_data.get('destination')} from {input_data.get('origin')} between {input_data.get('start_date')} and {input_data.get('end_date')} within a budget of {input_data.get('budget')}. "
        f"Suggest 2-3 flight options, each with airline, departure time, arrival time, and price. Respond in JSON with key 'flights' as a list of flight objects."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        print(f"I am inside flight_agent... ")
        if event.is_final_response():
            response_text = event.content.parts[0].text
            cleaned = strip_triple_backticks(response_text)
            try:
                parsed = json.loads(cleaned)
                if "flights" in parsed and isinstance(parsed["flights"], list):
                    return {
                        "output": {"flights": parsed["flights"]},
                        "status": "success"
                    }
                else:
                    return {
                        "output": {"flights": response_text},
                        "status": "error"
                    }
            except json.JSONDecodeError:
                return {
                    "output": {"flights": response_text},
                    "status": "error"
                }