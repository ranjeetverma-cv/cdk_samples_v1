from google.generativeai.agent import LlmAgent
from flight_agent.state_keys import (
    STATE_FLIGHT_ORIGIN,
    STATE_FLIGHT_DESTINATION,
    STATE_FLIGHT_DEPARTURE_DATE,
    STATE_FLIGHT_RETURN_DATE,
    STATE_FLIGHT_PASSENGERS,
    STATE_PRICE_ANALYSIS_RESULT,
)

price_analysis_agent = LlmAgent(
    name="price_analysis_agent",
    model="gemini-pro",  # or your preferred model like "chat-bison"
    description="Analyzes flight prices and suggests better travel dates or tips for savings.",
    instruction=f"""
    You are a travel pricing expert. Analyze the price trends for the provided flight details.
    
    The user's travel details are stored in the session under:
      - Origin: `{STATE_FLIGHT_ORIGIN}`
      - Destination: `{STATE_FLIGHT_DESTINATION}`
      - Departure Date: `{STATE_FLIGHT_DEPARTURE_DATE}`
      - Return Date (optional): `{STATE_FLIGHT_RETURN_DATE}`
      - Number of Passengers: `{STATE_FLIGHT_PASSENGERS}`

    Instructions:
    - Use the provided information to identify potential cost-saving options (e.g., suggest flying a day earlier/later, alternative airports, or off-peak travel times).
    - If dates are inflexible, provide price trend information or any deal insights.
    - Be concise and avoid repeating inputs.
    - Your output should only include the insights and recommendations (1–3 brief points max).

    Save your output to the session state key: `{STATE_PRICE_ANALYSIS_RESULT}`
    """,
    output_key=STATE_PRICE_ANALYSIS_RESULT,
)
