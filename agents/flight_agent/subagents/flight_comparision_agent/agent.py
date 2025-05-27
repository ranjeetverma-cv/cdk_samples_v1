from google.generativeai.agent import LlmAgent
from flight_agent.state_keys import (
    STATE_FLIGHT_OPTIONS,
    STATE_FLIGHT_COMPARISON_RESULT,
)

flight_comparison_agent = LlmAgent(
    name="flight_comparison_agent",
    model="gemini-pro",  # You can also use "chat-bison" or another model
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
