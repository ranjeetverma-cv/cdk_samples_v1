from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json
import re

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, skip loading .env
    pass

# from google.generativeai.agent import LlmAgent

from .state_keys import (
    STATE_FLIGHT_OPTIONS,
    STATE_FLIGHT_COMPARISON_RESULT,
    STATE_FLIGHT_ORIGIN,
    STATE_FLIGHT_DESTINATION,
    STATE_DEPARTURE_DATE,
    STATE_RETURN_DATE,
    STATE_PASSENGERS,
    STATE_FLIGHT_DEPARTURE_DATE,
    STATE_FLIGHT_RETURN_DATE,
    STATE_FLIGHT_PASSENGERS,
    STATE_PRICE_ANALYSIS_RESULT,
)

# --- ROOT_PROMPT for orchestration ---
ROOT_PROMPT = """
    You are a helpful and intelligent flight booking orchestration agent.
    Your primary role is to coordinate tasks by routing user input and context to the appropriate sub-agents. You will not generate responses yourself.

    Please follow these steps to accomplish the task successfully:
    1. Follow the <Gather Flight Details> section and collect all required information from the user.
    2. Move to the <Steps> section and strictly follow each step one by one.
    3. Follow all <Key Constraints> carefully when executing the flow.

    <Gather Flight Details>
    1. Greet the user and request the following mandatory details:
        - Origin (Departure city or airport)
        - Destination (Arrival city or airport)
        - Departure date
        - Return date (optional, only if it's a round trip)
        - Number of passengers
    2. If any required information is missing, continue to prompt the user until all necessary flight details are collected.
    3. Do not proceed to the next steps until all mandatory flight details are available.
    </Gather Flight Details>

    <Steps>
    1. Call `flight_search_agent` to get a list of available flight options based on the provided details. Store the flight options.
    2. Transfer control to the main agent.
    3. Call `price_analysis_agent` to evaluate price trends or recommend optimal dates (if flexible). Store the result.
    4. Transfer control to the main agent.
    5. Call `flight_comparison_agent` to compare flights based on duration, layovers, cost, and ratings. Relay the comparison report to the user.
    </Steps>

    <Key Constraints>
        - You must follow the <Steps> in strict order without skipping or reordering.
        - Always return control to the main agent after each sub-agent execution.
        - Do not provide any final answers or summaries yourself. Simply pass the results from sub-agents to the user.
        - Ensure that all flight options and recommendations are based on the inputs gathered in <Gather Flight Details>.
    </Key Constraints>
"""


def strip_triple_backticks(text):
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text

# --- Subagent definitions as referenced in the orchestration prompt ---
flight_search_agent = Agent(
    name="flight_search_agent",
    model=LiteLlm("openai/gpt-4o"),
    description="Searches and lists flight options based on user input.",
    instruction="""
        You are a flight search assistant.
        Your task is to search and return a list of available flight options based on the following session state values:
        - Origin: stored in the key '{STATE_FLIGHT_ORIGIN}'
        - Destination: stored in the key '{STATE_FLIGHT_DESTINATION}'
        - Departure Date: stored in the key '{STATE_DEPARTURE_DATE}'
        - Return Date (optional): stored in the key '{STATE_RETURN_DATE}'
        - Number of Passengers: stored in the key '{STATE_PASSENGERS}'

        Use this information to simulate a list of 3–5 available flight options.
        Each option must include:
        - Airline name
        - Departure time
        - Arrival time
        - Duration
        - Price (in USD)

        Return the result as a JSON object with the key `output`, containing all the following fields:
        - `{STATE_FLIGHT_ORIGIN}`
        - `{STATE_FLIGHT_DESTINATION}`
        - `{STATE_DEPARTURE_DATE}`
        - `{STATE_RETURN_DATE}`
        - `{STATE_PASSENGERS}`
        - `flight_options`

        Example:
        ```json
        {{
            "output": {{
                "{STATE_FLIGHT_ORIGIN}": "JFK",
                "{STATE_FLIGHT_DESTINATION}": "LAX",
                "{STATE_DEPARTURE_DATE}": "2025-06-01",
                "{STATE_RETURN_DATE}": "2025-06-10",
                "{STATE_PASSENGERS}": 1,
                "flight_options": [
                    {{
                        "airline": "Delta",
                        "departure": "2025-06-01T09:00",
                        "arrival": "2025-06-01T13:30",
                        "duration": "4h 30m",
                        "price": 350
                    }},
                    {{
                        "airline": "United",
                        "departure": "2025-06-01T10:15",
                        "arrival": "2025-06-01T14:45",
                        "duration": "4h 30m",
                        "price": 370
                    }}
                    // ... more flights
                ]
            }}
        }}
        ```

        Do not include any explanation or table. Only return the JSON.

        Do not include any explanation or table. Only return the JSON.
    """.format(
        STATE_FLIGHT_ORIGIN=STATE_FLIGHT_ORIGIN,
        STATE_FLIGHT_DESTINATION=STATE_FLIGHT_DESTINATION,
        STATE_DEPARTURE_DATE=STATE_DEPARTURE_DATE,
        STATE_RETURN_DATE=STATE_RETURN_DATE,
        STATE_PASSENGERS=STATE_PASSENGERS
    ),
    output_key=STATE_FLIGHT_OPTIONS
)




