from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json

activities_agent = Agent(
    name="activities_agent",
    model=LiteLlm("openai/gpt-4o"),
    description="Suggests interesting activities for the user at a destination.",
    instruction=(
        "Given a destination, dates, and budget, suggest 2-3 engaging tourist or cultural activities. "
        "For each activity, provide a name, a short description, price estimate, and duration in hours. "
        "Respond in plain English. Keep it concise and well-formatted."
    )
)

session_service = InMemorySessionService()
runner = Runner(
    agent=activities_agent,
    app_name="activities_app",
    session_service=session_service
)
USER_ID = "user_activities"
SESSION_ID = "session_activities"

async def execute(request):
    # Extract A2A input
    input_data = request.get("input", {})
    user_id = request.get("user_id", USER_ID)
    session_id = request.get("session_id", SESSION_ID)
    session_service.create_session(
        app_name="activities_app",
        user_id=user_id,
        session_id=session_id
    )
    prompt = (
        f"{input_data.get("query")}."
        f"Suggest 2-3 activities, each with name, description, price estimate, and duration. "
        f"Respond in JSON format using the key 'activities' with a list of activity objects."
    )
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        print(f"I am inside activities_agent........")
        if event.is_final_response():
            response_text = event.content.parts[0].text
            try:
                parsed = json.loads(response_text)
                if "activities" in parsed and isinstance(parsed["activities"], list):
                    return {
                        "output": {"activities": parsed["activities"]},
                        "status": "success"
                    }
                else:
                    return {
                        "output": {"activities": response_text},
                        "status": "error"
                    }
            except json.JSONDecodeError:
                return {
                    "output": {"activities": response_text},
                    "status": "error"
                }