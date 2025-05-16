import httpx
async def call_agent(url, payload):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.ReadTimeout:
        print(f"Timeout when calling {url}")
        return {"error": f"Timeout when calling {url}"}
    except httpx.HTTPStatusError as e:
        print(f"HTTP error from {url}: {e}")
        return {"error": f"HTTP error from {url}: {e}"}
    except Exception as e:
        print(f"Unexpected error calling {url}: {e}")
        return {"error": f"Unexpected error calling {url}: {e}"}