price_analysis_agent = Agent(
    name="price_analysis_agent",
    model=LiteLlm("openai/gpt-4o"),  # or your preferred model like "chat-bison"
    description="Analyzes flight prices and suggests better travel dates or tips for savings.",
    instruction=f"""
    You are a travel pricing expert. Analyze the price trends for the provided flight details.
    
    The user's travel details are stored in the session under:
      - Origin: `{STATE_FLIGHT_ORIGIN}`
      - Destination: `{STATE_FLIGHT_DESTINATION}`
      - Departure Date: `{STATE_DEPARTURE_DATE}`
      - Return Date (optional): `{STATE_RETURN_DATE}`
      - Number of Passengers: `{STATE_PASSENGERS}`
    The output of the flight search agent is stored in the session under the key `output`, specifically as `output.flight_options`.

    Instructions:
    - Use the provided information and the list of flight options from `output.flight_options` to identify potential cost-saving options (e.g., suggest flying a day earlier/later, alternative airports, or off-peak travel times).
    - If dates are inflexible, provide price trend information or any deal insights based on the available flight options.
    - Be concise and avoid repeating inputs.
    - Your output should only include the insights and recommendations (1–3 brief points max).

    Save your output to the session state key: `{STATE_PRICE_ANALYSIS_RESULT}`
    """,
    output_key=STATE_PRICE_ANALYSIS_RESULT,
)

flight_comparison_agent = Agent(
    name="flight_comparison_agent",
    model=LiteLlm("openai/gpt-4o"),  # You can also use "chat-bison" or another model
    description="Compares available flights based on duration, layovers, cost, and airline rating.",
    instruction=f"""
    You are a flight comparison assistant.

    The user's list of available flight options is stored in the session under `{STATE_FLIGHT_OPTIONS}`.
    Each flight option contains details like:
      - Airline
      - Departure and arrival times
      - Duration
      - Number of layovers
      - Cost
      - Airline rating (if available)

    Instructions:
    - Review the list of flight options.
    - Compare and contrast them on the basis of:
        - Total travel duration
        - Number of layovers
        - Cost
        - Airline rating
    - Highlight the top 2–3 flight options that best balance speed, price, and convenience.
    - Provide a brief summary of the best option(s) for the user.

    Output Format (example):
    - Best Option: Airline A, $500, 1 stop, 7 hrs
    - Runner Up: Airline B, $520, nonstop, 8 hrs
    - Consider Airline C if flexible on time – cheaper at $450 with 2 stops

    Save your comparison summary to: `{STATE_FLIGHT_COMPARISON_RESULT}`
    """,
    output_key=STATE_FLIGHT_COMPARISON_RESULT,
)


