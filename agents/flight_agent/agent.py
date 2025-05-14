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
    session_service.create_session(
        app_name="flight_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    prompt = (
        f"User wants to fly from {request['origin']} to {request['destination']} "
        f"between {request['start_date']} and {request['end_date']} with a budget of {request['budget']}. "
        "Suggest 2-3 flight options, each with airline name, flight number, departure and arrival times, price estimate, and duration. "
        "Respond in JSON format using the key 'flights' with a list of flight objects."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=message):
        if event.is_final_response():
            print(f"Inside flight_agent execute..............")
            response_text = event.content.parts[0].text
            print(f"flight_agent Response text: {response_text}...")
            cleaned = strip_triple_backticks(response_text)
            print(f"flight_agent Cleaned response: {cleaned}...")
            try:
                parsed = json.loads(cleaned)
                if "flights" in parsed and isinstance(parsed["flights"], list):
                    return {"flights": parsed["flights"]}
                else:
                    print("'flights' key missing or not a list in response JSON")
                    return {"flights": response_text}  # fallback to raw text
            except json.JSONDecodeError as e:
                print("JSON parsing failed:", e)