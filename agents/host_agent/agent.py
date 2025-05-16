from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

host_agent = Agent(
    name="host_agent",
    model=LiteLlm("openai/gpt-4o"),
    description="Coordinates travel planning by calling flight, stay, and activity agents.",
    instruction="You are the host agent responsible for orchestrating trip planning tasks. "
                "You call external agents to gather flights, stays, and activities, then return a final result."
)
session_service = InMemorySessionService()
runner = Runner(
    agent=host_agent,
    app_name="host_app",
    session_service=session_service
)

import httpx
import asyncio
import requests

USER_ID = "user_host"
SESSION_ID = "session_host"

# Helper to discover agent endpoint from .well-known/agent.json
def load_agent_endpoint(agent_base_url):
    resp = requests.get(f"{agent_base_url}/.well-known/agent.json")
    agent_info = resp.json()
    run_info = agent_info["endpoints"]["run"]
    return agent_base_url + run_info["url"]

# Discover endpoints at startup
def discover_agents():
    agents = {}

    import os
    
    # Default to localhost for local development
    flight_host = os.environ.get("FLIGHT_AGENT_URL", "http://localhost:8001")
    stay_host = os.environ.get("STAY_AGENT_URL", "http://localhost:8002")
    activities_host = os.environ.get("ACTIVITIES_AGENT_URL", "http://localhost:8003")
    
    # In Docker, use service names instead of localhost
    if os.environ.get("IN_DOCKER", "") == "true":
        flight_host = "http://flight-agent:8001"
        stay_host = "http://stay-agent:8002"
        activities_host = "http://activities-agent:8003"

    for name, base_url in {
        "flights": flight_host,
        "stays": stay_host,
        "activities": activities_host
    }.items():
        try:
            agents[name] = load_agent_endpoint(base_url)
        except Exception as e:
            print(f"Failed to discover {name} agent: {e}")
    return agents

AGENT_ENDPOINTS = discover_agents()

from common.a2a_client import call_agent

async def execute(request):
    session_service.create_session(
        app_name="host_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    # Compose A2A-compliant payload
    a2a_payload = {
        "input": request,
        "user_id": USER_ID,
        "session_id": SESSION_ID
    }
    # Call sub-agents in parallel using discovered endpoints
    flights_task = call_agent(AGENT_ENDPOINTS["flights"], a2a_payload)
    stay_task = call_agent(AGENT_ENDPOINTS["stays"], a2a_payload)
    activities_task = call_agent(AGENT_ENDPOINTS["activities"], a2a_payload)
    flights, stay, activities = await asyncio.gather(flights_task, stay_task, activities_task)

    # Extract results according to A2A schema
    flights_result = flights.get("output", {}).get("flights", "No flights returned.")
    stay_result = stay.get("output", {}).get("stays", "No stay options returned.")
    activities_result = activities.get("output", {}).get("activities", "No activities found.")

    return {
        "flights": flights_result,
        "stay": stay_result,
        "activities": activities_result
    }