flight_agent = Agent(
    name="flight_agent",
    model=LiteLlm("openai/gpt-4o"),
    description="Flight orchestration agent.",
    instruction=ROOT_PROMPT,
    sub_agents=[flight_search_agent, price_analysis_agent, flight_comparison_agent]
)



from .agent_runner import AgentRunner

async def execute(request):
    # Extract A2A input
    session_service = InMemorySessionService()
    USER_ID = "user_flight"
    SESSION_ID = "session_flight"
    APP_NAME = "flight_app"
    input_data = request.get("input", {})


    user_id = request.get("user_id", USER_ID)
    session_id = request.get("session_id", SESSION_ID)

    session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )
    session = session_service.create_session(app_name=APP_NAME, 
                                    user_id=user_id, 
                                    session_id=session_id)
    # Set session state variables for flight search agent
    if input_data.get("origin"): session.state[STATE_FLIGHT_ORIGIN] = input_data["origin"]
    if input_data.get("destination"): session.state[STATE_FLIGHT_DESTINATION] = input_data["destination"]
    if input_data.get("departure_date"): session.state[STATE_DEPARTURE_DATE] = input_data["departure_date"]
    if input_data.get("return_date"): session.state[STATE_RETURN_DATE] = input_data["return_date"]
    if input_data.get("num_passengers"): session.state[STATE_PASSENGERS] = input_data["num_passengers"]
    print(f"Initial state: {session.state}")

    # prompt = (
    #     f"User wants to find flights to {input_data.get('destination')} from {input_data.get('origin')} between {input_data.get('start_date')} and {input_data.get('end_date')} within a budget of {input_data.get('budget')}. "
    #     f"Suggest 2-3 flight options, each with airline, departure time, arrival time, and price. Respond in JSON with key 'flights' as a list of flight objects."
    # )
    # Format user details as a string to append to the prompt
    user_details = []
    if input_data.get("origin"): user_details.append(f"Origin: {input_data['origin']}")
    if input_data.get("destination"): user_details.append(f"Destination: {input_data['destination']}")
    if input_data.get("departure_date"): user_details.append(f"Departure Date: {input_data['departure_date']}")
    if input_data.get("return_date"): user_details.append(f"Return Date: {input_data['return_date']}")
    if input_data.get("num_passengers"): user_details.append(f"Number of Passengers: {input_data['num_passengers']}")
    if input_data.get("budget"): user_details.append(f"Budget: {input_data['budget']}")
    details_str = "\n".join(user_details)
    prompt_with_details = ROOT_PROMPT + ("\n\n<User Details>\n" + details_str if details_str else "")
    message = types.Content(role="user", parts=[types.Part(text=prompt_with_details)])
    runner = AgentRunner(agent=flight_agent, session_service=session_service, app_name="flight_app")
    async for event in runner.run(user_id=user_id, session_id=session_id, message=message):
    # async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        print(f"I am inside flight_agent... ")
        if event.is_final_response():
            response_text = event.content.parts[0].text
            updated_session = session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
            if updated_session is not None:
                print(f"State after agent run: {updated_session.state}")
            else:
                print("Session not found after agent run!")

            cleaned = strip_triple_backticks(response_text)
            try:
                parsed = json.loads(cleaned)
                print(f"Full parsed response: {parsed}")  # Debug: show everything returned by the orchestration agent
                # If the orchestration agent returns an 'output' key, return all of it
                if "output" in parsed:
                    return {
                        "output": parsed["output"],
                        "status": "success"
                    }
                # Otherwise, return the whole parsed response
                return {
                    "output": parsed,
                    "status": "success"
                }
            except json.JSONDecodeError:
                return {
                    "output": {"raw": response_text},
                    "status": "error"
                }

if __name__ == "__main__":
    import asyncio
    # Example request for testing
    request = {
        "input": {
            "origin": "JFK",
            "destination": "LAX",
            "departure_date": "2025-06-01",
            "return_date": "2025-06-10",
            "num_passengers": 1,
            "budget": 1000
        },
        "user_id": "test_user",
        "session_id": "test_session"
    }
    result = asyncio.run(execute(request))
    print(result)