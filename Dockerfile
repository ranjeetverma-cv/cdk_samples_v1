# Use an official Python image
FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose ports for Streamlit and all agents
EXPOSE 8501 8001 8002 8003 8004

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Start all agents and Streamlit in the same container
CMD bash -c "\
  uvicorn agents.host_agent.__main__:app --host 0.0.0.0 --port 8001 & \
  uvicorn agents.flight_agent.__main__:app --host 0.0.0.0 --port 8002 & \
  uvicorn agents.stay_agent.__main__:app --host 0.0.0.0 --port 8003 & \
  uvicorn agents.activities_agent.__main__:app --host 0.0.0.0 --port 8004 & \
  streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0\
"
